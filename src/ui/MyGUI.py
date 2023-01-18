import sys
import json
import os
from PySide6.QtWidgets import QApplication, QPushButton, QSizePolicy, QCheckBox, QWidget, QRadioButton, QGroupBox, QVBoxLayout, QHBoxLayout, QButtonGroup, QFileDialog, QMessageBox
from ui_mainWidget import Ui_MainWidget
from src.utils import *
import logging
from logging import handlers
from MyAbout import MyAbout

class MyGui(QWidget, Ui_MainWidget): 
    
    def __init__(self): 
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("哔哩哔哩漫画下载器 v0.0.1") 
        self.clearUserData = False
        self.aboutWindow = MyAbout()
        
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
        self.label_save_path = None

        ############################################################
        # 初始化
        self.settingUI()

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
