import json
import logging
import os
import re
import sys
from logging import handlers

import requests

from MyAbout import MyAbout
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import (QStandardItem, QStandardItemModel, QTextCharFormat,
                           QTextCursor, QFont, QPixmap, QImage)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox,
                               QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                               QListView, QListWidget, QListWidgetItem,
                               QMessageBox, QPushButton, QRadioButton,
                               QSizePolicy, QVBoxLayout, QWidget, QLayout)
from ui_mainWidget import Ui_MainWidget
from src.Comic import Comic
from src.searchComic import SearchComic
from src.utils import *


class MyGui(QWidget, Ui_MainWidget): 
    
    def __init__(self): 
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("哔哩哔哩漫画下载器 v0.0.1") 
        self.clearUserData = False
        self.aboutWindow = MyAbout()
        
        # 改变窗口内所有文字的大小
        self.setFont(QFont("Microsoft YaHei", 10))
        
        
        ############################################################
        # 获取应用程序数据目录
        appdata_path = os.getenv("APPDATA")
        self.app_folder = os.path.join(appdata_path, "BiliBili-Manga-Downloader")
        if not os.path.exists(self.app_folder):
            os.mkdir(self.app_folder)
        
        ############################################################
        # 配置日志记录器
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

        ############################################################
        # 读取配置文件
        self.configPath = os.path.join(self.app_folder, "config.json")
        self.config = None

        ############################################################
        # 初始化UI绑定事件
        self.settingUI()
        self.mangaUI()
        
        
    def mangaUI(self):
        ############################################################
        # 链接搜索漫画功能
        def _():
            if not self.getConfig("cookie"):
                QMessageBox.critical(self, "Critical",  "请先在设置界面填写自己的Cookie！")
                return
                
            self.searchInfo = SearchComic(self.logger, self.lineEdit_manga_search_name.text(), self.getConfig("cookie")).getResults()['data']['list']
            self.listWidget_manga_search.clear()
            self.label_manga_search.setText(f"找到：{len(self.searchInfo)}条结果")
            for item in self.searchInfo:
                # 替换爬取信息里的html标签
                item['title'] = re.sub(r'</[^>]+>', '</span>', item['title'])
                item['title'] = re.sub(r'<[^/>]+>', '<span style="color:red;font-weight:bold">', item['title'])
                temp = QListWidgetItem()
                self.listWidget_manga_search.addItem(temp)
                self.listWidget_manga_search.setItemWidget(temp, QLabel(f"{item['title']} by <span style='color:blue'>{item['author_name'][0]}</span>"))
        self.lineEdit_manga_search_name.returnPressed.connect(_)
        self.pushButton_manga_search_name.clicked.connect(_)
        
        ############################################################
        # 绑定双击显示漫画详情事件
        def _(item):
            index = self.listWidget_manga_search.indexFromItem(item).row()
            comic = Comic(self.logger, self.searchInfo[index]['id'], self.getConfig("cookie"), self.getConfig("save_path"), self.getConfig("num_thread"))
            data = comic.getComicInfo()
            self.label_manga_title.setText("<span style='color:blue;font-weight:bold'>标题：</span>" + data['title'])
            self.label_manga_author.setText("<span style='color:blue;font-weight:bold'>作者：</span>" + data['author_name'])
            self.label_manga_style.setText("<span style='color:blue;font-weight:bold'>标签：</span>" + data['styles'] if data['styles'] else "标签：无")
            self.label_manga_outline.setText("<span style='color:blue;font-weight:bold'>概要：</span>" + data['evaluate'] if data['evaluate'] else "概要：无")
            self.labelImg = QPixmap.fromImage(QImage.fromData(requests.get(data['vertical_cover']).content))
            
            ############################################################
            # 重写图片大小改变事件，使图片不会变形
            def __(event=None):
                newSize = event.size() if event else self.label_manga_image.size()
                if newSize.width() < 200:
                    newSize.setWidth(200)
                img = self.labelImg.scaled(newSize, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.label_manga_image.setPixmap(img)
                self.label_manga_image.setAlignment(Qt.AlignTop)
            self.label_manga_image.resizeEvent = __
            __()

        self.listWidget_manga_search.itemDoubleClicked.connect(_)
        
        

    ############################################################
    # 重写关闭事件，清除用户数据
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
        if self.clearUserData and os.path.exists(self.app_folder):
            _(self.app_folder)
        event.accept()
    
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

    def updateConfig(self, key: str, value):
        self.config[key] = value
        with open(self.configPath, 'w+', encoding='utf-8') as f:
            # ensure_ascii=False 保证中文不被转义
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        
    def settingUI(self):
        ############################################################
        # 绑定Cookie值
        if self.getConfig("cookie"):
            self.lineEdit_my_cookie.setText(self.getConfig("cookie"))
        def _():
            self.updateConfig("cookie", self.lineEdit_my_cookie.text())
            self.lineEdit_my_cookie.clearFocus()
        self.lineEdit_my_cookie.returnPressed.connect(_)
        self.pushButton_my_cookie.clicked.connect(_)
        
        ############################################################
        # 绑定漫画保存路径设置
        if self.getConfig("save_path"):
            self.lineEdit_save_path.setText(self.getConfig("save_path"))
        else:
            self.lineEdit_save_path.setText(os.getcwd())
            self.updateConfig("save_path", os.getcwd())
        def _():
            savePath = QFileDialog.getExistingDirectory(self, "选择保存路径")
            self.lineEdit_save_path.setText(savePath)
            self.updateConfig("save_path", savePath)
        self.pushButton_save_path.clicked.connect(_)
        def _():
            path = self.lineEdit_save_path.text()
            if os.path.exists(path):
                self.updateConfig("save_path", path)
            else:
                self.lineEdit_save_path.setText(os.getcwd())
            self.lineEdit_save_path.clearFocus()
        self.lineEdit_save_path.returnPressed.connect(_)
        
        ############################################################
        # 绑定线程数设置
        if self.getConfig("num_thread"):
            self.h_Slider_num_thread.setValue(self.getConfig("num_thread"))
        else:
            self.h_Slider_num_thread.setValue(8)
            self.updateConfig("num_thread", 8)
        
        self.label_num_thread_count.setText(f"同时下载线程数：{self.getConfig('num_thread')}")
        def _(value):
            self.label_num_thread_count.setText(f"同时下载线程数：{value}")
            self.updateConfig("num_thread", value)
        self.h_Slider_num_thread.valueChanged.connect(_)
        
        ############################################################
        # 绑定清理用户数据设置
        def _():
            res = QMessageBox.information(self, "提示", "清除所有用户数据，不包括已下载漫画\n只包括Cookie和其他程序缓存文件\n\n注意：清除后将无法恢复\n当前会话不再产生新的配置文件，所有新配置只在当前会话有效", QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.Yes:
                self.clearUserData = True
        self.pushButton_clear_data.clicked.connect(_)
        
        ############################################################
        # 绑定打开日志文件, 在新窗口用rich库打印日志
        self.pushButton_open_log.clicked.connect(lambda: os.startfile(os.path.join(self.logPath, "ERROR.log")))

        ############################################################
        # 绑定关于按钮
        self.pushButton_about.clicked.connect(lambda: self.aboutWindow.show())
