import ctypes
import logging
import os
import re
import time
from logging.handlers import TimedRotatingFileHandler

############################################################
# 配置全局网络请求的 timeout 以及 max retry
############################################################

TIMEOUT_SMALL = 2
TIMEOUT_LARGE = 5

MAX_RETRY_SMALL = 5000
MAX_RETRY_LARGE = 10000

RETRY_WAIT_EX = 200

############################################################
# 配置日志记录器
############################################################
appdata_path = os.getenv("APPDATA")
log_path = os.path.join(appdata_path, "BiliBili-Manga-Downloader", "logs")
if not os.path.exists(log_path):
    os.mkdir(log_path)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

#? 配置一个按天切割的日志记录器
log_handler = TimedRotatingFileHandler(os.path.join(log_path, "ERROR.log"),
                                        when='D', interval=1, backupCount=7, encoding="utf-8")
log_handler.suffix = "%Y-%m-%d.log"
log_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}(\.\w+)?$", re.ASCII)
log_handler.setFormatter(
    logging.Formatter(
        '%(asctime)s | %(levelname)s | %(module)s: %(funcName)s - %(lineno)d | %(message)s',
        datefmt='%H:%M:%S'
    )
)
log_handler.setLevel(logging.INFO)
logger.addHandler(log_handler)

############################################################
# Helper Functions
############################################################
def openFolderAndSelectItems(path : str) -> None:
    """ 读取一个文件的父目录, 如果可能的话，选择该文件。

        我们可以运行`explorer /select,filename`，
        但这并不支持在选择一个已经打开的目录中的文件时重复使用现有的资源管理器窗口。
        而且也不支持文件路径中包含空格和逗号等等的情况。
    Args:
        path (str): 文件或文件夹路径
    """
    path = os.path.normpath(path)
    try:
        # CoInitialize 和 CoUninitialize 是 Windows API 中的函数，用来初始化和反初始化COM(Component Object Model)库
        # CoInitialize 函数会初始化COM库，为当前线程分配资源。在调用CoInitialize之前，不能使用COM库，
        # 如果调用了CoInitialize函数，就必须在使用完COM库之后调用CoUninitialize函数来反初始化COM库。
        CoInitialize = ctypes.windll.ole32.CoInitialize
        CoInitialize.argtypes = [ctypes.c_void_p]
        CoInitialize.restype = ctypes.HRESULT
        CoUninitialize = ctypes.windll.ole32.CoUninitialize
        CoUninitialize.argtypes = []
        CoUninitialize.restype = None

        # ILCreateFromPathW 是一个 Windows API 函数，它可以根据给定的文件路径创建一个 Item ID List (PIDL)。
        # PIDL 是一种 Windows Shell 中使用的数据结构，用来表示文件系统中的对象（文件夹或文件）的位置。
        # 在这段代码中，使用了 ILCreateFromPath 函数来创建一个 PIDL，并在使用完之后使用 ILFree 函数来释放一个 PIDL 的内存.。这样可以避免内存泄漏
        ILCreateFromPath = ctypes.windll.shell32.ILCreateFromPathW
        ILCreateFromPath.argtypes = [ctypes.c_wchar_p]
        ILCreateFromPath.restype = ctypes.c_void_p
        ILFree = ctypes.windll.shell32.ILFree
        ILFree.argtypes = [ctypes.c_void_p]
        ILFree.restype = None

        # SHOpenFolderAndSelectItems 函数是一个 Windows API 函数，它是在 COM (Component Object Model) 环境中使用的
        SHOpenFolderAndSelectItems = ctypes.windll.shell32.SHOpenFolderAndSelectItems
        SHOpenFolderAndSelectItems.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_ulong,
        ]
        SHOpenFolderAndSelectItems.restype = ctypes.HRESULT

        CoInitialize(None)
        pidl = ILCreateFromPath(path)
        SHOpenFolderAndSelectItems(pidl, 0, None, 0)
        ILFree(pidl)
        CoUninitialize()

    except ValueError as e:
        logger.error(f"参数错误 - 打开文件夹失败 - 目录:{path}\n{e}")
    except TypeError as e:
        logger.error(f"类型错误 - 打开文件夹失败 - 目录:{path}\n{e}")
    except RuntimeError as e:
        logger.error(f"运行时错误 - 打开文件夹失败 - 目录:{path}\n{e}")
    except SystemError as e:
        logger.error(f"系统错误 - 打开文件夹失败 - 目录:{path}\n{e}")
    except OSError as e:
        logger.error(f"操作系统错误 - 打开文件夹失败 - 目录:{path}\n{e}")
    except AttributeError as e:
        logger.error(f"属性错误 - 打开文件夹失败 - 目录:{path}\n{e}")


