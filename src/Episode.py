"""
该模块包含漫画章节类，用于管理漫画章节的详细信息
"""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
from typing import TYPE_CHECKING
from zipfile import ZipFile, ZIP_DEFLATED

import piexif
import requests
from PIL import Image
from py7zr import SevenZipFile
from pypdf import PdfReader, PdfWriter
from retrying import retry

from src.ComicInfoXML import ComicInfoXML
from src.Utils import (
    MAX_RETRY_LARGE,
    MAX_RETRY_SMALL,
    RETRY_WAIT_EX,
    TIMEOUT_LARGE,
    TIMEOUT_SMALL,
    __app_name__,
    __copyright__,
    __version__,
    isCheckSumValid,
    logger,
    myStrFilter,
)

if TYPE_CHECKING:
    from ui.MainGUI import MainGUI


class Episode:
    """漫画章节类，用于管理漫画章节的详细信息"""

    def __init__(
        self, episode: dict, comic_id: str, comic_info: dict, mainGUI: MainGUI, idx: int
    ) -> None:
        self.mainGUI = mainGUI
        self.id = episode["id"]
        self.available = not episode["is_locked"]
        self.ord = episode["ord"]
        self.real_ord = idx
        self.comic_name = comic_info["title"]
        self.size = episode["size"]
        self.imgs_token = None
        self.author = comic_info["author_name"]
        self.save_method = mainGUI.getConfig("save_method")
        self.exif_setting = mainGUI.getConfig("exif")

        # if self.ord != self.real_ord:
        #     logger.warning(
        #         f"章节序号错误！{self.comic_name} - {episode["title"]}; ord: {self.ord} ≠ real_ord: {self.real_ord}, 请责怪B站"
        #     )

        if self.save_method == "Cbz压缩包":
            self.comicinfoxml = ComicInfoXML(comic_info, episode)

        # ?###########################################################
        # ? 修复标题中的特殊字符
        episode["short_title"] = myStrFilter(episode["short_title"])
        episode["title"] = myStrFilter(episode["title"])

        # ?###########################################################
        # ? 修复重复标题
        if episode["short_title"] == episode["title"] or episode["title"] == "":
            self.title = episode["short_title"]
        else:
            self.title = f"{episode['short_title']} {episode['title']}"
        temp = re.search(r"^(\d+)\s+第(\d+)话", self.title)
        if temp and temp[1] == temp[2]:
            self.title = re.sub(r"^\d+\s+(第\d+话)", r"\1", self.title)
        temp = re.search(r"^(\d+)\s+第(\d+)$", self.title)
        if temp and temp[1] == temp[2]:
            self.title = re.sub(r"^\d+\s+(第\d+)$", r"\1话", self.title)
        if re.search(r"^特别篇\s+特别篇", self.title):
            self.title = re.sub(r"^特别篇\s+特别篇", r"特别篇", self.title)

        # ?###########################################################
        # ? 修复短标题中的数字
        if re.search(r"^[0-9\-\.]+话", self.title):
            self.title = re.sub(r"^([0-9\-\.]+)话", r"第\1话", self.title)
        elif re.search(r"^[0-9\-\.]+ ", self.title):
            self.title = re.sub(r"^([0-9\-\.]+) ", r"第\1话 ", self.title)
        elif re.search(r"^[0-9\-\.]+$", self.title):
            self.title = re.sub(r"^([0-9\-\.]+)$", r"第\1话", self.title)

        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "origin": "https://manga.bilibili.com",
            "referer": f"https://manga.bilibili.com/detail/mc{comic_id}/{self.id}?from=manga_homepage",
            "cookie": f"SESSDATA={mainGUI.getConfig('cookie')}",
        }
        self.save_path = comic_info["save_path"]
        self.epi_path = os.path.join(self.save_path, f"{self.title}")

    ############################################################
    def init_imgsList(self) -> bool:
        """初始化章节内所有图片的列表和图片的token

        Returns
            bool: 是否初始化成功
        """
        # ?###########################################################
        # ? 获取图片列表
        GetImageIndexURL = (
            "https://manga.bilibili.com/twirp/comic.v1.Comic/GetImageIndex?device=pc&platform=web"
        )

        @retry(stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX)
        def _() -> list[dict]:
            try:
                res = requests.post(
                    GetImageIndexURL,
                    data={"ep_id": self.id},
                    headers=self.headers,
                    timeout=TIMEOUT_SMALL,
                )
            except requests.RequestException as e:
                logger.warning(
                    f"《{self.comic_name}》章节：{self.title}, 获取图片列表失败! 重试中...\n{e}"
                )
                raise e
            if res.status_code != 200:
                logger.warning(
                    f"《{self.comic_name}》章节：{self.title} 获取图片列表失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中..."
                )
                raise requests.HTTPError()
            return res.json()["data"]["images"]

        try:
            imgs_urls = [img["path"] for img in _()]
        except requests.RequestException as e:
            logger.error(
                f"《{self.comic_name}》章节：{self.title} 重复获取图片列表多次后失败! 跳过!\n{e}"
            )
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                f"《{self.comic_name}》章节：{self.title} 重复获取图片列表多次后失败!\n"
                f"已暂时跳过此章节!\n"
                f"请检查网络连接或者重启软件!\n\n"
                f"更多详细信息请查看日志文件, 或联系开发者！"
            )
            return False

        # ?###########################################################
        # ? 获取图片token
        ImageTokenURL = (
            "https://manga.bilibili.com/twirp/comic.v1.Comic/ImageToken?device=pc&platform=web"
        )

        @retry(stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX)
        def _() -> list[dict]:
            try:
                res = requests.post(
                    ImageTokenURL,
                    data={"urls": json.dumps(imgs_urls)},
                    headers=self.headers,
                    timeout=TIMEOUT_SMALL,
                )
            except requests.RequestException as e:
                logger.warning(
                    f"《{self.comic_name}》章节：{self.title}, 获取图片token失败! 重试中...\n{e}"
                )
                raise e
            if res.status_code != 200:
                logger.warning(
                    f"《{self.comic_name}》章节：{self.title} 获取图片token失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中..."
                )
                raise requests.HTTPError()
            return res.json()["data"]

        try:
            self.imgs_token = _()
        except requests.RequestException as e:
            logger.error(
                f"《{self.comic_name}》章节：{self.title} 重复获取图片token多次后失败! 跳过!\n{e}"
            )
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                f"《{self.comic_name}》章节：{self.title} 重复获取图片token多次后失败!\n"
                f"已暂时跳过此章节!\n请检查网络连接或者重启软件!\n\n"
                f"更多详细信息请查看日志文件, 或联系开发者！"
            )
            return False

        return True

    ############################################################

    def clearAfterSave(self, imgs_path: list[str]) -> None:
        """删除临时图片, 偶尔会出现删除失败的情况，故给与重试3次

        Args:
            imgs_path (list): 临时图片路径列表
        """

        @retry(stop_max_attempt_number=3)
        def _() -> None:
            for img in reversed(imgs_path):
                try:
                    os.remove(img)
                    if os.path.exists(img):
                        raise OSError()
                except OSError as e:
                    logger.warning(
                        f"《{self.comic_name}》章节：{self.title} - {img} 删除临时图片失败! 重试中..."
                    )
                    raise e
                imgs_path.remove(img)

        try:
            _()
        except OSError as e:
            logger.error(
                f"《{self.comic_name}》章节：{self.title} 删除临时图片多次后失败!\n{imgs_path}\n{e}"
            )
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                f"《{self.comic_name}》章节：{self.title} 删除临时图片多次后失败!\n请手动删除!\n\n更多详细信息请查看日志文件, 或联系开发者！"
            )

    ############################################################

    def clear(self, imgs_path: list[str]) -> None:
        """删除临时图片, 终止时使用, 故无需多次尝试, 以最快的速度关闭, 且异常无需提示

        Args:
            imgs_path (list): 临时图片路径列表
        """
        for img in reversed(imgs_path):
            os.remove(img)
            imgs_path.remove(img)

    ############################################################

    def save(self, imgs_path: list[str]) -> str:
        """保存章节

        Args:
            imgs_path (list): 临时图片路径列表

        Returns:
            str: 保存路径
        """

        save_path = ""
        if self.save_method == "PDF":
            self.saveToPDF(imgs_path)
            save_path = f"{self.epi_path}.pdf"
        elif self.save_method == "文件夹-图片":
            self.saveToFolder(imgs_path)
            save_path = self.epi_path
        elif self.save_method == "7z压缩包":
            self.saveTo7z(imgs_path)
            save_path = f"{self.epi_path}.7z"
        elif self.save_method == "Zip压缩包":
            self.saveToZip(imgs_path)
            save_path = f"{self.epi_path}.zip"
        elif self.save_method == "Cbz压缩包":
            self.saveToCbz(imgs_path)
            save_path = f"{self.epi_path}.cbz"
        return save_path

    ############################################################
    def saveToPDF(self, imgs_path: list[str]) -> None:
        """将图片保存为PDF文件

        Args:
            imgs_path (list): 临时图片路径列表
        """

        @retry(stop_max_attempt_number=5)
        def _() -> None:
            try:
                # 因为pdf的兼容性, 统一转换为RGB模式
                temp_imgs = [Image.open(x) for x in imgs_path]
                for i, img in enumerate(temp_imgs):
                    if img.mode != "RGB":
                        temp_imgs[i] = img.convert("RGB")

                temp_imgs[0].save(
                    f"{self.epi_path}.pdf",
                    save_all=True,
                    append_images=temp_imgs[1:],
                    quality=95,
                )

                # 关闭所有图像, 释放内存
                for img in temp_imgs:
                    img.close()
                self.clearAfterSave(imgs_path)

                # 在pdf文件属性中记录章节标题作者和软件版本以及版权信息
                if not self.exif_setting:
                    return
                with open(f"{self.epi_path}.pdf", "rb") as f:
                    pdf = PdfReader(f)
                    pdf_writer = PdfWriter()
                    pdf_writer.append_pages_from_reader(pdf)
                    pdf_writer.add_metadata(
                        {
                            "/Title": f"《{self.comic_name}》 - {self.title}",
                            "/Author": self.author,
                            "/Creator": f"{__app_name__} {__version__} {__copyright__}",
                        }
                    )
                    with open(f"{self.epi_path}.pdf", "wb") as f:
                        pdf_writer.write(f)

            except OSError as e:
                logger.error(f"《{self.comic_name}》章节：{self.title} 合并PDF失败! 重试中...\n{e}")
                raise e

        try:
            _()
        except OSError as e:
            logger.error(f"《{self.comic_name}》章节：{self.title} 合并PDF多次后失败!\n{e}")
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                f"《{self.comic_name}》章节：{self.title} 合并PDF多次后失败!\n已暂时跳过此章节!\n请重新尝试或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！"
            )

    ############################################################
    def saveToFolder(self, imgs_path: list[str]) -> None:
        """将图片保存到文件夹

        Args:
            imgs_path (list): 临时图片路径列表
        """

        @retry(stop_max_attempt_number=5)
        def _() -> None:
            try:
                for index, img_path in enumerate(imgs_path, start=1):

                    def jpg_exif(img_path: str):
                        # 在jpg文件属性中记录章节标题作者和软件版本以及版权信息
                        exif_data = {
                            "0th": {
                                piexif.ImageIFD.ImageDescription: f"《{self.comic_name}》 - {self.title}".encode(
                                    "utf-8"
                                ),
                                piexif.ImageIFD.Artist: self.author.encode("utf-8"),
                                piexif.ImageIFD.Software: f"{__app_name__} {__version__}".encode(
                                    "utf-8"
                                ),
                                piexif.ImageIFD.Copyright: __copyright__,
                            }
                        }
                        exif_bytes = piexif.dump(exif_data)
                        piexif.insert(exif_bytes, img_path)

                    img_format = img_path.split(".")[-1]

                    # 将 exif 数据插入到图像文件中, 如果插入失败则跳过
                    if self.exif_setting:
                        try:
                            if img_format == "jpg":
                                jpg_exif(img_path)
                        except piexif.InvalidImageDataError as e:
                            logger.warning(f"Failed to insert exif data for {img_path}: {e}")
                            logger.exception(e)

                    # 复制图片到文件夹
                    shutil.move(
                        img_path,
                        os.path.join(self.epi_path, f"{str(index).zfill(3)}.{img_format}"),
                    )

            except OSError as e:
                logger.error(
                    f"《{self.comic_name}》章节：{self.title} 保存图片到文件夹失败! 重试中...\n{e}"
                )
                raise e

        try:
            if not os.path.exists(self.epi_path):
                os.makedirs(self.epi_path)
            _()
        except OSError as e:
            logger.error(
                f"《{self.comic_name}》章节：{self.title} 保存图片到文件夹多次后失败!\n{e}"
            )
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                f"《{self.comic_name}》章节：{self.title} 保存图片到文件夹多次后失败!\n已暂时跳过此章节!\n请重新尝试或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！"
            )

    ############################################################
    def saveTo7z(self, imgs_path: list[str]) -> None:
        """将图片保存到7z压缩文件

        Args:
            imgs_path (list): 临时图片路径列表
        """

        self.saveToFolder(imgs_path)

        @retry(stop_max_attempt_number=5)
        def _() -> None:
            try:
                with SevenZipFile(f"{self.epi_path}.7z", "w") as z:
                    # 压缩文件里不要子目录，全部存在根目录
                    for root, _dirs, files in os.walk(self.epi_path):
                        for file in files:
                            z.write(
                                os.path.join(root, file),
                                os.path.basename(os.path.join(root, file)),
                            )
                    shutil.rmtree(self.epi_path)
            except OSError as e:
                logger.error(
                    f"《{self.comic_name}》章节：{self.title} 保存图片到7z失败! 重试中...\n{e}"
                )
                raise e

        try:
            _()
        except OSError as e:
            logger.error(f"《{self.comic_name}》章节：{self.title} 保存图片到7z多次后失败!\n{e}")
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                f"《{self.comic_name}》章节：{self.title} 保存图片到7z多次后失败!\n已暂时跳过此章节!\n请重新尝试或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！"
            )

    ############################################################

    def saveToZip(self, imgs_path: list[str]) -> None:
        """将图片保存到Zip压缩文件

        Args:
            imgs_path (list): 临时图片路径列表
        """

        self.saveToFolder(imgs_path)

        @retry(stop_max_attempt_number=5)
        def _() -> None:
            try:
                with ZipFile(f"{self.epi_path}.zip", "w", compression=ZIP_DEFLATED) as z:
                    # 压缩文件里不要子目录，全部存在根目录
                    for root, _dirs, files in os.walk(self.epi_path):
                        for file in files:
                            z.write(
                                os.path.join(root, file),
                                os.path.basename(os.path.join(root, file)),
                            )
                    shutil.rmtree(self.epi_path)
            except OSError as e:
                logger.error(
                    f"《{self.comic_name}》章节：{self.title} 保存图片到Zip失败! 重试中...\n{e}"
                )
                raise e

        try:
            _()
        except OSError as e:
            logger.error(f"《{self.comic_name}》章节：{self.title} 保存图片到Zip多次后失败!\n{e}")
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                f"《{self.comic_name}》章节：{self.title} 保存图片到Zip多次后失败!\n已暂时跳过此章节!\n请重新尝试或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！"
            )

    ############################################################

    def saveToCbz(self, imgs_path: list[str]) -> None:
        """将图片保存到Cbz压缩文件

        Args:
            imgs_path (list): 临时图片路径列表
        """

        self.saveToFolder(imgs_path)
        self.comicinfoxml.serialize(self.epi_path)

        @retry(stop_max_attempt_number=5)
        def _() -> None:
            try:
                with ZipFile(f"{self.epi_path}.cbz", "w", compression=ZIP_DEFLATED) as z:
                    # 压缩文件里不要子目录，全部存在根目录
                    for root, _dirs, files in os.walk(self.epi_path):
                        for file in files:
                            z.write(
                                os.path.join(root, file),
                                os.path.basename(os.path.join(root, file)),
                            )
                    shutil.rmtree(self.epi_path)
            except OSError as e:
                logger.error(
                    f"《{self.comic_name}》章节：{self.title} 保存图片到Cbz失败! 重试中...\n{e}"
                )
                raise e

        try:
            _()
        except OSError as e:
            logger.error(f"《{self.comic_name}》章节：{self.title} 保存图片到Cbz多次后失败!\n{e}")
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                f"《{self.comic_name}》章节：{self.title} 保存图片到Cbz多次后失败!\n已暂时跳过此章节!\n请重新尝试或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！"
            )

    ############################################################

    def downloadImg(self, index: int, img_url: str) -> str:
        """根据 url 和 token 下载图片

        Args:
            index (int): 章节中图片的序号
            img_url (str): 图片的合法 url

        Returns:
            str: 图片的保存路径
        """

        # ?###########################################################
        # ? 下载图片
        @retry(stop_max_delay=MAX_RETRY_LARGE, wait_exponential_multiplier=RETRY_WAIT_EX)
        def _() -> bytes:
            try:
                if img_url.find("token") != -1:
                    res = requests.get(img_url, timeout=TIMEOUT_LARGE)
                else:
                    res = requests.get(img_url, headers=self.headers, timeout=TIMEOUT_LARGE)

            except requests.RequestException as e:
                logger.warning(
                    f"《{self.comic_name}》章节：{self.title} - {index} - {img_url} 下载图片失败! 重试中...\n{e}"
                )
                raise e
            if res.status_code != 200:
                logger.warning(
                    f"《{self.comic_name}》章节：{self.title} - {index} - {img_url} 获取图片 header 失败! "
                    f"状态码：{res.status_code}, 理由: {res.reason} 重试中..."
                )
                raise requests.HTTPError()
            isValid, md5 = isCheckSumValid(res.headers["Etag"], res.content)
            if not isValid:
                logger.warning(
                    f"《{self.comic_name}》章节：{self.title} - {index} - {img_url} - 下载内容Checksum不正确! 重试中...\n"
                    f"\t{res.headers['Etag']} ≠ {md5}"
                )
                raise requests.HTTPError()
            return res.content

        try:
            img = _()
        except requests.RequestException as e:
            logger.error(
                f"《{self.comic_name}》章节：{self.title} - {index} - {img_url} 重复下载图片多次后失败!\n{e}"
            )
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                f"《{self.comic_name}》章节：{self.title} 重复下载图片多次后失败!\n已暂时跳过此章节!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！"
            )
            return None

        # ?###########################################################
        # ? 保存图片
        img_format = img_url.split(".")[-1].split("?")[0].lower().replace("&append=", "")
        path_to_save = os.path.join(self.save_path, f"{self.real_ord}_{index}.{img_format}")

        @retry(stop_max_attempt_number=5)
        def _() -> None:
            try:
                with open(path_to_save, "wb") as f:
                    f.write(img)
            except OSError as e:
                logger.error(
                    f"《{self.comic_name}》章节：{self.title} - {index} - {img_url} - {path_to_save} - 保存图片失败! 重试中...\n{e}"
                )
                raise e

        try:
            _()
        except OSError as e:
            logger.error(
                f"《{self.comic_name}》章节：{self.title} - {index} - {img_url} - {path_to_save} - 保存图片多次后失败!\n{e}"
            )
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                f"《{self.comic_name}》章节：{self.title} - {index} - 保存图片多次后失败!\n"
                f"已暂时跳过此章节, 并删除所有缓存文件！\n"
                f"请重新尝试或者重启软件!\n\n"
                f"更多详细信息请查看日志文件, 或联系开发者！"
            )
            return None

        return path_to_save

    ############################################################
    def isAvailable(self) -> bool:
        """判断章节是否可用

        Returns:
            bool: True: 已解锁章节; False: 需付费章节
        """

        return self.available

    ############################################################
    def isDownloaded(self) -> bool:
        """判断章节是否已下载

        Returns:
            bool: True: 已下载; False: 未下载
        """
        file_name = re.sub(r"(\[|\])", r"[\1]", self.epi_path)
        file_list = glob.glob(f"{file_name}*")
        return len(file_list) > 0
