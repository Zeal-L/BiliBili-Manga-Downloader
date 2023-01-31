from __future__ import annotations

import hashlib
import json
import os
import re
import typing

import requests
from PIL import Image
from PySide6.QtCore import SignalInstance
from PySide6.QtWidgets import QMessageBox
from retrying import RetryError, retry

from src.utils import (MAX_RETRY_LARGE, MAX_RETRY_SMALL, RETRY_WAIT_EX,
                       TIMEOUT_LARGE, TIMEOUT_SMALL, DownloadInfo, logger)

if typing.TYPE_CHECKING:
    from ui.MainGUI import MainGUI

class Episode:
    """漫画章节类，用于管理漫画章节的详细信息
    """
    def __init__(self, episode: dict, sessData: str, comic_id: str, comic_name: str, save_path: str) -> None:
        self.id = episode['id']
        self.available = not episode['is_locked']
        self.ord = episode['ord']
        self.comic_name = comic_name
        self.content_size = 0
        self.imgs_token = None

        #?###########################################################
        #? 修复标题中的特殊字符
        episode['short_title'] = re.sub(r'[\\/:*?"<>|]', ' ', episode['short_title'])
        episode['short_title'] = re.sub(r'\s+$', '', episode['short_title'])
        episode['title'] =  re.sub(r'[\\/:*?"<>|]', ' ', episode['title'])
        episode['title'] =  re.sub(r'\s+$', '', episode['title'])

        #?###########################################################
        #? 修复重复标题
        if episode['short_title'] == episode['title'] or episode['title'] == '':
            self.title = episode['short_title']
        else:
            self.title = f"{episode['short_title']} {episode['title']}"
        temp = re.search(r'^(\d+)\s+第(\d+)话', self.title)
        if temp and temp[1] == temp[2]:
            self.title = re.sub(r"^\d+\s+(第\d+话)", r"\1", self.title)
        if re.search(r'^特别篇\s+特别篇', self.title):
            self.title = re.sub(r'^特别篇\s+特别篇', r"特别篇", self.title)

        #?###########################################################
        #? 修复短标题中的数字
        if re.search(r'^[0-9\-]+话', self.title):
            self.title = re.sub(r'^([0-9\-]+)', r'第\1', self.title)
        elif re.search(r'^[0-9\-]+', self.title):
            self.title = re.sub(r'^([0-9\-]+)', r'第\1话', self.title)

        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'origin': 'https://manga.bilibili.com',
            'referer': f'https://manga.bilibili.com/detail/mc{comic_id}/{self.id}?from=manga_homepage',
            'cookie': f'SESSDATA={sessData}'
        }
        self.save_path = save_path
        self.pdf_path = os.path.join(self.save_path, f"{self.title}.pdf")

    ############################################################
    def init_imgsList(self, mainGUI: MainGUI) -> None:
        """初始化章节内所有图片的列表和图片的token，以及统计章节的大小
        """
        #?###########################################################
        #? 获取图片列表
        GetImageIndexURL = 'https://manga.bilibili.com/twirp/comic.v1.Comic/GetImageIndex?device=pc&platform=web'
        @retry(stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX)
        def _() -> list:
            try:
                res = requests.post(GetImageIndexURL, data={'ep_id': self.id}, headers=self.headers, timeout=TIMEOUT_SMALL)
            except requests.RequestException() as e:
                logger.warning(f"《{self.comic_name}》章节：{self.title}，获取图片列表失败! 重试中...\n{e}")
                raise e
            if res.status_code != 200:
                logger.warning(f'《{self.comic_name}》章节：{self.title} 获取图片列表失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中...')
                raise requests.HTTPError()
            return res.json()['data']['images']

        try:
            imgs_urls = [img['path'] for img in _()]
        except RetryError as e:
            logger.error(f'《{self.comic_name}》章节：{self.title} 重复获取图片列表多次后失败!，跳过!\n {e}')
            QMessageBox.warning(mainGUI, "警告",  f"《{self.comic_name}》章节：{self.title} 重复获取图片列表多次后失败!\n已暂时跳过此章节!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！")
            return

        #?###########################################################
        #? 获取图片token
        ImageTokenURL = "https://manga.bilibili.com/twirp/comic.v1.Comic/ImageToken?device=pc&platform=web"
        @retry(stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX)
        def _() -> list:
            try:
                res = requests.post(ImageTokenURL, data={"urls": json.dumps(imgs_urls)}, headers=self.headers, timeout=TIMEOUT_SMALL)
            except requests.RequestException() as e:
                logger.warning(f"《{self.comic_name}》章节：{self.title}，获取图片token失败! 重试中...\n{e}")
                raise e
            if res.status_code != 200:
                logger.warning(f'《{self.comic_name}》章节：{self.title} 获取图片token失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中...')
                raise requests.HTTPError()
            return res.json()['data']

        try:
            self.imgs_token = _()
        except RetryError as e:
            logger.error(f'《{self.comic_name}》章节：{self.title} 重复获取图片token多次后失败，跳过!\n{e}')
            QMessageBox.warning(mainGUI, "警告",  f"《{self.comic_name}》章节：{self.title} 重复获取图片token多次后失败!\n已暂时跳过此章节!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！")
            return

        #?###########################################################
        #? 统计章节内所有图片大小
        @retry(stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX)
        def _(index: int, url: str, token: str) -> None:
            img_url = f"{url}?token={token}"
            try:
                res = requests.head(img_url, timeout=TIMEOUT_SMALL)
            except requests.RequestException() as e:
                logger.warning(f"《{self.comic_name}》章节：{self.title} - {index} - {img_url} 获取图片 header 失败! 重试中...\n{e}")
                raise e
            if res.status_code != 200:
                logger.warning(f'《{self.comic_name}》章节：{self.title} - {index} - {img_url} 获取图片 header 失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中...')
                raise requests.HTTPError()
            self.content_size += int(res.headers['Content-Length'])

        for index, img in enumerate(self.imgs_token, start=1):
            try:
                _(index, img['url'], img['token'])
            except RetryError as e:
                logger.error(f"获取图片 header 多次后失败，跳过!\n{e}")
                QMessageBox.warning(mainGUI, "警告",  f"《{self.comic_name}》章节：{self.title} 获取图片 header 多次后失败!\n已暂时跳过此章节!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！")
                return

    ############################################################
    def download(self, mainGUI: MainGUI, rate_progress: SignalInstance, taskID: str, downloadInfo: DownloadInfo) -> None:
        """下载章节内所有图片 并合并为PDF

        Args:
            mainGUI (MainGUI): 主窗口类实例
            rate_progress (SignalInstance): 信号槽，用于更新下载进度条
            taskID (str): 任务ID
            downloadInfo (DownloadInfo): 下载任务的详细信息类实例
        """
        # TODO: 尝试把这一步放在漫画初始化的时候完成，使用多线程
        self.init_imgsList(mainGUI)

        downloadInfo.updateTask(taskID, 0, size=self.content_size)

        #?###########################################################
        #? 下载所有图片
        imgs_path = []
        for index, img in enumerate(self.imgs_token, start=1):
            img_url = f"{img['url']}?token={img['token']}"
            try:
                img_path = self.downloadImg(index, img_url)
            except RetryError as e:
                logger.error(f"《{self.comic_name}》章节：{self.title} - {index} - {img_url} 重复下载图片多次后失败!\n{e}")
                QMessageBox.warning(mainGUI, "警告", f"《{self.comic_name}》章节：{self.title} 重复下载图片多次后失败!\n已暂时跳过此章节!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！")
                return

            imgs_path.append(img_path)
            rate_progress.emit({
                "taskID": taskID,
                "rate": int((index / len(self.imgs_token)) * 100),
                "path": self.pdf_path
            })

        #?###########################################################
        #? 统一转换为RGB模式
        temp_imgs = [Image.open(x) for x in imgs_path]
        for i,img in enumerate(temp_imgs):
            if img.mode != 'RGB':
                temp_imgs[i] = img.convert('RGB')

        #?###########################################################
        #? 合并PDF
        try:
            temp_imgs[0].save(self.pdf_path, save_all=True, append_images=temp_imgs[1:], quality=95)
        except ValueError as e:
            logger.error(f'《{self.comic_name}》章节：{self.title} 合并PDF失败!\n{imgs_path}\n{e}')
            QMessageBox.warning(mainGUI, "警告", f"《{self.comic_name}》章节：{self.title} 合并PDF失败!\n请重新尝试或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！")

        #?###########################################################
        #? 删除临时图片, 偶尔会出现删除失败的情况，故给与重试5次
        @retry(stop_max_attempt_number=5)
        def _() -> None:
            for img in reversed(imgs_path):
                os.remove(img)
                if os.path.exists(img):
                    logger.warning(f'《{self.comic_name}》章节：{self.title} - {img} 删除临时图片失败! 重试中...')
                    raise OSError()
                else:
                    imgs_path.remove(img)
        try:
            _()
        except RetryError as e:
            logger.error(f'《{self.comic_name}》章节：{self.title} 删除临时图片失败!\n{imgs_path}\n{e}')
            QMessageBox.warning(mainGUI, "警告", f"《{self.comic_name}》章节：{self.title} 删除临时图片失败!\n请手动删除!\n\n更多详细信息请查看日志文件, 或联系开发者！")


    ############################################################
    @retry(stop_max_delay=MAX_RETRY_LARGE, wait_exponential_multiplier=RETRY_WAIT_EX)
    def downloadImg(self, index: int, img_url: str) -> str:
        """根据 url 和 token 下载图片

        Args:
            index (int): 章节中图片的序号
            img_url (str): 图片的合法 url

        Returns:
            str: 图片的保存路径
        """

        try:
            res = requests.get(img_url, timeout=TIMEOUT_LARGE)
        except requests.RequestException() as e:
            logger.warning(f"《{self.comic_name}》章节：{self.title} - {index} - {img_url} 下载图片失败! 重试中...\n{e}")
            raise e
        if res.status_code != 200:
            logger.warning(f"《{self.comic_name}》章节：{self.title} - {index} - {img_url} 获取图片 header 失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中...")
            raise requests.HTTPError()
        if res.headers['Etag'] != hashlib.md5(res.content).hexdigest():
            logger.warning(f"《{self.comic_name}》章节：{self.title} - {index} - {img_url} - 下载内容Checksum不正确! 重试中...\n\t{res.headers['Etag']} ≠ {hashlib.md5(res.content).hexdigest()}")
            raise requests.HTTPError()

        path_to_save = os.path.join(self.save_path, f"{self.ord}_{index}.jpg")
        with open(path_to_save, 'wb') as f:
            f.write(res.content)
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
        return os.path.exists(f'{self.save_path}/{self.title}.pdf')