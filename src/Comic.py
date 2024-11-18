"""
该模块包含了单本漫画的综合信息类Comic，以及与Comic相关的函数
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import requests
from retrying import RetryError, retry

from PySide6.QtCore import QFile

from src.Episode import Episode
from src.Utils import (
    MAX_RETRY_SMALL,
    RETRY_WAIT_EX,
    TIMEOUT_SMALL,
    __user_agent__,
    isCheckSumValid,
    logger,
    myStrFilter,
)

if TYPE_CHECKING:
    from ui.MainGUI import MainGUI


class Comic:
    """单本漫画 综合信息类"""

    def __init__(self, comic_id: int, mainGUI: MainGUI, save_path: str = "") -> None:
        self.mainGUI = mainGUI
        self.comic_id = comic_id
        if save_path == "":
            self.save_path = mainGUI.getConfig("save_path")
        else:
            self.save_path = save_path
        self.num_thread = mainGUI.getConfig("num_thread")
        self.num_downloaded = 0
        self.episodes = []
        self.data = None
        self.detail_url = (
            "https://manga.bilibili.com/twirp/comic.v1.Comic/ComicDetail?device=pc&platform=web"
        )
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "origin": "https://manga.bilibili.com",
            "referer": f"https://manga.bilibili.com/detail/mc{comic_id}?from=manga_homepage",
            "cookie": f"SESSDATA={mainGUI.getConfig('cookie')}",
        }
        self.payload = {"comic_id": self.comic_id}

    ############################################################
    def getComicInfo(self) -> dict:
        """使用哔哩哔哩漫画 API 分析漫画数据

        Returns:
            dict: 漫画信息
        """

        @retry(
            stop_max_delay=MAX_RETRY_SMALL - 5000,
            wait_exponential_multiplier=RETRY_WAIT_EX,
        )
        def _() -> dict:
            try:
                res = requests.post(
                    self.detail_url,
                    headers=self.headers,
                    data=self.payload,
                    timeout=TIMEOUT_SMALL - 3,
                )
            except requests.RequestException as e:
                logger.warning(f"漫画id:{self.comic_id} 获取漫画信息失败! 重试中...\n{e}")
                raise e
            if res.status_code != 200 or res.json().get("code") != 0:
                if res.json().get("code") == 404:
                    return None
                reason = res.reason
                status_code = res.status_code
                if res.status_code != 200:
                    reason = res.json().get("msg")
                    status_code = res.json().get("code")
                logger.warning(
                    f"漫画id:{self.comic_id} 爬取漫画信息失败! 状态码：{status_code}, 理由: {reason} 重试中..."
                )
                raise requests.HTTPError()
            return res.json().get("data")

        try:
            self.data = _()
            if not self.data:
                logger.error(f"漫画id:{self.comic_id} 无效, 该漫画不存在!")
                return {}
        except requests.RequestException as e:
            logger.error(f"漫画id:{self.comic_id} 重复获取漫画信息多次后失败!\n{e}")
            logger.exception(e)
            return {}

        # ?###########################################################
        # ? 解析漫画信息
        self.data["title"] = myStrFilter(self.data["title"])
        self.data["author_name"] = ",".join(self.data["author_name"])
        self.data["author_name"] = (
            self.data["author_name"].replace("作者:", "").replace("出品:", "")
        )
        self.data["author_name"] = myStrFilter(self.data["author_name"])
        self.data["styles"] = ",".join(self.data["styles"])
        if self.comic_id in self.mainGUI.my_library:
            self.data["save_path"] = self.mainGUI.my_library[self.comic_id].get("comic_path")
        else:
            self.data["save_path"] = f"{self.save_path}/{self.data['title']}"

        return self.data

    ############################################################
    def getComicCover(self, data: dict) -> bytes:
        """获取漫画封面图片

        Returns:
            bytes: 漫画封面图片
        """

        @retry(stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX)
        def _() -> bytes:
            try:
                res = requests.get(data["vertical_cover"], timeout=TIMEOUT_SMALL)
            except requests.RequestException() as e:
                logger.warning(f"获取封面图片失败! 重试中...\n{e}")
                raise e
            if res.status_code != 200:
                logger.warning(
                    f"获取封面图片失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中..."
                )
                raise requests.HTTPError()
            isValid, md5 = isCheckSumValid(res.headers["Etag"], res.content)
            if not isValid:
                logger.warning(
                    f"图片内容 Checksum 不正确! 重试中...\n\t{res.headers['Etag']} ≠ {md5}"
                )
                raise requests.HTTPError()
            return res.content

        logger.info(f"获取《{data['title']}》的封面图片中...")
        try:
            img = _()
            return img
        except RetryError as e:
            logger.error(f"获取封面图片多次后失败, 跳过!\n{e}")
            self.mainGUI.signal_warning_box.emit(
                "获取封面图片多次后失败!\n"
                "请检查网络连接或者重启软件!\n\n"
                "更多详细信息请查看日志文件, 或联系开发者！"
            )
            fail_img = QFile(":/imgs/fail_img.jpg")
            fail_img.open(QFile.ReadOnly)
            return bytes(fail_img.readAll())


    ############################################################
    def getEpisodesInfo(self) -> list[Episode]:
        """获取章节信息

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
        for idx, episode in enumerate(reversed(ep_list), start=1):
            epi = Episode(episode, self.comic_id, self.data, self.mainGUI, idx)
            self.episodes.append(epi)
            if epi.isDownloaded():
                self.num_downloaded += 1
        return self.episodes

    ############################################################
    def getNumDownloaded(self) -> int:
        """获取已下载章节数

        Returns:
            int: 已下载章节数
        """
        return self.num_downloaded

