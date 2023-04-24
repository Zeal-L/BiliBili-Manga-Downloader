import json
import logging
import os
from typing import Any

from src.ui.DownloadUI import DownloadUI
from src.ui.MangaUI import MangaUI
from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import QMessageBox, QWidget
from src.ui.SettingUI import SettingUI
from src.ui.PySide_src.mainWidget_ui import Ui_MainWidget

from src.utils import logger, __version__, check_new_version


class MainGUI(QWidget, Ui_MainWidget):
    """主窗口类，用于管理所有UI"""

    # ? 主要是为了 Episode 类里面的提示框准备的，
    # ? 因为 Episode 类是在另一个线程里面运行的，而只有主线程才能修改 GUI
    message_box = Signal(str)
    # ? 用于多线程更新我的库存
    my_library_add_widget = Signal(dict)

    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.setWindowTitle(f"哔哩哔哩漫画下载器 v{__version__}")
        self.setFont(QFont("Microsoft YaHei", 10))
        self.message_box.connect(lambda msg: QMessageBox.warning(None, "警告", msg))

        logger.info("\n\n\t\t\t------------------- 程序启动，初始化主窗口 -------------------\n")

        # ?###########################################################
        # ? 获取应用程序数据目录
        appdata_path = os.getenv("APPDATA")
        self.app_folder = os.path.join(appdata_path, "BiliBili-Manga-Downloader")
        if not os.path.exists(self.app_folder):
            os.mkdir(self.app_folder)

        # ?###########################################################
        # ? 读取配置文件，以及初始化 save_path
        self.config_path = os.path.join(self.app_folder, "config.json")
        self.config = {}

        if self.getConfig("save_path"):
            self.lineEdit_save_path.setText(self.getConfig("save_path"))
        else:
            self.lineEdit_save_path.setText(os.getcwd())
            self.updateConfig("save_path", os.getcwd())

        # ?###########################################################
        # ? 初始化UI绑定事件
        self.mangaUI = MangaUI(self)
        self.settingUI = SettingUI(self)
        self.downloadUI = DownloadUI(self)

        # ? 检查新版本
        check_new_version(self)

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

        if self.settingUI.clearUserData:
            try:
                _(self.app_folder)
            except OSError as e:
                logger.error(f"清除用户数据失败 - 目录:{self.app_folder}\n{e}")

        logger.info("\n\n\t\t\t-------------------  程序正常退出 -------------------\n")
        logging.shutdown()
        event.accept()

    ############################################################
    def getConfig(self, key: str) -> Any:
        """读取用户配置文件

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
