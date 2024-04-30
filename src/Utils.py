"""
该模块包含了一些工具函数和类，用于支持BiliBili漫画下载器的其他模块
"""

from __future__ import annotations

import ctypes
import hashlib
import logging
import os
import re
from ctypes import CDLL, c_int
from logging.handlers import TimedRotatingFileHandler
from sys import platform
from typing import TYPE_CHECKING

import requests
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QMessageBox
from retrying import retry

if TYPE_CHECKING:
    from ui.MainGUI import MainGUI

__app_name__ = "BiliBili-Manga-Downloader"
__version__ = "1.6.0"
__author__ = "Zeal L"
__copyright__ = "Copyright (C) 2023-2024 Zeal L"
__main_window_title__ = f"哔哩哔哩漫画下载器 v{__version__}"

############################################################
# 配置全局网络请求的 timeout 以及 max retry
############################################################

TIMEOUT_SMALL = 5
TIMEOUT_LARGE = 10

MAX_RETRY_TINY = 4000
MAX_RETRY_SMALL = 10000
MAX_RETRY_LARGE = 20000

RETRY_WAIT_EX = 200

############################################################
# 配置日志记录器
############################################################

if platform == "win32":
    appdata_path = os.getenv("APPDATA")
elif platform == "darwin":
    appdata_path = os.getenv("HOME")
elif platform == "linux":
    appdata_path = os.getenv("HOME")

data_path = os.path.join(appdata_path, "BiliBili-Manga-Downloader")
if not os.path.exists(data_path):
    os.mkdir(data_path)

log_path = os.path.join(data_path, "logs")
if not os.path.exists(log_path):
    os.mkdir(log_path)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ? 配置一个按天切割的日志记录器
log_handler = TimedRotatingFileHandler(
    os.path.join(log_path, "ERROR.log"),
    when="D",
    interval=1,
    backupCount=7,
    encoding="utf-8",
)
log_handler.suffix = "%Y-%m-%d.log"
log_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}(\.\w+)?$", re.ASCII)
log_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s | %(levelname)s | %(module)s: %(funcName)s - %(lineno)d | %(message)s",
        datefmt="%H:%M:%S",
    )
)
log_handler.setLevel(logging.INFO)
logger.addHandler(log_handler)


############################################################
# Helper Functions
############################################################


def myStrFilter(s: str) -> str:
    """过滤字符串中的非法字符

    Args:
        s (str): 待过滤的字符串

    Returns:
        str: 过滤后的字符串
    """

    s = re.sub(r"[\\/]", " ", s)
    s = re.sub(r":", "：", s)
    s = re.sub(r"\*", "⭐", s)
    s = re.sub(r"\?", "？", s)
    s = re.sub(r'"', "'", s)
    s = re.sub(r"<", "《", s)
    s = re.sub(r">", "》", s)
    s = re.sub(r"\|", "丨", s)
    s = re.sub(r"\s+$", "", s)
    s = re.sub(r"^\s+", " ", s)
    s = re.sub(r"\.", "·", s)

    return s


def sizeToBytes(size_str: str) -> int:
    """把文件大小字符串转化为字节数

    Args:
        size_str (str): 文件大小字符串

    Returns:
        int: 字节数
    """

    multipliers = {
        'KB': 1024,
        'MB': 1024**2,
        'GB': 1024**3,
        'TB': 1024**4,
        'PB': 1024**5,
        'EB': 1024**6,
    }
    size_str = size_str.upper()
    number = float(size_str[:-2])
    unit = size_str[-2:]
    if unit in multipliers:
        return int(number * multipliers[unit])
    else:
        logger.error("文件大小转化错误! 不支持的文件大小格式: {size_str}")
    return 0


############################################################


def isCheckSumValid(etag, content) -> tuple[bool, str]:
    """判断MD5是否有效

    Returns:
        tuple[bool, str]: (是否有效, MD5)
    """
    md5 = hashlib.md5(content).hexdigest()
    return etag == md5, md5


############################################################


def openFileOrDir(mainGUI: MainGUI, path: str) -> None:
    """打开指定路径，使用Qt自带的兼容性打开方法

    Args:
        path (str): 文件或文件夹路径
    """
    path = os.path.normpath(path)
    if not os.path.exists(path):
        content = f"目录不存在 - 打开目录失败 - 目录:\n{path}"
        logger.error(content)
        QMessageBox.warning(
            mainGUI,
            "打开文件夹失败",
            content,
        )
    else:
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))


