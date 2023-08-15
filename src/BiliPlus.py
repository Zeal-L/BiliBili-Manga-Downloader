from __future__ import annotations

from typing import TYPE_CHECKING

import requests
from bs4 import BeautifulSoup
from retrying import retry

from src.Comic import Comic
from src.Episode import Episode
from src.Utils import MAX_RETRY_SMALL, RETRY_WAIT_EX, TIMEOUT_SMALL, logger

if TYPE_CHECKING:
    from ui.MainGUI import MainGUI


class BiliPlusComic(Comic):
    """BiliPlus 单本漫画 综合信息类"""

    def __init__(self, comic_id: int, mainGUI: MainGUI) -> None:
        super().__init__(comic_id, mainGUI)
        self.access_key = mainGUI.getConfig("biliplus_cookie")
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
            "cookie": f"manga_pic_format=jpg-full;login=2;access_key={self.access_key}",
        }

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
        # ? 解析章节
        ep_list = self.data["ep_list"]
        for episode in reversed(ep_list):
            epi = BiliPlusEpisode(
                episode,
                self.sessdata,
                self.headers,
                self.comic_id,
                self.data,
                self.mainGUI,
            )
            self.episodes.append(epi)
            if epi.isDownloaded():
                self.num_downloaded += 1

        self.retrieveAvailableEpisode(self.episodes, self.comic_id, self.mainGUI)

        return self.episodes

    ############################################################
    def retrieveAvailableEpisode(
        self, episodes: list[BiliPlusEpisode], comic_id: str, mainGUI: MainGUI
    ):
        """从BiliPlus重新获取解锁状态"""
        biliplus_detail_url = (
            f"https://www.biliplus.com/manga/?act=detail_preview&mangaid={comic_id}"
        )
        biliplus_html = ""

        @retry(
            stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX
        )
        def _(url: str = biliplus_detail_url) -> dict:
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
                mainGUI.signal_message_box.emit("请先在设置界面填写正确的BiliPlus Cookie！")
                return
            if res.status_code != 200:
                logger.warning(
                    f"漫画id:{self.comic_id} 在BiliPlus爬取漫画信息失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中..."
                )
                raise requests.HTTPError()
            return res.text

        try:
            biliplus_html = _()
        except requests.RequestException as e:
            logger.error(f"漫画id:{self.comic_id} 在BiliPlus重复获取漫画信息多次后失败!\n{e}")
            logger.exception(e)

        # ?###########################################################
        # ? 解析BiliPlus解锁章节信息
        try:
            document = BeautifulSoup(biliplus_html, "html.parser")
            ep_items = document.find_all("div", {"class": "episode-item"})
            ep_available = []
            for ep in ep_items:
                if ep.img["src"] != "about:blank":
                    ep_available.append(ep.a["href"].split("epid=")[1])
            total_ep_element = document.select_one("center p")
            if total_ep_element:
                total_ep = total_ep_element.contents[0].split("/")[1]
                total_pages = int(int(total_ep) / 200) + 1
                for pages in range(2, total_pages + 1):
                    mainGUI.signal_resolve_status.emit(f"正在解析漫画章节({pages}/{total_pages})...")
                    page_html = _(f"{biliplus_detail_url}&page={pages}")
                    document = BeautifulSoup(page_html, "html.parser")
                    ep_items = document.find_all("div", {"class": "episode-item"})
                    for ep in ep_items:
                        if ep.img["src"] != "about:blank":
                            ep_available.append(ep.a["href"].split("epid=")[1])
            for ep in episodes:
                if str(ep.id) in ep_available:
                    ep.available = True
        except Exception as e:
            logger.error(f"漫画id:{self.comic_id} 在处理BiliPlus解锁章节数据时失败!\n{e}")
            logger.exception(e)
            mainGUI.signal_message_box.emit(
                f"漫画id:{self.comic_id} 在处理BiliPlus解锁章节数据时失败!\n\n更多详细信息请查看日志文件, 或联系开发者！"
            )


############################################################
class BiliPlusEpisode(Episode):
    """BiliPlus漫画章节类，用于管理漫画章节的详细信息"""

    def __init__(
        self,
        episode: dict,
        sessData: str,
        headers: str,
        comic_id: str,
        comic_info: dict,
        mainGUI: MainGUI,
    ) -> None:
        super().__init__(episode, sessData, comic_id, comic_info, mainGUI)
        self.headers = headers
        self.comic_id = comic_id

    ############################################################
    def init_imgsList(self, mainGUI: MainGUI) -> bool:
        """重写用于初始化从BiliPlus获取的章节内所有图片的列表(自带token)

        Returns
            bool: 是否初始化成功
        """
        # ?###########################################################
        # ? 获取图片列表
        biliplus_img_url = f"https://www.biliplus.com/manga/?act=read&mangaid={self.comic_id}&epid={self.id}"
        biliplus_html = ""

        @retry(
            stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX
        )
        def _() -> list[dict]:
            try:
                res = requests.post(
                    biliplus_img_url,
                    headers=self.headers,
                    timeout=TIMEOUT_SMALL,
                )
            except requests.RequestException as e:
                logger.warning(
                    f"《{self.comic_name}》章节：{self.title}，从BiliPlus获取图片列表失败! 重试中...\n{e}"
                )
                raise e
            if res.status_code != 200:
                logger.warning(
                    f"《{self.comic_name}》章节：{self.title} 从BiliPlus获取图片列表失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中..."
                )
                raise requests.HTTPError()
            return res.text

        try:
            biliplus_html = _()
        except requests.RequestException as e:
            logger.error(
                f"《{self.comic_name}》章节：{self.title} 从BiliPlus重复获取图片列表多次后失败!，跳过!\n{e}"
            )
            logger.exception(e)
            mainGUI.signal_message_box.emit(
                f"《{self.comic_name}》章节：{self.title} 从BiliPlus重复获取图片列表多次后失败!\n已暂时跳过此章节!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！"
            )
            return False

        # ?###########################################################
        # ? 解析BiliPlus解锁章节图片地址
        try:
            biliplus_imgs_token = []
            document = BeautifulSoup(biliplus_html, "html.parser")
            images = document.find_all("img", {"class": "comic-single"})
            for img in images:
                img_url = img["_src"]
                url, token = img_url.split("?token=")
                biliplus_imgs_token.append({"url": url, "token": token})
            self.imgs_token = biliplus_imgs_token
            if not biliplus_imgs_token:
                logger.error(
                    f"《{self.comic_name}》章节：{self.title} 在处理BiliPlus地址时因Cookie有误导致失败!"
                )
                mainGUI.signal_message_box.emit(
                    f"《{self.comic_name}》章节：{self.title} 在处理BiliPlus解锁章节图片地址时因Cookie有误导致失败!"
                )
                return False
        except Exception as e:
            logger.error(
                f"《{self.comic_name}》章节：{self.title} 在处理BiliPlus解锁章节图片地址时失败!\n{e}"
            )
            logger.exception(e)
            mainGUI.signal_message_box.emit(
                f"《{self.comic_name}》章节：{self.title} 在处理BiliPlus解锁章节图片地址时失败!\n\n更多详细信息请查看日志文件, 或联系开发者！"
            )
            return False

        return True