class DownloadInfo:
    """
    下载任务的详细信息类，包含任务ID、任务文件进度，任务文件大小等，
    可以计算出当前下载速度、平均速度、剩余时间等信息
    """

    def __init__(self):
        self.info = {}
        self.average_speed_in_last_second = {}

    ############################################################
    def updateTask(self, taskID: int, rate: float, size: int = None) -> None:
        """更新任务信息

        Args:
            taskID (int): 任务ID
            rate (float): 下载进度百分比
            size (int, optional): 任务文件大小. Defaults to None.
        """
        rate /= 100

        if taskID not in self.info:
            self.info[taskID] = {
                'size': size,               # 任务文件大小  单位: Byte
                'rate': rate,               # 当前已下载百分比
                'last_rate': 0,             # 上次已下载百分比
                'curr_speed': None,         # 当前速度  单位: Byte/s
                'average_speed': None,      # 平均速度  单位: Byte/s
                'last_update_time': None,   # 上次更新时间 单位: 秒
                # 'remaining_time': None    # 剩余时间  单位: 秒
            }
        else:
            self.info[taskID]['rate'] = rate

        self.calcuCurrSpeed(self.info[taskID])
        self.calcuSmoothSpeed(self.info[taskID])
        # self.calcu_remaining_time(self.info[id])

    ############################################################
    def calcuCurrSpeed(self, task: dict) -> None:
        """计算任务的当前下载速度

        Args:
            task (dict): 任务信息
        """
        if task['rate'] == 0 or task['last_update_time'] is None:
            task['curr_speed'] = 0
            task['last_update_time'] = time.perf_counter()
            return
        curr_time = time.perf_counter()

        task['curr_speed'] = (task['size'] * task['rate'] - task['size'] * task['last_rate']) / (curr_time - task['last_update_time'])
        task['last_rate'] = task['rate']
        task['last_update_time'] = curr_time

    ############################################################
    def calcuSmoothSpeed(self, task: dict) -> None:
        """计算任务的平均下载速度

        Args:
            task (dict): 任务信息
        """
        SMOOTHING_FACTOR = 0.005
        # 使用 Exponential moving average 来均衡历史平均速度和当前速度，以防波动过大
        task['average_speed'] = SMOOTHING_FACTOR * task['curr_speed'] + (1-SMOOTHING_FACTOR) * (task['average_speed'] or task['curr_speed'])

    ############################################################
    def removeTask(self, taskID: int) -> None:
        """清空任务信息, 释放内存

        Args:
            taskID (int): 任务ID
        """
        self.info.pop(taskID)

    ############################################################
    def getTotalSmoothSpeedStr(self) -> str:
        """获取所有任务的平均速度

        Returns:
            str: 平均速度字符串
        """
        self.average_speed_in_last_second[time.perf_counter()] = sum(task['average_speed'] for task in self.info.values() if task['rate'] != 1.0)

        # 取5秒内的平均速度，以防止速度突然变化
        # 比如下载完一个文件 速度突然变为0
        # 或者开始一组新的下载，速度突然变为很大
        for key in list(self.average_speed_in_last_second.keys()):
            if key < time.perf_counter() - 5:
                self.average_speed_in_last_second.pop(key)

        return self.formatSize(
            sum(self.average_speed_in_last_second.values())
            / len(self.average_speed_in_last_second) or 1
        )

    ############################################################
    def formatSize(self, size: int) -> str:
        """格式化文件大小

        Args:
            size (int): 文件大小

        Returns:
            str: 格式化后的文件大小, 例如: 1.23MB/s
        """
        if size < 0:
            return '0B/s'
        elif size < 1024:
            return '%dB/s' % size
        elif size < 1024 * 1024:
            return '%.2fKB/s' % (size / 1024)
        elif size < 1024 * 1024 * 1024:
            return '%.2fMB/s' % (size / 1024 / 1024)
        elif size < 1024 * 1024 * 1024 * 1024:
            return '%.2fGB/s' % (size / 1024 / 1024 / 1024)
        else:
            return '%.2fTB/s' % (size / 1024 / 1024 / 1024 / 1024)

    ############################################################

    # #? 由于需要提前访问所有章节的所有图片链接的header来统计总下载大小
    # #? 轻易上千次的request产生的RTT会导致用户等待太长时间，所以放弃‘预计下载时间’功能
    # #? 如果B站后续更新API可以一次就获取一章的大小，就可以复用以下功能

    # def calcuRemainingTime(self, task) -> None:
    #     if task['average_speed'] != 0:
    #         task['remaining_time'] = (task['size'] * (1 - task['rate'])) / task['average_speed']

    # def getSmoothSpeed(self, task_id) -> str:
    #     if task_id in self.info:
    #         task = self.info[task_id]
    #         if task['average_speed'] != 0:
    #             return self.formatSize(task['average_speed'])
    #     return '0B/s'

    # def getTotalSmoothSpeed(self) -> int:
    #     return sum(task['average_speed'] for task in self.info.values() if task['rate'] != 1.0)

    # def get_remaining_time(self, task_id) -> str:
    #     if task_id in self.info:
    #         return self.formatTime(self.info[task_id]['remaining_time'])
    #     return '00:00:00'

    # def getTotalRemainingTime(self):
    #     total_size_left = sum(task['size'] * (1 - task['rate']) for task in self.info.values())
    #     if self.getTotalSmoothSpeed() == 0:
    #         return self.formatTime(0)
    #     return self.formatTime(total_size_left/self.getTotalSmoothSpeed())

    # def formatTime(self, seconds) -> str:
    #     m, s = divmod(seconds, 60)
    #     h, m = divmod(m, 60)
    #     return "%02d:%02d:%02d" % (h, m, s)