def openFolderAndSelectItems(mainGUI: MainGUI, path: str) -> None:
    """读取一个文件的父目录, 如果可能的话，选择该文件。

        我们可以运行`explorer /select,filename`，
        但这并不支持在选择一个已经打开的目录中的文件时重复使用现有的资源管理器窗口。
        而且也不支持文件路径中包含空格和逗号等等的情况。
    Args:
        path (str): 文件或文件夹路径
    """
    path = os.path.normpath(path)
    try:
        if platform == "win32":
            __inner__openFolderAndSelectItems_windows(path)
        else:
            if os.path.isfile(path):
                path = os.path.dirname(path)
            openFileOrDir(mainGUI, path)
        return
    except ValueError as e:
        content = f"参数错误 - 打开文件夹失败 - 目录:{path}\n{e}"
    except TypeError as e:
        content = f"类型错误 - 打开文件夹失败 - 目录:{path}\n{e}"
    except RuntimeError as e:
        content = f"运行时错误 - 打开文件夹失败 - 目录:{path}\n{e}"
    except SystemError as e:
        content = f"系统错误 - 打开文件夹失败 - 目录:{path}\n{e}"
    except OSError as e:
        content = f"操作系统错误 - 打开文件夹失败 - 目录:{path}\n{e}"
    except AttributeError as e:
        content = f"属性错误 - 打开文件夹失败 - 目录:{path}\n{e}"
    logger.error(content)
    QMessageBox.warning(
        mainGUI,
        "打开文件夹失败",
        content,
    )


def __inner__openFolderAndSelectItems_windows(path):
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


############################################################


def checkNewVersion(mainGUI: MainGUI):
    """检查新版本, 如果有新版本则弹出提示

    Args:
        mainGUI (MainGUI): 主窗口类实例

    """
    url = "https://api.github.com/repos/Zeal-L/BiliBili-Manga-Downloader/releases/latest"

    @retry(stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX)
    def _() -> dict:
        try:
            res = requests.get(url, timeout=TIMEOUT_SMALL)
        except requests.RequestException as e:
            logger.warning(f"获取更新信息失败! 重试中...\n{e}")
            raise e
        if res.status_code != 200:
            logger.warning(
                f"获取更新信息失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中..."
            )
            raise requests.HTTPError()
        return res.json()

    try:
        data = _()
    except requests.RequestException as e:
        logger.error(f"重复更新信息多次后失败!\n{e}")
        logger.exception(e)
        QMessageBox.warning(
            mainGUI,
            "警告",
            "重复获取软件版本更新信息多次后失败!\n请检查网络连接或者重启软件!\n因需要访问github，所以请确认拥有外网访问权限（VPN）\n\n更多详细信息请查看日志文件",
        )
        return

    if data["tag_name"][1:] != __version__:
        message_box = QMessageBox()
        message_box.setWindowTitle("更新小助手")
        message_box.setText(
            f"您当前使用的版本为 v{__version__}，最新版本为 {data['tag_name']} <br> <a href='{data['html_url']}'>请前往 Github 下载最新版本</a>"
        )
        message_box.setTextFormat(Qt.RichText)
        message_box.setIcon(QMessageBox.Information)
        message_box.setWindowIcon(QIcon(":/imgs/BiliBili_favicon.ico"))
        message_box.exec()

    else:
        QMessageBox.information(
            mainGUI, "更新小助手", f"您当前使用的版本为 v{__version__}，已经是最新版本了"
        )


############################################################

DLL_PATH = "./src/assets/easy-taskbar-progress.dll"

TBPF_NOPROGRESS = 0x0  # 没有加载条
TBPF_INDETERMINATE = 0x1  # 正在加载中
TBPF_NORMAL = 0x2  # 正常，显示加载进度
TBPF_ERROR = 0x4  # 错误，显示为红色的加载条
TBPF_PAUSED = 0x8  # 中断，显示为黄色的加载条


class EasyProgressBar:
    def __init__(self, dll_path: str = DLL_PATH) -> None:
        """Windows progress bar."""
        if platform == "win32":
            self._dll = CDLL(dll_path)
        else:
            raise NotImplementedError("Only Windows is supported")
        self._is_init = False

    def init(self) -> int:
        """Initialize the progress bar."""
        ret = self._dll.init()
        self._is_init = True
        return ret

    def init_with_hwnd(self, hwnd: int) -> int:
        """Initialize the progress bar with hwnd."""
        ret = self._dll.init_with_hwnd(c_int(hwnd))
        self._is_init = True
        return ret

    def set_mode(self, mode: int) -> int:
        """Set the progress bar mode."""
        if not self._is_init:
            raise RuntimeError("ProgressBar is not initialized")
        return self._dll.set_mode(c_int(mode))

    def set_progress(self, progress: int, total: int) -> int:
        """Set the progress bar progress and total."""
        if not self._is_init:
            raise RuntimeError("ProgressBar is not initialized")
        return self._dll.set_value(c_int(progress), c_int(total))

    def end(self) -> int:
        """End the progress bar."""
        return self._dll.end()
