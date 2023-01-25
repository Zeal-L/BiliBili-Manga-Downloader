import datetime
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

from rich.progress import Progress
import io

class RemainingTime:
    def __init__(self):
        self.remaining_time = {}
        self.last_update_time = {}
        self.progress = {}
        self.totalProgress = {}
        self.temp = io.StringIO()
        self.p = Progress(disable=True, redirect_stdout=(True, self.temp))

    def update_task(self, id, rate):
        if id not in self.progress:
            self.progress[id] = self.p.add_task(f'正在下载 <{id}>', total=100)
        
        self.p.update(self.progress[id], completed=rate)
        # self.remaining_time[id] = temp
    def getRmainingTime(self, id) -> str:

        
        return self.remaining_time[id]

    def getTotalRmainingTime(self):
        print(self.temp.getvalue())
    