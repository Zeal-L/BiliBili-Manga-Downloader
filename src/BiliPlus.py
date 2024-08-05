"""
该模块包含了BiliPlusComic和BiliPlusEpisode类，用于获取BiliPlus网站上的单本漫画信息和章节信息
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import time
import requests
from bs4 import BeautifulSoup
from retrying import retry

from src.Comic import Comic
from src.Episode import Episode
from src.Utils import (
    MAX_RETRY_SMALL,
    RETRY_WAIT_EX,
    TIMEOUT_SMALL,
    __app_name__,
    __version__,
    logger,
    myStrFilter,
    sizeToBytes,
)

if TYPE_CHECKING:
    from ui.MainGUI import MainGUI


class BiliPlusComic(Comic):
    """BiliPlus 单本漫画 综合信息类"""

    def __init__(self, comic_id: int, mainGUI: MainGUI) -> None:
        super().__init__(comic_id, mainGUI)
        self.cookie = mainGUI.getConfig("biliplus_cookie")
        self.biliplus_detail_url = 'https://www.biliplus.com/manga/?act=detail&mangaid='
        self.headers = {
            "User-Agent": f"{__app_name__}/{__version__}",
            "cookie": f"{self.cookie};manga_sharing=on;manga_pic_format=jpg-full;",
        }

    ############################################################
    def getComicInfo(self) -> dict:
        """使用BiliPlus 页面爬取得到的漫画数据

        Returns:
            dict: 漫画信息
        """
        
        data = super().getComicInfo()
        if data:
             return data

        biliplus_detail_url = (
            f"https://www.biliplus.com/manga/?act=detail&mangaid={self.comic_id}"
        )
        biliplus_html = ""
        def _() -> dict:
            try:
                res = requests.post(
                    biliplus_detail_url,
                    headers=self.headers,
                    timeout=TIMEOUT_SMALL - 3,
                )
            except requests.RequestException as e:
                logger.warning(f"漫画id:{self.comic_id} 在BiliPlus爬取漫画信息失败! \n{e}")
                raise e
            if res.status_code != 200:
                logger.warning(
                    f"漫画id:{self.comic_id} 在BiliPlus爬取漫画信息失败! 状态码：{res.status_code}, 理由: {res.reason}"
                )
                raise requests.HTTPError()
            return res.text

        try:
            biliplus_html = _()
            if "漫画不存在" in biliplus_html:
                logger.error(f"漫画id:{self.comic_id} 无效, 该漫画在BiliPlus不存在!")
                return {}
            if "contents" not in biliplus_html:
                logger.error(f"漫画id:{self.comic_id} 获取异常, 请手动登入该漫画网页查看详情!")
                return {}
        except requests.RequestException as e:
            logger.error(f"漫画id:{self.comic_id} 在BiliPlus爬取漫画信息失败!\n{e}")
            logger.exception(e)
            return {}

        # ?###########################################################
        # ? 解析漫画信息
        try:
            soup = BeautifulSoup(biliplus_html, "html.parser")
            comic_title = soup.h3.text
            author_name = soup.h5.text.split()
            evaluate = soup.body.div.p.text
            styles = soup.body.div.div.text.split()
            horizontal_cover = soup.body.div.find_all("div")[1].div.find_all("a")[0]["href"]
            vertical_cover = soup.body.div.find_all("div")[1].div.find_all("a")[1]["href"]
            square_cover = soup.body.div.find_all("div")[1].div.find_all("a")[2]["href"]
            renewal_time = soup.body.div.find_all("p")[2].text
            episode_div_list = soup.body.div.find_all("div", {"class": "contents-full"})
            ep_list = []
            for idx, episode_div in enumerate(episode_div_list):
                ord = idx+1
                id = episode_div.find("div", {"class": "epid"}).text.split()[-1]
                temp = episode_div.find("div").find_all("div")[-1].text.split(" / ")
                if 2 == len(temp):
                    size, image_count = sizeToBytes(temp[0]), temp[1]
                else:
                    size, image_count = 0, temp[0]
                image_count = int(image_count.replace("页", ""))
                short_title, title = episode_div.find("a").text.split(". ")
                pub_time = episode_div.find_all(text=True)[-1].replace('发布', '').strip()
                ep_list.append({
                    "id": id,
                    "ord": ord,
                    "size": size,
                    "short_title": short_title,
                    "title": title,
                    "is_locked": True,
                    "image_count": image_count,
                    "pub_time": pub_time,
                })
        except Exception as e:
            msg = f"漫画id:{self.comic_id} 处理BiliPlus解析漫画信息时意外失败!"
            logger.error(msg)
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(f"{msg}\n\n更多详细信息请查看日志文件, 或联系开发者！")
        
        self.data = {}
        self.data["id"] = self.comic_id
        self.data["title"] = myStrFilter(comic_title)
        self.data["author_name"] = ",".join(author_name)
        self.data["author_name"] = (
            self.data["author_name"].replace("作者:", "").replace("出品:", "")
        )
        self.data["author_name"] = myStrFilter(self.data["author_name"])
        self.data["evaluate"] = evaluate
        self.data["styles"] = ",".join(styles)
        self.data["horizontal_cover"] = horizontal_cover
        self.data["square_cover"] = square_cover
        self.data["vertical_cover"] = vertical_cover
        self.data["renewal_time"] = renewal_time
        self.data["hall_icon_text"] = ""
        self.data["tags"] = []
        self.data["is_finish"] = True if renewal_time == "已完结" else False
        self.data["total"] = len(ep_list)
        self.data["ep_list"] = ep_list[::-1]
        if self.comic_id in self.mainGUI.my_library:
            self.data["save_path"] = self.mainGUI.my_library[self.comic_id].get("comic_path")
        else:
            self.data["save_path"] = f"{self.save_path}/{self.data['title']}"

        return self.data

    ############################################################
    def getEpisodesInfo(self) -> list[Episode]:
        """获取章节信息,但是得到的解锁章节和资源是BiliPlus的数据

        Returns:
            list: 章节信息列表
        """
        if self.episodes:
            return self.episodes
        if not self.data:
            return []

        # ?###########################################################
        # ? 解析 Biliplus 章节
        biliplus_ep_list = self.data["ep_list"]
        for idx, episode in enumerate(reversed(biliplus_ep_list), start=1):
            epi = BiliPlusEpisode(
                episode, self.headers, self.comic_id, self.data, self.mainGUI, idx
            )
            self.episodes.append(epi)
            if epi.isDownloaded():
                self.num_downloaded += 1

        self.retrieveAvailableEpisode(self.episodes, self.comic_id)

        return self.episodes

    ############################################################
    def retrieveAvailableEpisode(self, episodes: list[BiliPlusEpisode], comic_id: str) -> None:
        """从BiliPlus重新获取解锁状态"""
        biliplus_detail_url = (
            f"https://www.biliplus.com/manga/?act=detail_preview&mangaid={comic_id}"
        )
        biliplus_html = ""

        @retry(stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX)
        def _(url: str) -> str:
            try:
                res = requests.post(
                    url,
                    headers=self.headers,
                    timeout=TIMEOUT_SMALL,
                )
            except requests.RequestException as e:
                logger.warning(f"漫画id:{self.comic_id} 在BiliPlus获取漫画信息失败! 重试中...\n{e}")
                raise e
            if "未登录" in res.text:
                return "cookie invalid"
            if res.status_code != 200:
                logger.warning(
                    f"漫画id:{self.comic_id} 在BiliPlus爬取漫画信息失败! "
                    f"状态码：{res.status_code}, 理由: {res.reason} 重试中..."
                )
                raise requests.HTTPError()
            return res.text

        try:
            biliplus_html = _(biliplus_detail_url)
            if "" == biliplus_html:
                return None
            if "cookie invalid" == biliplus_html:
                self.mainGUI.signal_message_box.emit(
                    "您的BiliPlus Cookie无效, 请更新您的BiliPlus Cookie!"
                )
                return None
        except requests.RequestException as e:
            logger.error(f"漫画id:{self.comic_id} 在BiliPlus重复获取漫画信息多次后失败!\n{e}")
            logger.exception(e)
            return None

        # ?###########################################################
        # ? 解析BiliPlus解锁章节信息
        try:
            soup = BeautifulSoup(biliplus_html, "html.parser")
            ep_items = soup.find_all("div", {"class": "episode-item"})
            ep_available = []
            for ep in ep_items:
                if ep.img.get("_src") is not None:
                    ep_available.append(ep.a["href"].split("epid=")[1])
            total_ep_element = soup.select_one("center p")
            if total_ep_element:
                total_ep = total_ep_element.contents[0].split("/")[1]
                total_pages = int(int(total_ep) / 200) + 1
                for pages in range(2, total_pages + 1):
                    self.mainGUI.signal_resolve_status.emit(
                        f"正在解析漫画章节({pages}/{total_pages})..."
                    )
                    page_html = _(f"{biliplus_detail_url}&page={pages}")
                    soup = BeautifulSoup(page_html, "html.parser")
                    ep_items = soup.find_all("div", {"class": "episode-item"})
                    for ep in ep_items:
                        if ep.img.get("_src") is not None:
                            ep_available.append(ep.a["href"].split("epid=")[1])

            unlock_times = 0
            for ep in episodes:
                if str(ep.id) in ep_available:
                    if ep.available is False:
                        unlock_times += 1
                    ep.available = True

            if len(ep_available) == 0:
                msg = "BiliPlus无此漫画的缓存记录\n\n" \
                      "请在BiliPlus的该漫画详情页面使用功能“获取未缓存索引”后重试\n\n"
            elif unlock_times != 0:
                msg = f"BiliPlus为本漫画额外解锁{unlock_times}个章节\n\n"
            else:
                msg = "BiliPlus未能为此漫画解锁更多章节\n\n"
            self.mainGUI.signal_information_box.emit(
                f"{msg}Ciallo～(∠・ω< )⌒★\n"
                "您的主动分享能温暖每一个漫画人\n"
                "请在BiliPlus漫画主页进入功能“查看已购漫画”展示你的实力!"
            )
        except requests.RequestException as e:
            msg = f"漫画id:{self.comic_id} 处理BiliPlus解锁章节数据多次后失败!"
            logger.error(msg)
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                f"{msg}\n请检查网络连接或者重启软件!\n\n"
                f"更多详细信息请查看日志文件, 或联系开发者！"
            )
        except Exception as e:
            msg = f"漫画id:{self.comic_id} 处理BiliPlus解锁章节数据时意外失败!"
            logger.error(msg)
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(f"{msg}\n\n更多详细信息请查看日志文件, 或联系开发者！")


############################################################
class BiliPlusEpisode(Episode):
    """BiliPlus漫画章节类，用于管理漫画章节的详细信息"""

    def __init__(
        self,
        episode: dict,
        headers: str,
        comic_id: str,
        comic_info: dict,
        mainGUI: MainGUI,
        idx: int,
    ) -> None:
        super().__init__(episode, comic_id, comic_info, mainGUI, idx)
        self.headers = headers
        self.comic_id = comic_id

    ############################################################
    def init_imgsList(self) -> bool:
        """重写用于初始化从BiliPlus获取的章节内所有图片的列表(自带token)

        Returns
            bool: 是否初始化成功
        """
        # ?###########################################################
        # ? 获取图片列表
        biliplus_img_url = (
            f"https://www.biliplus.com/manga/?act=read&mangaid={self.comic_id}&epid={self.id}"
        )
        biliplus_img_url += f"&t={time.time()}"
        biliplus_html = ""

        @retry(stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX)
        def _() -> list[dict]:
            try:
                res = requests.post(
                    biliplus_img_url,
                    headers=self.headers,
                    timeout=TIMEOUT_SMALL,
                )
            except requests.RequestException as e:
                logger.warning(
                    f"《{self.comic_name}》章节：{self.title}"
                    f"从BiliPlus获取图片列表失败! 重试中...\n{e}"
                )
                raise e
            if res.status_code != 200:
                logger.warning(
                    f"《{self.comic_name}》章节：{self.title} 从BiliPlus获取图片列表失败! "
                    f"状态码：{res.status_code}, 理由: {res.reason} 重试中..."
                )
                raise requests.HTTPError()
            return res.text

        try:
            biliplus_html = _()
        except requests.RequestException as e:
            msg = f"《{self.comic_name}》章节：{self.title} 从BiliPlus重复获取图片列表多次后失败!"
            logger.error(msg)
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                f"{msg}\n已暂时跳过此章节!\n"
                f"请检查网络连接或者重启软件!\n\n"
                f"更多详细信息请查看日志文件, 或联系开发者！"
            )
            return False

        # ?###########################################################
        # ? 解析BiliPlus解锁章节图片地址
        try:
            biliplus_imgs_token = []
            if "获取凭据出错" in biliplus_html and 'src="http' not in biliplus_html:
                msg = f"《{self.comic_name}》章节：{self.title} " \
                       "在BiliPlus上的章节共享者已退出登陆, 下载失败！"
                logger.error(msg)
                self.mainGUI.signal_message_box.emit(msg)
                return False
            soup = BeautifulSoup(biliplus_html, "html.parser")
            images = soup.find_all("img", {"class": "comic-single"})
            for img in images:
                img_url = f'https://www.biliplus.com/manga/{img["_src"]}'
                biliplus_imgs_token.append({"url": img_url})
            self.imgs_token = biliplus_imgs_token
            if not biliplus_imgs_token:
                msg = f"《{self.comic_name}》章节：{self.title} " \
                       "在处理BiliPlus章节图片地址时因获取的Token无效导致失败!\n\n"
                logger.error(msg)
                self.mainGUI.signal_message_box.emit(
                    f"{msg}此问题不是下载器引发的, 请在BiliPlus本章节页面上查看失败原因!"
                )
                return False
        except Exception as e:
            msg = f"《{self.comic_name}》章节：{self.title} 在处理BiliPlus解锁章节图片地址时意外失败!"
            logger.error(msg)
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(f"{msg}\n\n更多详细信息请查看日志文件, 或联系开发者！")
            return False

        return True
