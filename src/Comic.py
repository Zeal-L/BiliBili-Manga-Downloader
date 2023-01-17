

import hashlib
import json
import os
import re
import textwrap

import logging
from src.utils import *

import requests
from PIL import Image
from retrying import retry
from rich import print
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from src.Episode import Episode

console = Console()

class Comic:
    def __init__(self, logger: logging.Logger, comicID: int, sessdata: str, rootPath: str) -> None:
        self.logger = logger
        self.comicID = comicID
        self.sessdata = sessdata
        self.rootPath = rootPath
        info(f'初始化漫画 ID {comicID}')
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'origin': 'https://manga.bilibili.com',
            'referer': f'https://manga.bilibili.com/detail/mc{comicID}?from=manga_homepage',
            'cookie': f'SESSDATA={sessdata}'
        }
        self.analyzeData()

    def analyzeData(self) -> None:
        """
        使用哔哩哔哩漫画 API 分析漫画数据。
        Analyze data of a comic using the Bilibili Manga API.
        """
        
        # 爬取漫画信息
        detailUrl = 'https://manga.bilibili.com/twirp/comic.v1.Comic/ComicDetail?device=pc&platform=web'
        payload = {"comic_id": self.comicID}
        with console.status('正在访问 BiliBili Manga'):
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
        info('已获取漫画信息!')
        info('开始解析...')
        data = data.json()
        if data['code']: 
            error(f'漫画信息有误! 请仔细检查! (提示信息{data["msg"]})')
            self.logger.warning(f'{self.comicID} 漫画信息有误! {data["msg"]}')
            raise ValueError()
        
        
        self.title = data['data']['title']
        self.authorName = data['data']['author_name']
        self.styles = data['data']['styles']
        self.evaluate = data['data']['evaluate']
        self.total = data['data']['total']
        self.savePath = f"{self.rootPath}/《{self.title}》 作者：{', '.join(self.authorName)}"

        # 打印漫画信息
        t = Table(title='漫画作品详情')
        t.add_column('[green bold]作品标题[/green bold]')
        t.add_column('[green bold]作者[/green bold]')
        t.add_column('[green bold]标签[/green bold]')
        t.add_column('[green bold]概要[/green bold]')
        t.add_column('[green bold]总章节数[/green bold]')
        t.add_row(self.title, ', '.join(self.authorName), ''.join(self.styles), textwrap.fill(self.evaluate, width=30), str(self.total))
        print(t)

        # 选择下载章节
        while True:
            start = requireInt('开始章节(不输入则不限制): ', False)
            start = 0 if start is None else start
            end = requireInt('结束章节(不输入则不限制): ', False)
            end = 2147483647 if end is None else end
            if start <= end: break
            error('开始章节必须小于结束章节!')
        
        # 解析章节
        self.episodes = []
        with console.status('正在解析详细章节...'):
            epList = data['data']['ep_list']
            epList.reverse()
            for episode in epList:
                epi = Episode(self.logger, episode, self.sessdata, self.comicID, self.savePath)
                if start <= epi.ord <= end and epi.isAvailable():
                    self.episodes.append(epi)

        # 打印章节信息
        print("已选中章节:")
        for episode in self.episodes:
            print(f"\t<{episode.title}>")
        info(f'分析结束 将爬取章节数: {len(self.episodes)} 输入回车开始爬取!')
        input()

    def fetch(self) -> None:
        """
        使用多线程获取和下载漫画数据
        Fetch and download comic data using multiple threads.
        """
        # 初始化储存文件夹
        if not os.path.exists(self.rootPath):
            os.mkdir(self.rootPath)
        if os.path.exists(self.savePath) and os.path.isdir(self.savePath):
            info('存在历史下载 将避免下载相同文件!')
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

        info('任务完成!')