def getMyFavoriteComic(mainGUI: MainGUI) -> list[dict]:
    """获取我的追漫列表

    Args:
        mainGUI (MainGUI): 主页面

    Returns:
        list[dict]: 我的追漫漫画详情列表
    """    
    favorite_list_url = "https://manga.bilibili.com/twirp/bookshelf.v1.Bookshelf/ListFavorite?device=pc&platform=web"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "origin": "https://manga.bilibili.com",
        "referer": f"https://manga.bilibili.com/account-center/my-favourite",
        "cookie": f"SESSDATA={mainGUI.getConfig('cookie')}",
    }
    payload = {"page_num":1,"page_size":99,"order":1,"wait_free":0}

    @retry(
        stop_max_delay=MAX_RETRY_SMALL - 5000,
        wait_exponential_multiplier=RETRY_WAIT_EX,
    )
    def _() -> dict:
        try:
            res = requests.post(
                favorite_list_url,
                headers=headers,
                data=payload,
                timeout=TIMEOUT_SMALL - 3,
            )
        except requests.RequestException as e:
            logger.warning(f"获取我的追漫失败! 重试中...\n{e}")
            raise e
        if res.status_code != 200 or res.json().get("code") != 0:
            if res.json().get("code") == 404:
                return None
            reason = res.reason
            status_code = res.status_code
            if res.status_code != 200:
                reason = res.json().get("msg")
                status_code = res.json().get("code")
                
            logger.warning(
                f"获取我的追漫失败! 状态码：{status_code}, 理由: {reason} 重试中..."
            )
            raise requests.HTTPError()
        return res.json().get("data")

    try:
        data = _()
        return data
    except requests.RequestException as e:
        logger.error(f"获取我的追漫多次后失败!\n{e}")
        logger.exception(e)
        return []

def addComicToFavorite(mainGUI: MainGUI, comic_id: int) -> bool:
    """添加漫画到我的追漫列表

    Args:
        mainGUI (MainGUI): 主页面
        comic_id (int): 漫画ID

    Returns:
        bool: 是否请求成功
    """    
    add_favorite_url = "https://manga.bilibili.com/twirp/bookshelf.v1.Bookshelf/AddFavorite?device=pc&platform=web"
    headers = {
        "user-agent": __user_agent__,
        "origin": "https://manga.bilibili.com",
        "referer": f"https://manga.bilibili.com/detail/mc{comic_id}",
        "cookie": f"SESSDATA={mainGUI.getConfig('cookie')}",
    }
    payload = {"comic_ids": str(comic_id)}

    @retry(
        stop_max_delay=MAX_RETRY_SMALL - 5000,
        wait_exponential_multiplier=RETRY_WAIT_EX,
    )
    def _() -> None:
        try:
            res = requests.post(
                add_favorite_url,
                headers=headers,
                data=payload,
                timeout=TIMEOUT_SMALL - 3,
            )
        except requests.RequestException as e:
            logger.warning(f"添加到我的追漫列表失败! 重试中...\n{e}")
            raise e
        if res.status_code != 200 or res.json().get("code") != 0:
            reason = res.reason
            status_code = res.status_code
            if res.status_code != 200:
                reason = res.json().get("msg")
                status_code = res.json().get("code")

            logger.warning(
                f"添加到我的追漫列表失败! 状态码：{status_code}, 理由: {reason} 重试中..."
            )
            raise requests.HTTPError()

    try:
        _()
        return True
    except requests.RequestException as e:
        logger.error(f"添加到我的追漫列表多次后失败!\n{e}")
        logger.exception(e)
        return False

def delComicFromFavorite(mainGUI: MainGUI, comic_id: int) -> bool:
    """从我的追漫列表移除

    Args:
        mainGUI (MainGUI): 主页面
        comic_id (int): 漫画ID

    Returns:
        bool: 是否请求成功
    """    
    del_favorite_url = "https://manga.bilibili.com/twirp/bookshelf.v1.Bookshelf/DeleteFavorite?device=pc&platform=web"
    headers = {
        "user-agent": __user_agent__,
        "origin": "https://manga.bilibili.com",
        "referer": f"https://manga.bilibili.com/detail/mc{comic_id}",
        "cookie": f"SESSDATA={mainGUI.getConfig('cookie')}",
    }
    payload = {"comic_ids": str(comic_id)}

    @retry(
        stop_max_delay=MAX_RETRY_SMALL - 5000,
        wait_exponential_multiplier=RETRY_WAIT_EX,
    )
    def _() -> None:
        try:
            res = requests.post(
                del_favorite_url,
                headers=headers,
                data=payload,
                timeout=TIMEOUT_SMALL - 3,
            )
        except requests.RequestException as e:
            logger.warning(f"从我的追漫列表中移除失败! 重试中...\n{e}")
            raise e
        if res.status_code != 200 or res.json().get("code") != 0:
            reason = res.reason
            status_code = res.status_code
            if res.status_code != 200:
                reason = res.json().get("msg")
                status_code = res.json().get("code")

            logger.warning(
                f"从我的追漫列表中移除失败! 状态码：{status_code}, 理由: {reason} 重试中..."
            )
            raise requests.HTTPError()

    try:
        _()
        return True
    except requests.RequestException as e:
        logger.error(f"从我的追漫列表中移除多次后失败!\n{e}")
        logger.exception(e)
        return False

