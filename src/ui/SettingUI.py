"""
该模块包含SettingUI类，它管理BiliBili Manga Downloader应用程序的设置UI。它允许用户设置 BiliBili 登录 cookie、下载路径、线程数和其他设置
"""

from __future__ import annotations

import os
import threading
from functools import partial
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, quote, urlparse

import requests
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QFileDialog, QMessageBox, QRadioButton
from retrying import retry

from src.BiliQrCode import QrCode
from src.ui.MyAboutUI import MyAboutUI
from src.ui.QrCodeUI import QrCodeUI
from src.Utils import (
    MAX_RETRY_SMALL,
    RETRY_WAIT_EX,
    TIMEOUT_SMALL,
    checkNewVersion,
    openFileOrDir,
    log_path,
    logger,
)

if TYPE_CHECKING:
    from src.ui.MainGUI import MainGUI


class SettingUI(QObject):
    """设置窗口类，用于管理设置UI"""

    # ? 用于多线程更新我的库存
    signal_qr_res = Signal(dict)

    def __init__(self, mainGUI: MainGUI):
        super().__init__()
        self.mainGUI = mainGUI
        self.clear_user_data = False
        self.init_qrCode(mainGUI)
        self.init_cookie(mainGUI)
        self.init_biliplus_cookie(mainGUI)
        self.init_savePath(mainGUI)
        self.init_num_thread(mainGUI)
        self.init_openLog(mainGUI)
        self.init_about(mainGUI)
        self.init_clearUserData(mainGUI)
        self.init_saveMethod(mainGUI)
        self.init_checkUpdate(mainGUI)
        self.init_theme(mainGUI)
        self.qr_ui = QrCodeUI()

    ############################################################
    def qrCodeCallBack(self, data: dict) -> None:
        """二维码回调函数

        Args:
            data (dict): 二维码数据
        """
        # sourcery skip: extract-method

        if data is None:
            self.qr_ui.close()
            return

        # 0：扫码登录成功
        if data["code"] == 0:
            self.qr_ui.close()

            parsed_url = urlparse(data["url"])
            query_params = parse_qs(parsed_url.query)
            sessdata = quote(query_params["SESSDATA"][0])

            self.mainGUI.updateConfig("cookie", sessdata)
            self.mainGUI.lineEdit_my_cookie.setText(sessdata)
            self.qr_ui.label.setText("## 请使用BiliBili手机客户端扫描二维码登入")

            QMessageBox.information(
                self.mainGUI,
                "提示",
                f"扫码登录成功！\n新Cookie为: {sessdata}\n已自动保存！",
            )

        # 86038：二维码已失效
        elif data["code"] == 86038:
            self.qr_ui.close()
            QMessageBox.warning(self.mainGUI, "警告", "二维码已超时失效！请重新获取二维码！")

        # 86090：二维码已扫码未确认
        elif data["code"] == 86090:
            self.qr_ui.label.setText("## 扫码成功！请在手机上确认登录！")

    ############################################################
    def init_qrCode(self, mainGUI: MainGUI) -> None:
        """绑定二维码按钮

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """

        def _():
            qr = QrCode(mainGUI)
            img = qr.generate()
            if img is None:
                return

            self.qr_ui.label_img.setPixmap(
                QPixmap.fromImage(QImage.fromData(img)).scaled(400, 400)
            )
            self.qr_ui.show()

            # 开一个线程去检测二维码是否扫描成功
            thread = threading.Thread(
                target=qr.get_cookie,
                args=(self.signal_qr_res,),
            )
            thread.start()

            # 如果用户把二维码窗口关了，就把线程也关了
            self.qr_ui.closeEvent = lambda _: setattr(qr, "close_flag", True)

        self.signal_qr_res.connect(self.qrCodeCallBack)
        mainGUI.pushButton_qrcode.clicked.connect(partial(_))

    ############################################################
    def init_cookie(self, mainGUI: MainGUI) -> None:
        """绑定Cookie值

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        stored_cookie = mainGUI.getConfig("cookie")
        if stored_cookie:
            mainGUI.lineEdit_my_cookie.setText(stored_cookie)
            self.is_cookie_valid(mainGUI, stored_cookie)

        def _():
            new_cookie = mainGUI.lineEdit_my_cookie.text()
            if new_cookie == "":
                QMessageBox.information(mainGUI, "提示", "请输入Cookie！")
                return
            mainGUI.updateConfig("cookie", new_cookie)
            mainGUI.lineEdit_my_cookie.clearFocus()
            if self.is_cookie_valid(mainGUI, new_cookie):
                QMessageBox.information(mainGUI, "提示", "Cookie有效！")

        mainGUI.lineEdit_my_cookie.returnPressed.connect(_)
        mainGUI.pushButton_my_cookie.clicked.connect(_)

    ############################################################
    def is_cookie_valid(self, mainGUI: MainGUI, cookie: str) -> bool:
        """判断Cookie是否有效

        Args:
            mainGUI (MainGUI): 主窗口类实例
            cookie (str): Cookie值
        Returns:
            bool: Cookie是否有效
        """
        detail_url = "https://manga.bilibili.com/twirp/comic.v1.Comic/Search?device=pc&platform=web"
        headers = {
            "cookie": f"SESSDATA={cookie}",
        }
        payload = {"key_word": "test", "page_num": 1, "page_size": 1}

        @retry(
            stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX
        )
        def _() -> None:
            try:
                res = requests.post(
                    detail_url, data=payload, headers=headers, timeout=TIMEOUT_SMALL
                )
            except requests.RequestException as e:
                logger.warning(f"测试Cookie是否有效失败! 重试中...\n{e}")
                raise e
            if res.status_code != 200:
                logger.warning(
                    f"测试Cookie是否有效失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中..."
                )
                raise requests.HTTPError()

        try:
            _()
        except requests.RequestException as e:
            logger.error(f"重复测试Cookie是否有效多次后失败!\n{e}")
            logger.exception(e)
            QMessageBox.warning(
                mainGUI,
                "警告",
                "重复测试Cookie是否有效多次后失败!\n请核对输入的Cookie值或者检查网络连接!\n\n更多详细信息请查看日志文件",
            )
            return False
        return True

    ############################################################
    def init_biliplus_cookie(self, mainGUI: MainGUI) -> None:
        """绑定BiliPlus Cookie值

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        stored_cookie = mainGUI.getConfig("biliplus_cookie")
        if stored_cookie:
            mainGUI.lineEdit_biliplus_cookie.setText(stored_cookie)
            self.is_biliplus_cookie_valid(mainGUI, stored_cookie)

        def _():
            new_cookie = mainGUI.lineEdit_biliplus_cookie.text()
            if new_cookie == "":
                QMessageBox.information(mainGUI, "提示", "请输入Cookie！")
                return
            mainGUI.updateConfig("biliplus_cookie", new_cookie)
            mainGUI.lineEdit_biliplus_cookie.clearFocus()
            if self.is_biliplus_cookie_valid(mainGUI, new_cookie):
                QMessageBox.information(mainGUI, "提示", "Cookie有效！")

        mainGUI.lineEdit_biliplus_cookie.returnPressed.connect(_)
        mainGUI.pushButton_biliplus_cookie.clicked.connect(_)

    ############################################################
    def is_biliplus_cookie_valid(self, mainGUI: MainGUI, cookie: str) -> bool:
        """判断BiliPlus Cookie是否有效

        Args:
            mainGUI (MainGUI): 主窗口类实例
            cookie (str): Cookie值
        Returns:
            bool: Cookie是否有效
        """
        # 此处对Cookie是否有效验证使用了硬编码，如果该漫画或该章节变更，需要修改才能继续正常验证
        main_url = "https://www.biliplus.com/manga/?act=read&mangaid=26551&epid=316882"
        headers = {
            "cookie": f"login=2;access_key={cookie}",
        }

        @retry(
            stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX
        )
        def _() -> None:
            try:
                res = requests.post(main_url, headers=headers, timeout=TIMEOUT_SMALL)
            except requests.RequestException as e:
                logger.warning(f"测试BiliPlus Cookie是否有效失败! 重试中...\n{e}")
                raise e
            if res.status_code != 200:
                logger.warning(
                    f"测试BiliPlus Cookie是否有效失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中..."
                )
                raise requests.HTTPError()
            if "hoz-container" not in res.text:
                logger.warning("BiliPlus Cookie检测出现故障，暂时无法检测是否有效...")
                raise ReferenceError
            if 'class="comic-single"' not in res.text or 'src="http' not in res.text:
                logger.warning("BiliPlus Cookie无效!重试中...")
                raise requests.HTTPError()

        try:
            _()
        except requests.RequestException as e:
            logger.error(f"重复测试Cookie是否有效多次后失败!\n{e}")
            logger.exception(e)
            QMessageBox.warning(
                mainGUI,
                "警告",
                "重复测试biliplus Cookie是否有效多次后失败!\n请核对输入的biliplus Cookie值或者检查网络连接!\n\n更多详细信息请查看日志文件",
            )
            return False
        except ReferenceError:
            QMessageBox.warning(
                mainGUI, "警告", "BiliPlus Cookie检测功能出现故障!\n暂时无法检测是否有效!\n请自行判断或联系开发者"
            )
            return False
        return True

    ############################################################
    def init_savePath(self, mainGUI: MainGUI) -> None:
        """绑定漫画保存路径设置

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """

        def _():
            path = QFileDialog.getExistingDirectory(mainGUI, "选择保存路径")
            if os.path.exists(path):
                mainGUI.lineEdit_save_path.setText(path)
                mainGUI.updateConfig("save_path", path)
            else:
                mainGUI.lineEdit_save_path.setText(os.getcwd())
                mainGUI.updateConfig("save_path", os.getcwd())

        mainGUI.pushButton_save_path.clicked.connect(_)

        def _():
            path = mainGUI.lineEdit_save_path.text()
            if os.path.exists(path):
                mainGUI.updateConfig("save_path", path)
            else:
                mainGUI.lineEdit_save_path.setText(os.getcwd())
                mainGUI.updateConfig("save_path", os.getcwd())
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
            mainGUI.updateConfig("num_thread", mainGUI.h_Slider_num_thread.value())

        mainGUI.label_num_thread_count.setText(
            f"同时下载线程数：{mainGUI.getConfig('num_thread')}"
        )

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
        mainGUI.pushButton_open_log.clicked.connect(
            lambda: openFileOrDir(os.path.join(log_path, 'ERROR.log'))
        )

    ############################################################
    def init_about(self, mainGUI: MainGUI) -> None:
        """绑定关于按钮

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        about_window = MyAboutUI()
        mainGUI.pushButton_about.clicked.connect(partial(about_window.show))

    ############################################################
    def init_clearUserData(self, mainGUI: MainGUI) -> None:
        """绑定清理用户数据设置

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """

        def _():
            res = QMessageBox.information(
                mainGUI,
                "提示",
                "清除所有用户数据，不包括已下载漫画\n只包括Cookie和其他程序缓存文件\n\n注意：清除后将无法恢复\n当前会话不再产生新的配置文件，所有新配置只在当前会话有效",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res == QMessageBox.Yes:
                self.clear_user_data = True

        mainGUI.pushButton_clear_data.clicked.connect(_)

    ############################################################
    def init_saveMethod(self, mainGUI: MainGUI) -> None:
        """绑定保存方式设置

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        if mainGUI.getConfig("save_method"):
            for i in range(mainGUI.h_Layout_groupBox_save_method.count()):
                button: QRadioButton = mainGUI.h_Layout_groupBox_save_method.itemAt(
                    i
                ).widget()
                if button.text() == mainGUI.getConfig("save_method"):
                    button.setChecked(True)
        else:
            for i in range(mainGUI.h_Layout_groupBox_save_method.count()):
                button: QRadioButton = mainGUI.h_Layout_groupBox_save_method.itemAt(
                    i
                ).widget()
                if button.isChecked():
                    mainGUI.updateConfig("save_method", button.text())
                    break

        def _(button: QRadioButton, checked: bool) -> None:
            if checked:
                mainGUI.updateConfig("save_method", button.text())

        for i in range(mainGUI.h_Layout_groupBox_save_method.count()):
            button: QRadioButton = mainGUI.h_Layout_groupBox_save_method.itemAt(
                i
            ).widget()
            button.toggled.connect(partial(_, button))

    ############################################################

    def init_checkUpdate(self, mainGUI: MainGUI) -> None:
        """绑定检查更新按钮

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        mainGUI.pushButton_check_update.clicked.connect(
            partial(checkNewVersion, mainGUI)
        )

    ############################################################

    def init_theme(self, mainGUI: MainGUI) -> None:
        """绑定主题相关设置

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        # ? 绑定主题样式设置
        theme_style = mainGUI.getConfig("theme_style")
        if theme_style is None:
            mainGUI.updateConfig("theme_style", "default")
            theme_style = "default"

        styles_list = {
            "default": "默认",
            "dark_amber.xml": "深色-琥珀",
            "dark_blue.xml": "深色-蓝色",
            "dark_cyan.xml": "深色-青色",
            "dark_lightgreen.xml": "深色-浅绿",
            "dark_pink.xml": "深色-粉色",
            "dark_purple.xml": "深色-紫色",
            "dark_red.xml": "深色-红色",
            "dark_teal.xml": "深色-靛青",
            "dark_yellow.xml": "深色-黄色",
            "light_amber.xml": "浅色-琥珀",
            "light_blue.xml": "浅色-蓝色",
            "light_cyan.xml": "浅色-青色",
            "light_cyan_500.xml": "浅色-青色500",
            "light_lightgreen.xml": "浅色-浅绿",
            "light_pink.xml": "浅色-粉色",
            "light_purple.xml": "浅色-紫色",
            "light_red.xml": "浅色-红色",
            "light_teal.xml": "浅色-靛青",
            "light_yellow.xml": "浅色-黄色",
        }

        reversed_styles_list = {value: key for key, value in styles_list.items()}
        mainGUI.comboBox_theme_style.addItems(styles_list.values())
        mainGUI.comboBox_theme_style.setCurrentText(styles_list[theme_style])

        def _(text: str) -> None:
            mainGUI.updateConfig("theme_style", reversed_styles_list[text])
            mainGUI.apply_stylesheet(
                mainGUI,
                reversed_styles_list[text],
                extra={
                    "density_scale": f"{mainGUI.getConfig('theme_density')}",
                },
            )

            if text == "默认":
                mainGUI.comboBox_theme_density.setEnabled(False)
            else:
                mainGUI.comboBox_theme_density.setEnabled(True)

        mainGUI.comboBox_theme_style.currentTextChanged.connect(_)

        # ? 绑定主题密度设置
        theme_density = mainGUI.getConfig("theme_density")
        if theme_density is None:
            mainGUI.updateConfig("theme_density", 0)
            theme_density = 0

        mainGUI.comboBox_theme_density.addItems(["-2", "-1", "0", "1", "2"])
        mainGUI.comboBox_theme_density.setCurrentText(str(theme_density))

        def _(text: str) -> None:
            mainGUI.updateConfig("theme_density", int(text))
            mainGUI.apply_stylesheet(
                mainGUI,
                mainGUI.getConfig("theme_style"),
                extra={
                    "density_scale": f"{int(text)}",
                },
            )

        mainGUI.comboBox_theme_density.currentTextChanged.connect(_)

        # ? 初始化主题样式+密度
        mainGUI.apply_stylesheet(
            mainGUI,
            mainGUI.getConfig("theme_style"),
            extra={
                "density_scale": f"{mainGUI.getConfig('theme_density')}",
            },
        )

        if mainGUI.comboBox_theme_style.currentText() == "默认":
            mainGUI.comboBox_theme_density.setEnabled(False)
