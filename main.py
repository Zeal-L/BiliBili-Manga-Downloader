import datetime
import hashlib
import json
import os
import re
import textwrap
import time
import logging

import requests
from PIL import Image
from retrying import retry
from rich import print
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

console = Console()
logging.basicConfig(filename='ERRORrecord.log', 
                    level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | 模块:%(module)s | 函数:%(funcName)s %(lineno) d行 | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    encoding="utf-8")

logger = logging.getLogger(__name__)

def timeStr():
    t = datetime.datetime.fromtimestamp(time.time())
    timeStr = t.strftime("[ %Y.%m.%d %H:%M:%S ]")
    return f"{timeStr}"


def info(msg):
    logStr = f"{timeStr()} [b]|[rgb(51, 204, 204)]INFO[/]|[/b] {msg}"
    print(logStr)


def error(msg):
    logStr = f"{timeStr()} [b]|[rgb(204, 0, 0)]ERROR[/]|[/b] {msg}"
    print(logStr)

def requireInt(msg, notNull):
    while True:
        userInput = input(msg)
        try:
            return None if len(userInput) == 0 and (not notNull) else int(userInput)
        except ValueError:
            error('请输入数字...')

class Comic:
    def __init__(self, comicID: int, sessdata: str, rootPath: str) -> None:
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
                    logger.warning(f'{self.comicID} 爬取漫画信息失败! {res.status_code} {res.reason} 重试中...')
                    raise requests.HTTPError()
                return res
        try:
            data = _()
        except Exception as e:
            logger.error(f'{self.comicID} 重复解析漫画信息多次后失败! {e}')
            raise requests.HTTPError(f'{self.comicID} 爬取漫画信息失败!\n请检查输入信息是否正确!也可以查看日志文件或者联系作者')
        
        # 解析漫画信息
        info('已获取漫画信息!')
        info('开始解析...')
        data = data.json()
        if data['code']: 
            error(f'漫画信息有误! 请仔细检查! (提示信息{data["msg"]})')
            logger.warning(f'{self.comicID} 漫画信息有误! {data["msg"]}')
            raise ValueError()
        
        
        self.title = data['data']['title']
        self.authorName = data['data']['author_name']
        self.styles = data['data']['styles']
        self.evaluate = data['data']['evaluate']
        self.total = data['data']['total']
        self.savePath = f"{rootPath}/《{self.title}》 作者：{', '.join(self.authorName)}"

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
                epi = Episode(episode, self.sessdata, self.comicID, self.savePath)
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
            logger.info(f'开始下载 <{self.title} - 下载章节数:{len(self.episodes)}>')
            # 将下载任务提交到线程池中执行
            future_to_epi = {executor.submit(epi.download): epi for epi in self.episodes}
            # 等待所有任务完成
            for future in as_completed(future_to_epi):
                if future.done():
                    progress.update(epiTask, advance=1)

        info('任务完成!')

