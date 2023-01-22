import json
import logging
import os
import re
import sys
from functools import partial
from logging import handlers

import requests

from PySide6.QtCore import (Q_ARG, QEvent, QMetaObject, QSize, Qt, QThread,
                            QTimer, QUrl, Slot)
from PySide6.QtGui import (QColor, QDesktopServices, QFont, QImage, QPixmap,
                           QStandardItem, QStandardItemModel, QTextCharFormat,
                           QTextCursor)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox,
                               QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                               QLayout, QListView, QListWidget,
                               QListWidgetItem, QMenu, QMessageBox,
                               QPushButton, QRadioButton, QSizePolicy,
                               QVBoxLayout, QWidget)
from ui_mainWidget import Ui_MainWidget

from src.Comic import Comic
from src.searchComic import SearchComic
from src.utils import *
from MangaUI import MangaUI 
from SettingUI import SettingUI
from DownloadUI import DownloadUI


class MainGUI(QWidget, Ui_MainWidget): 
    
    def __init__(self): 
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("哔哩哔哩漫画下载器 v0.0.1") 
        self.setFont(QFont("Microsoft YaHei", 10))
        
        #?###########################################################
        #? 获取应用程序数据目录
        appdata_path = os.getenv("APPDATA")
        self.app_folder = os.path.join(appdata_path, "BiliBili-Manga-Downloader")
        if not os.path.exists(self.app_folder):
            os.mkdir(self.app_folder)
        
        #?###########################################################
        #? 配置日志记录器
        self.logPath = os.path.join(appdata_path, "BiliBili-Manga-Downloader", "logs")
        if not os.path.exists(self.logPath):
            os.mkdir(self.logPath)
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        logHandler = handlers.TimedRotatingFileHandler(os.path.join(self.logPath, "ERROR.log"), when='D', interval=1, backupCount=5, encoding="utf-8")
        
        logHandler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | 模块:%(module)s | 函数:%(funcName)s %(lineno) d行 | %(message)s', 
            datefmt='%Y-%m-%d %H:%M:%S'))
        
        logger.addHandler(logHandler)
        self.logger = logger

        #?###########################################################
        #? 读取配置文件
        self.configPath = os.path.join(self.app_folder, "config.json")
        self.config = None

        #?###########################################################
        #? 初始化UI绑定事件
        self.mangaUI = MangaUI(self)
        self.SettingUI = SettingUI(self)
        self.DownloadUI = DownloadUI(self)


    ############################################################
    # 重写关闭事件，清除用户数据
    ############################################################
    def closeEvent(self, event):
        def _(path):
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isdir(file_path):
                    _(file_path)
                else:
                    os.remove(file_path)
            os.rmdir(path)
        logging.shutdown()
        if self.SettingUI.clearUserData and os.path.exists(self.app_folder):
            _(self.app_folder)
        event.accept()
    
    ############################################################
    # 读取配置文件
    ############################################################
    def getConfig(self, key: str):
        if self.config:
            return self.config.get(key)

        # 检测配置文件是否存在， 不存在则创建
        if not os.path.exists(self.configPath):
            with open(self.configPath, 'w', encoding='utf-8') as f:
                json.dump({}, f)
                return None
        with open(self.configPath, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        return self.config.get(key)

    ############################################################
    # 更新配置文件
    ############################################################
    def updateConfig(self, key: str, value):
        self.config[key] = value
        with open(self.configPath, 'w+', encoding='utf-8') as f:
            # ensure_ascii=False 保证中文不被转义
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        