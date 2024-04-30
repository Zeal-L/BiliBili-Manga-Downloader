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
    MAX_RETRY_TINY,
    RETRY_WAIT_EX,
    TIMEOUT_SMALL,
    checkNewVersion,
    log_path,
    logger,
    openFileOrDir,
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
        self.init_qrCode()
        self.init_cookie()
        self.init_biliplus_cookie()
        self.init_savePath()
        self.init_num_thread()
        self.init_openLog()
        self.init_about()
        self.init_clearUserData()
        self.init_saveMethod()
        self.init_checkUpdate()
        self.init_theme()
        self.init_exif_setting()
        self.init_save_meta_setting()
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
    def init_qrCode(self) -> None:
        """绑定二维码按钮"""

        def _() -> None:
            qr = QrCode(self.mainGUI)
            img = qr.generate()
            if img is None:
                return

            self.qr_ui.label_img.setPixmap(QPixmap.fromImage(QImage.fromData(img)).scaled(400, 400))
            self.qr_ui.show()

            # 开一个线程去检测二维码是否扫描成功
            threading.Thread(
                target=qr.get_cookie,
                args=(self.signal_qr_res,),
                daemon=True,
            ).start()

            # 如果用户把二维码窗口关了，就把线程也关了
            self.qr_ui.closeEvent = lambda _: setattr(qr, "close_flag", True)

        self.signal_qr_res.connect(self.qrCodeCallBack)
        self.mainGUI.pushButton_qrcode.clicked.connect(partial(_))

    ############################################################
    def init_cookie(self) -> None:
        """绑定Cookie值"""

        stored_cookie = self.mainGUI.getConfig("cookie")
        if stored_cookie:
            self.mainGUI.lineEdit_my_cookie.setText(stored_cookie)

        def _() -> None:
            new_cookie = self.mainGUI.lineEdit_my_cookie.text().strip()
            if new_cookie == "":
                QMessageBox.information(self.mainGUI, "提示", "请输入Cookie！")
                return
            self.mainGUI.updateConfig("cookie", new_cookie)
            self.mainGUI.lineEdit_my_cookie.setEnabled(False)
            self.mainGUI.pushButton_my_cookie.clearFocus()
            self.mainGUI.pushButton_my_cookie.setEnabled(False)
            threading.Thread(
                target=self.check_cookie_valid,
                args=(new_cookie, True),
                daemon=True,
            ).start()

        self.mainGUI.lineEdit_my_cookie.returnPressed.connect(_)
        self.mainGUI.pushButton_my_cookie.clicked.connect(_)

    ############################################################
    def check_cookie_valid(self, cookie: str, notice: bool = False) -> bool:
        """判断Cookie是否有效

        Args:
            cookie (str): Cookie值
            notice (bool): Cookie值有效是否提示
        Returns:
            bool: (Cookie是否有效)
        """

        detail_url = "https://manga.bilibili.com/twirp/comic.v1.Comic/Search?device=pc&platform=web"
        headers = {
            "cookie": f"SESSDATA={cookie}",
        }
        payload = {"key_word": "test", "page_num": 1, "page_size": 1}
        is_cookie_valid = False

        @retry(stop_max_delay=MAX_RETRY_TINY, wait_exponential_multiplier=RETRY_WAIT_EX)
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
            if notice:
                self.mainGUI.signal_information_box.emit("Cookie有效！")
            is_cookie_valid = True
        except requests.RequestException as e:
            logger.error(f"重复测试Cookie是否有效多次后失败!\n{e}")
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                "重复测试Cookie是否有效多次后失败!\n请核对输入的Cookie值或者检查网络连接!\n\n更多详细信息请查看日志文件",
            )
        self.mainGUI.lineEdit_my_cookie.setEnabled(True)
        self.mainGUI.pushButton_my_cookie.setEnabled(True)
        return is_cookie_valid

    ############################################################
    def init_biliplus_cookie(self) -> None:
        """绑定BiliPlus Cookie值"""

        stored_cookie = self.mainGUI.getConfig("biliplus_cookie")
        if stored_cookie:
            self.mainGUI.lineEdit_biliplus_cookie.setText(stored_cookie)

        def _() -> None:
            new_cookie = self.mainGUI.lineEdit_biliplus_cookie.text().strip()
            if new_cookie == "":
                QMessageBox.information(self.mainGUI, "提示", "请输入Cookie！")
                return
            self.mainGUI.updateConfig("biliplus_cookie", new_cookie)
            self.mainGUI.lineEdit_biliplus_cookie.setEnabled(False)
            self.mainGUI.pushButton_biliplus_cookie.clearFocus()
            self.mainGUI.pushButton_biliplus_cookie.setEnabled(False)
            threading.Thread(
                target=self.check_biliplus_cookie_valid,
                args=(new_cookie, True),
                daemon=True,
            ).start()

        self.mainGUI.lineEdit_biliplus_cookie.returnPressed.connect(_)
        self.mainGUI.pushButton_biliplus_cookie.clicked.connect(_)

    ############################################################
    def check_biliplus_cookie_valid(self, cookie: str, notice: bool = False) -> bool:
        """判断BiliPlus Cookie是否有效

        Args:
            cookie (str): Cookie值
            notice (bool): Cookie值有效是否提示
        Returns:
            bool: (Cookie是否有效)
        """

        main_url = "https://www.biliplus.com/manga/"
        headers = {
            "cookie": f"{cookie};manga_sharing=on;",
        }
        is_cookie_valid = False

        @retry(stop_max_delay=MAX_RETRY_TINY, wait_exponential_multiplier=RETRY_WAIT_EX)
        def _() -> bool | None:
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
            if "书架" in res.text:
                return True
            elif "未登录" in res.text:
                return False
            else:
                return False

        try:
            result = _()
            if None is result:
                self.mainGUI.signal_message_box.emit(
                    "BiliPlus访问异常!\n暂时无法检测是否有效!\n请自行判断BiliPlus可访问状态或联系开发者"
                )
            elif False is result:
                self.mainGUI.signal_message_box.emit(
                    "BiliPlus Cookie检测无效!\n请核对输入的Cookie是否正确以及完整!"
                )
            elif True is result:
                is_cookie_valid = True
                if notice:
                    self.mainGUI.signal_information_box.emit("BiliPlus Cookie有效！")
        except requests.RequestException as e:
            msg = "重复测试biliplus Cookie是否有效多次后失败!"
            logger.error(msg)
            logger.exception(e)
            self.mainGUI.signal_message_box.emit(
                f"{msg}\n请检查网络连接或者重启软件!\n\n"
                f"更多详细信息请查看日志文件, 或联系开发者！"
            )
        self.mainGUI.lineEdit_biliplus_cookie.setEnabled(True)
        self.mainGUI.pushButton_biliplus_cookie.setEnabled(True)
        return is_cookie_valid

    ############################################################
    def init_savePath(self) -> None:
        """绑定漫画保存路径设置"""

        # ? 绑定选择路径按钮的回调函数
        def _() -> None:
            path = QFileDialog.getExistingDirectory(self.mainGUI, "选择保存路径")
            if os.path.exists(path):
                self.mainGUI.lineEdit_save_path.setText(path)
                self.mainGUI.updateConfig("save_path", path)
            else:
                self.mainGUI.lineEdit_save_path.setText(os.getcwd())
                self.mainGUI.updateConfig("save_path", os.getcwd())

        self.mainGUI.pushButton_save_path.clicked.connect(_)

        # ? 绑定保存路径文本框的回调函数
        def _() -> None:
            path = self.mainGUI.lineEdit_save_path.text()
            if os.path.exists(path):
                self.mainGUI.updateConfig("save_path", path)
            else:
                self.mainGUI.lineEdit_save_path.setText(os.getcwd())
                self.mainGUI.updateConfig("save_path", os.getcwd())
            self.mainGUI.lineEdit_save_path.clearFocus()

        self.mainGUI.lineEdit_save_path.returnPressed.connect(_)

    ############################################################
    def init_num_thread(self) -> None:
        """绑定线程数设置

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """

        if self.mainGUI.getConfig("num_thread") is not None:
            self.mainGUI.h_Slider_num_thread.setValue(self.mainGUI.getConfig("num_thread"))
        else:
            self.mainGUI.updateConfig("num_thread", self.mainGUI.h_Slider_num_thread.value())

        self.mainGUI.label_num_thread_count.setText(
            f"同时下载线程数：{self.mainGUI.getConfig('num_thread')}"
        )

        def _(value) -> None:
            self.mainGUI.label_num_thread_count.setText(f"同时下载线程数：{value}")
            self.mainGUI.updateConfig("num_thread", value)

        self.mainGUI.h_Slider_num_thread.valueChanged.connect(_)

    ############################################################
    def init_openLog(self) -> None:
        """绑定打开日志文件

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        self.mainGUI.pushButton_open_log.clicked.connect(
            lambda: openFileOrDir(self.mainGUI, os.path.join(log_path, "ERROR.log"))
        )

    ############################################################
    def init_about(self) -> None:
        """绑定关于按钮

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        about_window = MyAboutUI()
        self.mainGUI.pushButton_about.clicked.connect(partial(about_window.show))

    ############################################################
    def init_clearUserData(self) -> None:
        """绑定清理用户数据设置"""

        def _() -> None:
            res = QMessageBox.information(
                self.mainGUI,
                "提示",
                "清除所有用户数据，不包括已下载漫画\n只包括Cookie和其他程序缓存文件\n\n注意：清除后将无法恢复\n当前会话不再产生新的配置文件，所有新配置只在当前会话有效",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res == QMessageBox.Yes:
                self.clear_user_data = True

        self.mainGUI.pushButton_clear_data.clicked.connect(_)

    ############################################################
    def init_saveMethod(self) -> None:
        """绑定保存方式设置"""
        if self.mainGUI.getConfig("save_method") is not None:
            for i in range(self.mainGUI.h_Layout_groupBox_save_method.count()):
                button: QRadioButton = self.mainGUI.h_Layout_groupBox_save_method.itemAt(i).widget()
                if button.text() == self.mainGUI.getConfig("save_method"):
                    button.setChecked(True)
        else:
            for i in range(self.mainGUI.h_Layout_groupBox_save_method.count()):
                button: QRadioButton = self.mainGUI.h_Layout_groupBox_save_method.itemAt(i).widget()
                if button.isChecked():
                    self.mainGUI.updateConfig("save_method", button.text())
                    break

        def _(button: QRadioButton, checked: bool) -> None:
            if checked:
                self.mainGUI.updateConfig("save_method", button.text())

        for i in range(self.mainGUI.h_Layout_groupBox_save_method.count()):
            button: QRadioButton = self.mainGUI.h_Layout_groupBox_save_method.itemAt(i).widget()
            button.toggled.connect(partial(_, button))

    ############################################################

    def init_checkUpdate(self) -> None:
        """绑定检查更新按钮"""
        self.mainGUI.pushButton_check_update.clicked.connect(partial(checkNewVersion, self.mainGUI))

    ############################################################

    def init_theme(self) -> None:
        """绑定主题相关设置"""

        # ? 绑定主题样式设置
        theme_style = self.mainGUI.getConfig("theme_style")
        if theme_style is None:
            self.mainGUI.updateConfig("theme_style", "default")
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
        self.mainGUI.comboBox_theme_style.addItems(styles_list.values())
        self.mainGUI.comboBox_theme_style.setCurrentText(styles_list[theme_style])

        def _(text: str) -> None:
            self.mainGUI.updateConfig("theme_style", reversed_styles_list[text])
            self.mainGUI.apply_stylesheet(
                self.mainGUI,
                reversed_styles_list[text],
                extra={
                    "density_scale": f"{self.mainGUI.getConfig('theme_density')}",
                },
            )

            if text == "默认":
                self.mainGUI.comboBox_theme_density.setEnabled(False)
            else:
                self.mainGUI.comboBox_theme_density.setEnabled(True)

        self.mainGUI.comboBox_theme_style.currentTextChanged.connect(_)

        # ? 绑定主题密度设置
        theme_density = self.mainGUI.getConfig("theme_density")
        if theme_density is None:
            self.mainGUI.updateConfig("theme_density", 0)
            theme_density = 0

        self.mainGUI.comboBox_theme_density.addItems(["-2", "-1", "0", "1", "2"])
        self.mainGUI.comboBox_theme_density.setCurrentText(str(theme_density))

        def _(text: str) -> None:
            self.mainGUI.updateConfig("theme_density", int(text))
            self.mainGUI.apply_stylesheet(
                self.mainGUI,
                self.mainGUI.getConfig("theme_style"),
                extra={
                    "density_scale": f"{int(text)}",
                },
            )

        self.mainGUI.comboBox_theme_density.currentTextChanged.connect(_)

        # ? 初始化主题样式+密度
        self.mainGUI.apply_stylesheet(
            self.mainGUI,
            self.mainGUI.getConfig("theme_style"),
            extra={
                "density_scale": f"{self.mainGUI.getConfig('theme_density')}",
            },
        )

        if self.mainGUI.comboBox_theme_style.currentText() == "默认":
            self.mainGUI.comboBox_theme_density.setEnabled(False)

    ############################################################

    def init_exif_setting(self) -> None:
        """绑定EXIF信息设置"""
        flag = self.mainGUI.getConfig("exif")
        if flag is not None:
            self.mainGUI.checkBox_exif_info.setChecked(flag)
        else:
            self.mainGUI.updateConfig("exif", True)

        def _(checked: bool) -> None:
            self.mainGUI.updateConfig("exif", checked)

        self.mainGUI.checkBox_exif_info.toggled.connect(_)

    ############################################################

    def init_save_meta_setting(self) -> None:
        """绑定保存元数据设置"""
        flag = self.mainGUI.getConfig("save_meta")
        if flag is not None:
            self.mainGUI.checkBox_save_meta.setChecked(flag)
        else:
            self.mainGUI.updateConfig("save_meta", True)

        def _(checked: bool) -> None:
            self.mainGUI.updateConfig("save_meta", checked)

        self.mainGUI.checkBox_save_meta.toggled.connect(_)
