"""
该模块包含了主窗口类，用于管理所有子UI
"""

import json
import logging
import os
from functools import partial
from sys import platform
from typing import Any, Optional

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QCloseEvent, QFont, QKeyEvent
from PySide6.QtWidgets import QMainWindow, QMessageBox
from qt_material import QtStyleTools

from src.ui.DownloadUI import DownloadUI
from src.ui.MangaUI import MangaUI

if platform == "darwin":
    from src.ui.PySide_src.mainWindow_mac_ui import Ui_MainWindow
else:
    from src.ui.PySide_src.mainWindow_ui import Ui_MainWindow
from src.ui.SettingUI import SettingUI
from src.Utils import __version__, data_path, logger


class MainGUI(QMainWindow, Ui_MainWindow, QtStyleTools):
    """主窗口类，用于管理所有UI"""

    # ? 主要是为了 Episode 类里面的提示框准备的，
    # ? 因为 Episode 类是在另一个线程里面运行的，而只有主线程才能修改 GUI
    signal_message_box = Signal(str)
    signal_information_box = Signal(str)

    # ? 用于多线程报告程序详情
    signal_resolve_status = Signal(str)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setupUi(self)
        self.setWindowTitle(f"哔哩哔哩漫画下载器 v{__version__}")
        if platform == "darwin":
            self.setFont(QFont("PingFang SC", 12))
        else:
            self.setFont(QFont("Microsoft YaHei", 10))
        self.signal_message_box.connect(lambda msg: QMessageBox.warning(self, "警告", msg))
        self.signal_information_box.connect(lambda msg: QMessageBox.information(self, "通知", msg))
        self.signal_resolve_status.connect(partial(self.label_resolve_status.setText))

        # ?###########################################################
        # ? 初始化功能键状态
        self.CtrlPress = False
        self.AltPress = False
        self.ShiftPress = False
        self.isFocus = True

        # ?###########################################################
        # ? 初始化事件过滤器
        self.mainEventFilter = self.initEventFilter()
        self.app.installEventFilter(self.mainEventFilter)

        logger.info("\n\n\t\t\t------------------- 程序启动，初始化主窗口 -------------------\n")

        # ?###########################################################
        # ? 读取配置文件，以及初始化 save_path
        self.config_path = os.path.join(data_path, "config.json")
        self.config = {}

        if self.getConfig("save_path"):
            self.lineEdit_save_path.setText(self.getConfig("save_path"))
        else:
            self.lineEdit_save_path.setText(os.getcwd())
            self.updateConfig("save_path", os.getcwd())
        logger.info(f"save_method: {self.getConfig('save_method')}")

        # ?###########################################################
        # ? 初始化 my_library，方便读取本地漫画元数据
        self.my_library = {}

        # ?###########################################################
        # ? 初始化UI绑定事件
        self.settingUI = SettingUI(self)
        self.mangaUI = MangaUI(self)
        self.downloadUI = DownloadUI(self)

    ############################################################
    def closeEvent(self, event: QCloseEvent) -> None:
        """重写关闭事件，清除用户数据

        Args:
            event (QCloseEvent): 关闭事件
        """

        def _(path: str) -> None:
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isdir(file_path):
                    _(file_path)
                else:
                    os.remove(file_path)
            os.rmdir(path)

        if self.settingUI.clear_user_data:
            try:
                _(data_path)
            except OSError as e:
                logger.error(f"清除用户数据失败 - 目录:{data_path}\n{e}")

        logger.info("\n\n\t\t\t-------------------  程序正常退出 -------------------\n")

        self.downloadUI.downloadManager.terminated = True
        self.downloadUI.downloadManager.executor.shutdown(wait=False, cancel_futures=True)
        self.mangaUI.executor.shutdown(wait=False, cancel_futures=True)
        logging.shutdown()
        event.accept()

    ############################################################
    def initEventFilter(self) -> QObject:
        """初始化主事件过滤器
        当前主事件过滤器主要是对QEvent.ApplicationDeactivate与QEvent.ApplicationActivate
        即焦点的失去与获得进行处理

        Returns:
            mainEventFilter (QObject): 主窗口事件过滤器
        """

        class MainEventFilter(QObject):
            """用于过滤主窗口事件的类

            Args:
                outer_self (MainGUI): 外部类的实例
                parent (Optional[QObject], optional): 父对象。默认为 None
            """

            def __init__(self, outer_self: MainGUI, parent: Optional[QObject] = None) -> None:
                self.outer_self = outer_self
                super().__init__(parent)

            def eventFilter(self, *args, **kwargs) -> bool:
                """重写事件过滤器函数

                Args:
                    *args: 位置参数
                    **kwargs: 关键字参数

                Returns:
                    bool: 是否过滤该事件
                """
                try:
                    event: QEvent = args[1]
                    if event.type() == QEvent.ApplicationDeactivate:
                        self.outer_self.isFocus = False
                        self.outer_self.CtrlPress = (
                            self.outer_self.AltPress
                        ) = self.outer_self.ShiftPress = False
                    elif event.type() == QEvent.ApplicationActivate:
                        self.outer_self.isFocus = True
                    return super().eventFilter(*args, **kwargs)
                except Exception as e:
                    logger.error(f"主窗口事件过滤器出错！\n{e}")
                    return False

        return MainEventFilter(outer_self=self)

    ############################################################
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """覆写QMainWindow的keyPressEvent方法

        Args:
            event (QKeyEvent): 事件类

        Returns:
            None
        """
        if event.key() == Qt.Key.Key_Control:
            self.CtrlPress = True
        elif event.key() in [Qt.Key.Key_Alt, Qt.Key.Key_Option]:
            self.AltPress = True
        elif event.key() == Qt.Key.Key_Shift:
            self.ShiftPress = True
        return super().keyPressEvent(event)

    ############################################################
    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """覆写QMainWindow的keyReleaseEvent方法

        Args:
            event (QKeyEvent): 事件类

        Returns:
            None
        """
        if event.key() == Qt.Key.Key_Control:
            self.CtrlPress = False
        if event.key() in [Qt.Key.Key_Alt, Qt.Key.Key_Option]:
            self.AltPress = False
        elif event.key() == Qt.Key.Key_Shift:
            self.ShiftPress = False
        return super().keyReleaseEvent(event)

    ############################################################
    def getConfig(self, key: str) -> Any:
        """读取用户配置文件, 如果key不存在则创建空值

        Args:
            key (str): 配置项

        Returns:
            Any: 配置项的值
        """
        if self.config:
            return self.config.get(key)

        # ?###########################################################
        # ? 检测配置文件是否存在， 不存在则创建
        if not os.path.exists(self.config_path):
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump({}, f)
                    return None
            except OSError as e:
                logger.error(f"创建配置文件失败: 目录:{self.config_path}\n{e}")
                return None

        # ?###########################################################
        # ? 读取配置文件
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except OSError as e:
            logger.error(f"读取配置文件失败 - 目录:{self.config_path}\n{e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"解析配置文件失败 - 目录:{self.config_path}\n{e}")
            QMessageBox.warning(
                None,
                "警告",
                "配置文件发生异常损毁，解析失败!\n" "更多详细信息请查看日志文件, 或联系开发者！",
            )
            return None
        return self.config.get(key)

    ############################################################
    def updateConfig(self, key: str, value: Any) -> None:
        """更新用户配置文件

        Args:
            key (str): 配置项
            value (Any): 配置项的值
        """
        self.config[key] = value

        try:
            with open(self.config_path, "w+", encoding="utf-8") as f:
                # ensure_ascii=False 保证中文不被转义
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except OSError as e:
            logger.error(
                f"更新配置文件失败 - 目录:{self.config_path} - key: {key} - value: {value}\n{e}"
            )