class Episode:
    def __init__(self, episode, sessData: str, comicID: str, savePath: str) -> None:
        self.id = episode['id']
        self.available = not episode['is_locked']
        self.ord = episode['ord']
        
        # 修复标题中的特殊字符
        episode['short_title'] = re.sub(r'[\\/:*?"<>|]', ' ', episode['short_title'])
        episode['short_title'] = re.sub(r'\s+$', '', episode['short_title'])
        episode['title'] =  re.sub(r'[\\/:*?"<>|]', ' ', episode['title'])
        episode['title'] =  re.sub(r'\s+$', '', episode['title'])
        
        # 修复短标题中的数字
        if re.search(r'^\d+$', episode['short_title']):
            new_short_title = f"第{episode['short_title']}话"
        elif re.search(r'^\d+话', episode['short_title']):
            new_short_title = f"第{episode['short_title']}"
        else:
            new_short_title = episode['short_title']

        # 修复标题
        if episode['short_title'] == episode['title'] or episode['title'] == '':
            self.title = new_short_title
        else:
            self.title = f"{new_short_title} {episode['title']}"
        
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
    
    def download(self) -> None:
        """
        下载章节内所有图片 并合并为PDF
        """
        
        # 相同文件名已经存在 跳过下载
        if os.path.exists(f'{self.savePath}/{self.title}.pdf'):
            return False
        
        # 获取图片列表
        GetImageIndexURL = 'https://manga.bilibili.com/twirp/comic.v1.Comic/GetImageIndex?device=pc&platform=web'
        @retry(stop_max_delay=5000, wait_exponential_multiplier=200)
        def _():
            res = requests.post(GetImageIndexURL, data={'ep_id': self.id}, headers=self.headers)
            if res.status_code != 200:
                logger.warning(f'{self.title} 获取图片列表失败! {res.status_code} {res.reason} 重试中...')
                raise requests.HTTPError()
            return res
        try:
            data = _()
        except Exception as e:
            logger.error(f'{self.title} 重复获取图片列表多次后失败! {e}')
            raise requests.HTTPError(f'{self.title} 重复获取图片列表多次后失败!, 请查看日志文件或者联系作者')
        
        images = data.json()['data']['images']
        paths = [img['path'] for img in images]

        # 获取图片token
        ImageTokenURL = "https://manga.bilibili.com/twirp/comic.v1.Comic/ImageToken?device=pc&platform=web"
        @retry(stop_max_delay=5000, wait_exponential_multiplier=200)
        def _():
            res = requests.post(ImageTokenURL, data={"urls": json.dumps(paths)}, headers=self.headers)
            if res.status_code != 200:
                logger.warning(f'{self.title} 获取图片token失败! {res.status_code} {res.reason} 重试中...')
                raise requests.HTTPError()
            return res
        try:
            data = _()
        except Exception as e:
            logger.error(f'{self.title} 重复获取图片token多次后失败! {e}')
            raise requests.HTTPError(f'{self.title} 重复获取图片token多次后失败!, 请查看日志文件或者联系作者')
        
        imgs = []
        for index, img in enumerate(data.json()['data'], start=1):
            try:
                imgs.append(self.downloadImg(index, img['url'], img['token']))
            except Exception as e:
                logger.error(f"{self.title} - {index, img['url'], img['token']} - 重复下载图片多次后失败! - {e}")
                raise requests.HTTPError(f'{self.title} 重复下载图片多次后失败!, 请查看日志文件或者联系作者')

        # 旧方法，偶尔会出现pdf打不开的情况, 猜测可能是img文件信道的问题
        # import img2pdf
        # with open(os.path.join(self.savePath, f"{self.title}.pdf"), 'wb') as f:
        #     f.write(img2pdf.convert(imgs))

        # 新方法
        tempImgs = [Image.open(x) for x in imgs]
        for i,img in enumerate(tempImgs):
            if img.mode != 'RGB':
                tempImgs[i] = img.convert('RGB')

        try:
            tempImgs[0].save(os.path.join(self.savePath, f"{self.title}.pdf"), save_all=True, append_images=tempImgs[1:])
        except Exception as e:
            logger.error(f'{self.title} 合并PDF失败! {e} - {imgs}')
            raise ValueError(f'{self.title} 合并PDF失败!, 请查看日志文件或者联系作者')

        for img in imgs:
            os.remove(img)

        info(f'已下载 <{self.title}>')

    @retry(stop_max_delay=10000, wait_exponential_multiplier=200)
    def downloadImg(self, index: int, url: str, token: str) -> str:
        """
        根据 url 和 token 下载图片
        """
        url = f"{url}?token={token}"
        file = requests.get(url)
        if file.status_code != 200:
            logger.error(f"{self.title} - {index, url} - 下载图片失败! 重试中... {file.status_code} {file.reason}")
            raise requests.HTTPError()
        if file.headers['Etag'] != hashlib.md5(file.content).hexdigest():
            logger.error(f"{self.title} - {index, url} - 下载内容Checksum不正确! 重试中... {file.headers['Etag']} ≠ {hashlib.md5(file.content).hexdigest()}")
            raise ValueError()

        pathToSave = os.path.join(self.savePath, f"{self.ord}_{index}.jpg")
        with open(pathToSave, 'wb') as f:
            f.write(file.content)
        return pathToSave


if __name__ == '__main__':
    rootPath = "C://Users//Zeal//Desktop//漫画"
    
    # comicID = requireInt('请输入漫画ID: ', True)
    # userInput = input('请输入SESSDATA (免费漫画请直接按下enter): ')
    
    comicID = 'mc26551'
    comicID = re.sub(r'^mc', '', comicID)
    # sessdata = '6a2f415f%2C1689285165%2C3ac9d%2A11'
    sessdata = 'f5230c77%2C1689341122%2Cd6518%2A11'
    manga = Comic(comicID, sessdata, rootPath)
    manga.fetch()
