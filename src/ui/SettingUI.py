import os

from MyAbout import MyAbout
from PySide6.QtWidgets import QFileDialog, QMessageBox

from src.utils import *


class SettingUI(): 
    
    def __init__(self, mainGUI): 
        self.clearUserData = False
        self.init_cookie(mainGUI)
        self.init_savePath(mainGUI)
        self.init_num_thread(mainGUI)
        self.init_openLog(mainGUI)
        self.init_about(mainGUI)
        self.init_clearUserData(mainGUI)
    
    ############################################################
    # 绑定Cookie值
    ############################################################
    def init_cookie(self, mainGUI):
        if mainGUI.getConfig("cookie"):
            mainGUI.lineEdit_my_cookie.setText(mainGUI.getConfig("cookie"))
        def _():
            mainGUI.updateConfig("cookie", mainGUI.lineEdit_my_cookie.text())
            mainGUI.lineEdit_my_cookie.clearFocus()
        mainGUI.lineEdit_my_cookie.returnPressed.connect(_)
        mainGUI.pushButton_my_cookie.clicked.connect(_)
        
    ############################################################
    # 绑定漫画保存路径设置
    ############################################################
    def init_savePath(self, mainGUI):
        if mainGUI.getConfig("save_path"):
            mainGUI.lineEdit_save_path.setText(mainGUI.getConfig("save_path"))
        else:
            mainGUI.lineEdit_save_path.setText(os.getcwd())
            mainGUI.updateConfig("save_path", os.getcwd())
        def _():
            savePath = QFileDialog.getExistingDirectory(mainGUI, "选择保存路径")
            if savePath:
                mainGUI.lineEdit_save_path.setText(savePath)
                mainGUI.updateConfig("save_path", savePath)
        mainGUI.pushButton_save_path.clicked.connect(_)
        def _():
            path = mainGUI.lineEdit_save_path.text()
            if os.path.exists(path):
                mainGUI.updateConfig("save_path", path)
            else:
                mainGUI.lineEdit_save_path.setText(os.getcwd())
            mainGUI.lineEdit_save_path.clearFocus()
        mainGUI.lineEdit_save_path.returnPressed.connect(_)
        
    ############################################################
    # 绑定线程数设置
    ############################################################
    def init_num_thread(self, mainGUI):
        if mainGUI.getConfig("num_thread"):
            mainGUI.h_Slider_num_thread.setValue(mainGUI.getConfig("num_thread"))
        else:
            mainGUI.h_Slider_num_thread.setValue(8)
            mainGUI.updateConfig("num_thread", 8)
        
        mainGUI.label_num_thread_count.setText(f"同时下载线程数：{mainGUI.getConfig('num_thread')}")
        def _(value):
            mainGUI.label_num_thread_count.setText(f"同时下载线程数：{value}")
            mainGUI.updateConfig("num_thread", value)
        mainGUI.h_Slider_num_thread.valueChanged.connect(_)
    
    ############################################################
    # 绑定打开日志文件
    ############################################################
    def init_openLog(self, mainGUI):
        mainGUI.pushButton_open_log.clicked.connect(lambda: os.startfile(os.path.join(mainGUI.logPath, "ERROR.log")))

    ############################################################
    # 绑定关于按钮
    ############################################################
    def init_about(self, mainGUI):
        aboutWindow = MyAbout()
        mainGUI.pushButton_about.clicked.connect(lambda: aboutWindow.show())


    ############################################################
    # 绑定清理用户数据设置
    ############################################################
    def init_clearUserData(self, mainGUI):
        def _():
            res = QMessageBox.information(mainGUI, "提示", "清除所有用户数据，不包括已下载漫画\n只包括Cookie和其他程序缓存文件\n\n注意：清除后将无法恢复\n当前会话不再产生新的配置文件，所有新配置只在当前会话有效", QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.Yes:
                self.clearUserData = True
        mainGUI.pushButton_clear_data.clicked.connect(_)