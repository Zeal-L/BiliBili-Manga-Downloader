"""
该模块包含一个用于根据漫画名搜索漫画信息的类SearchComic
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import requests
from retrying import retry

from src.Utils import MAX_RETRY_SMALL, RETRY_WAIT_EX, TIMEOUT_SMALL, getRamdomKaomojis, logger

if TYPE_CHECKING:
    from ui.MainGUI import MainGUI


class SearchComic:
    """根据名字搜索漫画类"""

    def __init__(self, comic_name: str, sessdata: str) -> None:
        self.comic_name = comic_name
        self.sessdata = sessdata
        # self.detail_url = ("https://manga.bilibili.com/twirp/comic.v1.Comic/Search?device=pc&platform=web")
        # self.payload = {"key_word": comic_name, "page_num": 1, "page_size": 99}
        self.detail_url = ("https://manga.bilibili.com/twirp/search.v1.Search/SearchKeyword")
        self.payload = json.dumps({"keyword": self.comic_name, "pageNum": 1, "pageSize": 99})
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "origin": "https://manga.bilibili.com",
            "referer": "https://manga.bilibili.com/search?from=manga_homepage",
            # "cookie": f"SESSDATA={sessdata}",  # 使用客户端搜索API无需cookie
        }

    ############################################################
    def getResults(self, mainGUI: MainGUI) -> list:
        """获取搜索结果

        Returns:
            list: 搜索结果列表
        """

        @retry(stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX)
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
            elif res.json().get("code") == 401:
                mainGUI.signal_confirm_box.emit(
                    f"搜索次数过多，需要人机验证，验证完毕关闭即可～ {getRamdomKaomojis("sad")}\n"
                    f"点击确定打开打开网页完成滑动验证",
                    lambda: mainGUI.signal_open_web_view.emit(
                        "风险验证", "https://manga.bilibili.com/search?keyword=%10"
                    )
                )
                return []
            elif res.json().get("code") == 403:
                mainGUI.signal_warning_box.emit(
                    f"您的搜索次数已达今日上限 {getRamdomKaomojis("helpless")}"
                )
                return []
            elif res.json().get("code") != 0:
                mainGUI.signal_warning_box.emit(
                    f"获取搜索结果失败! 理由: {res.json().get("msg")} "
                )
                return []
            return res.json()["data"]["comic_data"]["list"]

        logger.info(f"正在搜索漫画:《{self.comic_name}》中...")

        try:
            data = _()
        except requests.RequestException as e:
            logger.error(f"重复获取搜索结果多次后失败!\n{e}")
            logger.exception(e)
            mainGUI.signal_warning_box.emit(
                f"重复获取搜索结果多次后失败!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件",
            )
            return []

        logger.info(f"搜索结果数量:{len(data)}")
        return data
