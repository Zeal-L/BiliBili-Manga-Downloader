import sys
import json
import os
from PySide6.QtWidgets import QApplication, QPushButton, QSizePolicy, QCheckBox, QWidget, QRadioButton, QGroupBox, QVBoxLayout, QHBoxLayout, QButtonGroup, QFileDialog
from ui_mainWidget import Ui_MainWidget
from src.utils import *

class MyGui(QWidget, Ui_MainWidget): 
    def __init__(self): 
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("哔哩哔哩漫画下载器 v0.0.1") 

        # 读取配置文件
        appdata_path = os.getenv("APPDATA")
        self.app_folder = os.path.join(appdata_path, "BiliBili-Manga-Downloader")
        if not os.path.exists(self.app_folder):
            os.mkdir(self.app_folder)
        self.configPath = os.path.join(self.app_folder, "config.json")
        self.config = None
        self.label_save_path = None

        self.settingUI()
        
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
        # 只会在用户清除数据后触发，不再产生新的配置文件，所有新配置只在当前会话有效
        if not os.path.exists(self.configPath):
            return
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
        def __(path):
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isdir(file_path):
                    __(file_path)
                else:
                    os.remove(file_path)
            os.rmdir(path)
        def _():
            if os.path.exists(self.app_folder):
                __(self.app_folder)
        self.pushButton_clear_data.clicked.connect(_)
        self.pushButton_clear_data.setToolTip("清除所有用户数据，不包括已下载漫画\n只包括Cookie和下载路径和其他程序缓存文件\n注意：清除后将无法恢复\n当前会话不再产生新的配置文件，所有新配置只在当前会话有效")

