
from __future__ import annotations

import typing

import requests
from retrying import retry, RetryError
from PySide6.QtWidgets import QMessageBox

from src.Episode import Episode
from src.utils import (logger, MAX_RETRY_SMALL, RETRY_WAIT_EX, TIMEOUT_SMALL)

if typing.TYPE_CHECKING:
    from ui.MainGUI import MainGUI


class Comic:
    """单本漫画 综合信息类
    """
    def __init__(self, comic_id: int, sessdata: str, save_path: str, num_thread: int) -> None:
        self.comic_id = comic_id
        self.sessdata = sessdata
        self.save_path = save_path
        self.num_thread = num_thread
        self.num_downloaded = 0
        self.episodes = []
        self.data = None
        self.detail_url = 'https://manga.bilibili.com/twirp/comic.v1.Comic/ComicDetail?device=pc&platform=web'
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'origin': 'https://manga.bilibili.com',
            'referer': f'https://manga.bilibili.com/detail/mc{comic_id}?from=manga_homepage',
            'cookie': f'SESSDATA={sessdata}'
        }
        self.payload = {"comic_id": self.comic_id}

    ############################################################
    def getComicInfo(self, mainGUI: MainGUI) -> dict:
        """使用哔哩哔哩漫画 API 分析漫画数据

        Returns:
            dict: 漫画信息
        """

        @retry(stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX)
        def _() -> dict:
            try:
                res = requests.post(self.detail_url, headers=self.headers, data=self.payload, timeout=TIMEOUT_SMALL)
            except requests.RequestException() as e:
                logger.warning(f"漫画id:{self.comic_id} 获取漫画信息失败! 重试中...\n{e}")
                raise e
            if res.status_code != 200:
                logger.warning(f'漫画id:{self.comic_id} 爬取漫画信息失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中...')
                raise requests.HTTPError()
            return res.json()['data']

        try:
            self.data = _()
        except RetryError as e:
            logger.error(f'漫画id:{self.comic_id} 重复获取漫画信息多次后失败!\n{e}')
            QMessageBox.warning(mainGUI, "警告", "重复获取漫画信息多次后失败!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！")
            return {}

        #?###########################################################
        #? 解析漫画信息
        self.data['author_name'] = '，'.join(self.data['author_name'])
        self.data['styles'] = '，'.join(self.data['styles'])
        self.data['save_path'] = f"{self.save_path}/《{self.data['title']}》 作者：{self.data['author_name']} ID-{self.comic_id}"
        self.data['ID'] = self.comic_id
        return self.data

    ############################################################
    def getEpisodesInfo(self) -> list:
        """获取章节信息

        Returns:
            list: 章节信息列表
        """
        if self.episodes:
            return self.episodes
        if not self.data:
            return []

        #?###########################################################
        #? 解析章节
        ep_list = self.data['ep_list']
        for episode in reversed(ep_list):
            epi = Episode(episode, self.sessdata, self.comic_id, self.data['title'], self.data['save_path'])
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

