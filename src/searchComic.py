import logging
from src.utils import *

import requests
from retrying import retry
from logging import Logger

class SearchComic:
    def __init__(self, logger: Logger, comicName: str, sessdata: str) -> None:
        self.logger = logger
        self.comicName = comicName
        self.sessdata = sessdata
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'origin': 'https://manga.bilibili.com',
            'referer': f'https://manga.bilibili.com/search?from=manga_homepage&keyword={comicName}',
            'cookie': f'SESSDATA={sessdata}'
        }
    
    def getResults(self):
        # 爬取漫画信息
        detailUrl = 'https://manga.bilibili.com/twirp/comic.v1.Comic/Search?device=pc&platform=web'
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'origin': 'https://manga.bilibili.com',
            'referer': 'https://manga.bilibili.com/',
            'cookie': f'SESSDATA={self.sessdata}'
        }
        payload = { 
            "key_word": self.comicName,
            "page_num": 1,
            "page_size": 99
        }
        
        @retry(stop_max_delay=5000, wait_exponential_multiplier=200)
        def _():
            res = requests.post(detailUrl, data=payload, headers=headers)
            if res.status_code != 200:
                self.logger.warning(f'{self.comicName} 爬取漫画信息失败! {res.status_code} {res.reason} 重试中...')
                raise requests.HTTPError()
            return res
        try:
            data = _()
        except Exception as e:
            self.logger.error(f'{self.comicName} 重复解析漫画信息多次后失败! {e}')
            raise requests.HTTPError(f'{self.comicName} 爬取漫画信息失败!\n请检查输入信息是否正确!也可以查看日志文件或者联系作者')
        
        data = data.json()
        return data
