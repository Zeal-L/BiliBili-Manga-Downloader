import os
import time
import ctypes


def openFolderAndSelectItems(path):
    """ 读取一个文件的父目录, 如果可能的话，选择该文件。
        
        我们可以运行`explorer /select,filename`，
        但这并不支持在选择一个已经打开的目录中的文件时重复使用现有的资源管理器窗口。
        而且也不支持文件路径中包含空格和逗号等等的情况。
    """
    path = os.path.normpath(path)
    
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
    # ILFree 函数是 Windows API 中的函数, 用来释放一个 PIDL 的内存. 
    # 在这段代码中，使用了 ILCreateFromPath 函数来创建一个 PIDL，并在使用完之后使用 ILFree 函数来释放内存。这样可以避免内存泄漏
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

class DownloadInfo:
    def __init__(self):
        self.info = {}
        self.averageSpeedInLastSecond = {}

    def update_task(self, id, rate, size=None):
        rate = rate / 100
        if id not in self.info:
            self.info[id] = {
                'size': size,           # 任务文件大小  单位: Byte
                'rate': rate,           # 当前已下载百分比
                'lastRate': 0,          # 上次已下载百分比
                'currSpeed': None,      # 当前速度  单位: Byte/s
                'averageSpeed': None,   # 平均速度  单位: Byte/s
                'lastUpdateTime': None, # 上次更新时间 单位: 秒
                # 'remainingTime': None   # 剩余时间  单位: 秒
            }
        else:
            self.info[id]['rate'] = rate
        self.calcuCurrSpeed(self.info[id])
        self.calcuSmoothSpeed(self.info[id])
        # self.calcuRemainingTime(self.info[id])
    
    def calcuCurrSpeed(self, task) -> None:
        if task['rate'] == 0 or task['lastUpdateTime'] is None:
            task['currSpeed'] = 0
            task['lastUpdateTime'] = time.perf_counter()
            return
        currTime = time.perf_counter()

        task['currSpeed'] = (task['size'] * task['rate'] - task['size'] * task['lastRate']) / (currTime - task['lastUpdateTime'])
        task['lastRate'] = task['rate']
        task['lastUpdateTime'] = currTime
    
    def calcuSmoothSpeed(self, task) -> None:
        SMOOTHING_FACTOR = 0.005
        # 使用 Exponential moving average 来均衡历史平均速度和当前速度，以防波动过大
        task['averageSpeed'] = SMOOTHING_FACTOR * task['currSpeed'] + (1-SMOOTHING_FACTOR) * (task['averageSpeed'] or task['currSpeed'])

    def removeTask(self, taskID):
        self.info.pop(taskID)

    def getTotalSmoothSpeedStr(self):
        self.averageSpeedInLastSecond[time.perf_counter()] = sum(task['averageSpeed'] for task in self.info.values() if task['rate'] != 1.0)

        # 取5秒内的平均速度，以防止速度突然变化
        # 比如下载完一个文件 速度突然变为0
        # 或者开始一组新的下载，速度突然变为很大
        for key in list(self.averageSpeedInLastSecond.keys()):
            if key < time.perf_counter() - 5:
                self.averageSpeedInLastSecond.pop(key)

        return self.formatSize(
            sum(self.averageSpeedInLastSecond.values())
            / len(self.averageSpeedInLastSecond) or 1
        )

    def formatSize(self, size) -> str:
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

    # #? 由于需要提前访问所有章节的所有图片链接的header来统计总下载大小
    # #? 轻易上千次的request产生的RTT会导致用户等待太长时间，所以放弃‘预计下载时间’功能
    # #? 如果B站后续更新API可以一次就获取一章的大小，就可以复用以下功能

    # def calcuRemainingTime(self, task) -> None:
    #     if task['averageSpeed'] != 0:
    #         task['remainingTime'] = (task['size'] * (1 - task['rate'])) / task['averageSpeed']

    # def getSmoothSpeed(self, id) -> str:
    #     if id in self.info:
    #         task = self.info[id]
    #         if task['averageSpeed'] != 0:
    #             return self.formatSize(task['averageSpeed'])
    #     return '0B/s'
    
    # def getTotalSmoothSpeed(self):
    #     return sum(task['averageSpeed'] for task in self.info.values() if task['rate'] != 1.0)
        
    # def getRemainingTime(self, id) -> str:
    #     if id in self.info:
    #         return self.formatTime(self.info[id]['remainingTime'])
    #     return '00:00:00'
    
    # def getTotalRemainingTime(self):
    #     totalSizeLeft = sum(task['size'] * (1 - task['rate']) for task in self.info.values())
    #     if self.getTotalSmoothSpeed() == 0:
    #         return self.formatTime(0)
    #     return self.formatTime(totalSizeLeft/self.getTotalSmoothSpeed())

    # def formatTime(self, seconds) -> str:
    #     m, s = divmod(seconds, 60)
    #     h, m = divmod(m, 60)
    #     return "%02d:%02d:%02d" % (h, m, s)
