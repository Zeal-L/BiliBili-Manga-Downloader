import hashlib
import json
import logging
import os
import re

import requests
from retrying import retry
from src.utils import *
from PySide6.QtCore import SignalInstance
from PIL import Image

class Episode:
    def __init__(self, logger: logging.Logger, episode: dict, sessData: str, comicID: str, comicName: str, savePath: str) -> None:
        self.logger = logger
        self.id = episode['id']
        self.available = not episode['is_locked']
        self.ord = episode['ord']
        self.comicName = comicName
        self.contentSize = 0
        
        # 修复标题中的特殊字符
        episode['short_title'] = re.sub(r'[\\/:*?"<>|]', ' ', episode['short_title'])
        episode['short_title'] = re.sub(r'\s+$', '', episode['short_title'])
        episode['title'] =  re.sub(r'[\\/:*?"<>|]', ' ', episode['title'])
        episode['title'] =  re.sub(r'\s+$', '', episode['title'])
        
        # 修复重复标题
        if episode['short_title'] == episode['title'] or episode['title'] == '':
            self.title = episode['short_title']
        else:
            self.title = f"{episode['short_title']} {episode['title']}"
        temp = re.search(r'^(\d+)\s+第(\d+)话', self.title)
        if temp and temp[1] == temp[2]:
            self.title = re.sub(r"^\d+\s+(第\d+话)", r"\1", self.title)
        if re.search(r'^特别篇\s+特别篇', self.title):
            self.title = re.sub(r'^特别篇\s+特别篇', r"特别篇", self.title)

        # 修复短标题中的数字
        if re.search(r'^[0-9\-]+话', self.title):
            self.title = re.sub(r'^([0-9\-]+)', r'第\1', self.title)
        elif re.search(r'^[0-9\-]+', self.title):
            self.title = re.sub(r'^([0-9\-]+)', r'第\1话', self.title)

        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'origin': 'https://manga.bilibili.com',
            'referer': f'https://manga.bilibili.com/detail/mc{comicID}/{self.id}?from=manga_homepage',
            'cookie': f'SESSDATA={sessData}'
        }
        self.savePath = savePath
    
    def isAvailable(self) -> bool:
        """
        判断章节是否可用
        True: 已解锁章节
        False: 需付费章节
        """
        return self.available
    
    def isDownloaded(self) -> bool:
        """
        判断章节是否已下载
        True: 已下载
        False: 未下载
        """
        return os.path.exists(f'{self.savePath}/{self.title}.pdf')
    
    def download(self, rate_progress: SignalInstance, taskID: str) -> None:
        """
        下载章节内所有图片 并合并为PDF
        """
        
        self.taskID = taskID
        
        # 获取图片列表
        GetImageIndexURL = 'https://manga.bilibili.com/twirp/comic.v1.Comic/GetImageIndex?device=pc&platform=web'
        @retry(stop_max_delay=5000, wait_exponential_multiplier=200)
        def _():
            res = requests.post(GetImageIndexURL, data={'ep_id': self.id}, headers=self.headers)
            if res.status_code != 200:
                self.logger.warning(f'{self.title} 获取图片列表失败! {res.status_code} {res.reason} 重试中...')
                raise requests.HTTPError()
            return res
        try:
            data = _()
        except Exception as e:
            self.logger.error(f'{self.title} 重复获取图片列表多次后失败! {e}')
            raise requests.HTTPError(f'{self.title} 重复获取图片列表多次后失败!, 请查看日志文件或者联系作者')
        
        images = data.json()['data']['images']
        paths = [img['path'] for img in images]

        # 获取图片token
        ImageTokenURL = "https://manga.bilibili.com/twirp/comic.v1.Comic/ImageToken?device=pc&platform=web"
        @retry(stop_max_delay=5000, wait_exponential_multiplier=200)
        def _():
            res = requests.post(ImageTokenURL, data={"urls": json.dumps(paths)}, headers=self.headers)
            if res.status_code != 200:
                self.logger.warning(f'{self.title} 获取图片token失败! {res.status_code} {res.reason} 重试中...')
                raise requests.HTTPError()
            return res
        try:
            data = _()
        except Exception as e:
            self.logger.error(f'{self.title} 重复获取图片token多次后失败! {e}')
            raise requests.HTTPError(f'{self.title} 重复获取图片token多次后失败!, 请查看日志文件或者联系作者')
        
        # 获取图片大小
        for index, img in enumerate(data.json()['data'], start=1):
            try:
                self.calculateEpiSize(index, img['url'], img['token'])
            except Exception as e:
                self.logger.error(f"{self.title} - {index, img['url'], img['token']} - 重复获取图片大小多次后失败! - {e}")
                raise requests.HTTPError(f'{self.title} 重复获取图片大小多次后失败!, 请查看日志文件或者联系作者')
        
        # 下载所有图片
        imgs = []
        for index, img in enumerate(data.json()['data'], start=1):
            try:
                imgs.append(self.downloadImg(index, img['url'], img['token']))
                rate_progress.emit({
                    "taskID": self.taskID,
                    "rate": int((index / len(data.json()['data'])) * 100),
                    "path": f"{self.savePath}/{self.title}.pdf"
                })
            except Exception as e:
                self.logger.error(f"{self.title} - {index, img['url'], img['token']} - 重复下载图片多次后失败! - {e}")
                raise requests.HTTPError(f'{self.title} 重复下载图片多次后失败!, 请查看日志文件或者联系作者')

        # 统一转换为RGB模式
        tempImgs = [Image.open(x) for x in imgs]
        for i,img in enumerate(tempImgs):
            if img.mode != 'RGB':
                tempImgs[i] = img.convert('RGB')

        # 合并PDF
        try:
            tempImgs[0].save(os.path.join(self.savePath, f"{self.title}.pdf"), save_all=True, append_images=tempImgs[1:], quality=95)
            
        except Exception as e:
            self.logger.error(f'{self.title} 合并PDF失败! {e} - {imgs}')
            raise ValueError(f'{self.title} 合并PDF失败!, 请查看日志文件或者联系作者')

        # 删除临时图片
        for img in imgs:
            os.remove(img)

    @retry(stop_max_delay=10000, wait_exponential_multiplier=200)
    def calculateEpiSize(self, index: int, url: str, token: str) -> str:
        """
        根据 url 和 token 计算图片大小
        """
        url = f"{url}?token={token}"
        head = requests.head(url)
        if head.status_code != 200:
            self.logger.error(f"{self.title} - {index, url} - 获取图片大小失败! 重试中... {head.status_code} {head.reason}")
            raise requests.HTTPError()
        
        self.contentSize += int(head.headers['Content-Length'])


    def getEpiSize(self):
        """
        获取章节大小
        """
        return self.contentSize
    
    @retry(stop_max_delay=10000, wait_exponential_multiplier=200)
    def downloadImg(self, index: int, url: str, token: str) -> str:
        """
        根据 url 和 token 下载图片
        """
        url = f"{url}?token={token}"
        
        file = requests.get(url)
        
        if file.status_code != 200:
            self.logger.error(f"{self.title} - {index, url} - 下载图片失败! 重试中... {file.status_code} {file.reason}")
            raise requests.HTTPError()
        if file.headers['Etag'] != hashlib.md5(file.content).hexdigest():
            self.logger.error(f"{self.title} - {index, url} - 下载内容Checksum不正确! 重试中... {file.headers['Etag']} ≠ {hashlib.md5(file.content).hexdigest()}")
            raise ValueError()

        pathToSave = os.path.join(self.savePath, f"{self.ord}_{index}.jpg")
        with open(pathToSave, 'wb') as f:
            f.write(file.content)
        return pathToSave