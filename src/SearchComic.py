"""
该模块包含一个用于根据漫画名搜索漫画信息的类SearchComic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import requests
from PySide6.QtWidgets import QMessageBox
from retrying import retry

from src.Utils import MAX_RETRY_SMALL, RETRY_WAIT_EX, TIMEOUT_SMALL, logger

if TYPE_CHECKING:
    from ui.MainGUI import MainGUI


class SearchComic:
    """根据名字搜索漫画类"""

    def __init__(self, comic_name: str, sessdata: str) -> None:
        self.comic_name = comic_name
        self.sessdata = sessdata
        self.detail_url = "https://manga.bilibili.com/twirp/comic.v1.Comic/Search?device=pc&platform=web"
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
            "origin": "https://manga.bilibili.com",
            "referer": "https://manga.bilibili.com/search?from=manga_homepage",
            "cookie": f"SESSDATA={sessdata}",
        }
        self.payload = {"key_word": comic_name, "page_num": 1, "page_size": 99}

    ############################################################
    def getResults(self, mainGUI: MainGUI) -> list:
        """获取搜索结果

        Returns:
            list: 搜索结果列表
        """

        @retry(
            stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX
        )
        def _() -> list:
            try:
                res = requests.post(
                    self.detail_url,
                    data=self.payload,
                    headers=self.headers,
                    timeout=TIMEOUT_SMALL,
                )
            except requests.RequestException as e:
                logger.warning(f"获取搜索结果失败! 重试中...\n{e}")
                raise e
            if res.status_code != 200:
                logger.warning(
                    f"获取搜索结果失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中..."
                )
                raise requests.HTTPError()
            return res.json()["data"]["list"]

        logger.info(f"正在搜索漫画:《{self.comic_name}》中...")

        try:
            data = _()
        except requests.RequestException as e:
            logger.error(f"重复获取搜索结果多次后失败!\n{e}")
            logger.exception(e)
            QMessageBox.warning(
                mainGUI, "警告", "重复获取搜索结果多次后失败!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件"
            )
            return []

        logger.info(f"搜索结果数量:{len(data)}")
        return data
