

import hashlib
import json
import os
import re
import textwrap

import logging
from src.utils import *

import requests
from retrying import retry
from rich import print
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from src.Episode import Episode
from logging import Logger

console = Console()

class Comic:
    def __init__(self, logger: Logger, comicID: int, sessdata: str, rootPath: str, num_thread: int) -> None:
        self.logger = logger
        self.comicID = comicID
        self.sessdata = sessdata
        self.rootPath = rootPath
        self.num_thread = num_thread
        self.numDownloaded = 0
        self.episodes = []
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'origin': 'https://manga.bilibili.com',
            'referer': f'https://manga.bilibili.com/detail/mc{comicID}?from=manga_homepage',
            'cookie': f'SESSDATA={sessdata}'
        }
        

    def getComicInfo(self) -> dict:
        """
        使用哔哩哔哩漫画 API 分析漫画数据。
        Analyze data of a comic using the Bilibili Manga API.
        """
        
        # 爬取漫画信息
        detailUrl = 'https://manga.bilibili.com/twirp/comic.v1.Comic/ComicDetail?device=pc&platform=web'
        payload = {"comic_id": self.comicID}
        
        @retry(stop_max_delay=5000, wait_exponential_multiplier=200)
        def _():
            res = requests.post(detailUrl, data=payload, headers=self.headers)
            if res.status_code != 200:
                self.logger.warning(f'{self.comicID} 爬取漫画信息失败! {res.status_code} {res.reason} 重试中...')
                raise requests.HTTPError()
            return res
        try:
            data = _()
        except Exception as e:
            self.logger.error(f'{self.comicID} 重复解析漫画信息多次后失败! {e}')
            raise requests.HTTPError(f'{self.comicID} 爬取漫画信息失败!\n请检查输入信息是否正确!也可以查看日志文件或者联系作者')
        
        # 解析漫画信息
        data = data.json()
        if data['code']: 
            self.logger.warning(f'{self.comicID} 漫画信息有误! {data["msg"]}')
            raise ValueError()
        self.data = data['data']

        self.data['author_name'] = ', '.join(self.data['author_name'])
        self.data['styles'] = ', '.join(self.data['styles'])
        self.data['savePath'] = f"{self.rootPath}/《{self.data['title']}》 作者：{self.data['author_name']} ID-{self.comicID}"
        self.data['ID'] = self.comicID
        return self.data
        
    def getEpisodeInfo(self) -> list:
        # 解析章节
        if self.episodes:
            return [(epi.title, epi.isAvailable(), epi.isDownloaded()) for epi in self.episodes]
        
        epList = self.data['ep_list']
        for episode in reversed(epList):
            epi = Episode(self.logger, episode, self.sessdata, self.comicID, self.data['savePath'])
            self.episodes.append(epi)
            if epi.isDownloaded():
                self.numDownloaded += 1
        return [(epi.title, epi.isAvailable(), epi.isDownloaded()) for epi in self.episodes]

    def getNumDownloaded(self) -> int:
        return self.numDownloaded

    def fetch(self) -> None:
        """
        使用多线程获取和下载漫画数据
        Fetch and download comic data using multiple threads.
        """
        # 初始化储存文件夹
        if not os.path.exists(self.rootPath):
            os.mkdir(self.rootPath)
        if os.path.exists(self.savePath) and os.path.isdir(self.savePath):
            pass
        else:
            os.mkdir(self.savePath)

        from concurrent.futures import ThreadPoolExecutor, as_completed

        # 创建线程池爬取漫画
        with ThreadPoolExecutor(max_workers=8) as executor, Progress() as progress:
            epiTask = progress.add_task(f'正在下载 <{self.title}>', total=len(self.episodes))
            self.logger.info(f'开始下载 <{self.title} - 下载章节数:{len(self.episodes)}>')
            # 将下载任务提交到线程池中执行
            future_to_epi = {executor.submit(epi.download): epi for epi in self.episodes}
            # 等待所有任务完成
            for future in as_completed(future_to_epi):
                if future.done():
                    progress.update(epiTask, advance=1)
