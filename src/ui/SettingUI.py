from __future__ import annotations

import os
from functools import partial
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFileDialog, QMessageBox, QRadioButton

from src.ui.MyAbout import MyAbout
from src.utils import log_path

if TYPE_CHECKING:
    from src.ui.MainGUI import MainGUI


class SettingUI():
    """设置窗口类，用于管理设置UI
    """
    def __init__(self, mainGUI: MainGUI):
        self.clearUserData = False
        self.init_cookie(mainGUI)
        self.init_savePath(mainGUI)
        self.init_num_thread(mainGUI)
        self.init_openLog(mainGUI)
        self.init_about(mainGUI)
        self.init_clearUserData(mainGUI)
        self.init_saveMethod(mainGUI)

    ############################################################
    def init_cookie(self, mainGUI: MainGUI) -> None:
        """绑定Cookie值

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        if mainGUI.getConfig("cookie"):
            mainGUI.lineEdit_my_cookie.setText(mainGUI.getConfig("cookie"))
        def _():
            mainGUI.updateConfig("cookie", mainGUI.lineEdit_my_cookie.text())
            mainGUI.lineEdit_my_cookie.clearFocus()
        mainGUI.lineEdit_my_cookie.returnPressed.connect(_)
        mainGUI.pushButton_my_cookie.clicked.connect(_)

    ############################################################
    def init_savePath(self, mainGUI: MainGUI) -> None:
        """绑定漫画保存路径设置

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """

        def _():
            save_path = QFileDialog.getExistingDirectory(mainGUI, "选择保存路径")
            if save_path:
                mainGUI.lineEdit_save_path.setText(save_path)
                mainGUI.updateConfig("save_path", save_path)
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
    def init_num_thread(self, mainGUI: MainGUI) -> None:
        """绑定线程数设置

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """

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
    def init_openLog(self, mainGUI: MainGUI) -> None:
        """绑定打开日志文件

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        mainGUI.pushButton_open_log.clicked.connect(lambda: os.startfile(os.path.join(log_path, "ERROR.log")))

    ############################################################
    def init_about(self, mainGUI: MainGUI) -> None:
        """绑定关于按钮

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        about_window = MyAbout()
        mainGUI.pushButton_about.clicked.connect(partial(about_window.show))

    ############################################################
    def init_clearUserData(self, mainGUI: MainGUI) -> None:
        """绑定清理用户数据设置

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        def _():
            res = QMessageBox.information(mainGUI, "提示", "清除所有用户数据，不包括已下载漫画\n只包括Cookie和其他程序缓存文件\n\n注意：清除后将无法恢复\n当前会话不再产生新的配置文件，所有新配置只在当前会话有效", QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.Yes:
                self.clearUserData = True

        mainGUI.pushButton_clear_data.clicked.connect(_)

    ############################################################
    def init_saveMethod(self, mainGUI: MainGUI) -> None:
        """绑定保存方式设置

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        if mainGUI.getConfig("save_method"):
            for i in range(mainGUI.h_Layout_groupBox_save_method.count()):
                button: QRadioButton = mainGUI.h_Layout_groupBox_save_method.itemAt(i).widget()
                if button.text() == mainGUI.getConfig("save_method"):
                    button.setChecked(True)

        def _(button: QRadioButton, checked: bool) -> None:
            if checked:
                mainGUI.updateConfig("save_method", button.text())

        for i in range(mainGUI.h_Layout_groupBox_save_method.count()):
            button: QRadioButton = mainGUI.h_Layout_groupBox_save_method.itemAt(i).widget()
            button.toggled.connect(partial(_, button))