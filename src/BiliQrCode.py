"""
该模块提供了一个用于生成Bilibili扫码登录二维码的类QrCode，以及确认登录和获取cookie的方法
"""

from __future__ import annotations

import io
import time
from typing import TYPE_CHECKING

import qrcode
import requests
from PySide6.QtCore import SignalInstance
from PySide6.QtWidgets import QMessageBox
from retrying import retry

from src.Utils import MAX_RETRY_SMALL, RETRY_WAIT_EX, TIMEOUT_SMALL, logger

if TYPE_CHECKING:
    from ui.MainGUI import MainGUI


class QrCode:
    """Bilibili 扫码登录二维码类"""

    def __init__(self, mainGUI: MainGUI) -> None:
        self.mainGUI = mainGUI
        self.generate_url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
        self.poll_url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
        self.code_url = None
        self.qrcode_key = None
        self.close_flag = False
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "origin": "https://manga.bilibili.com",
        }

    def generate(self) -> str | None:
        """生成登入二维码

        Returns:
            str: 二维码内容, 二维码图片

        """

        @retry(stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX)
        def _() -> dict:
            try:
                res = requests.get(self.generate_url, headers=self.headers, timeout=TIMEOUT_SMALL)
            except requests.RequestException as e:
                logger.warning(f"获取登入二维码失败! 重试中...\n {e}")
                raise e
            if res.status_code != 200:
                logger.warning(f"获取登入二维码失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中...")
                raise requests.HTTPError()
            return res.json()["data"]

        logger.info("正在获取登入二维码...")

        try:
            data = _()
            self.code_url = data["url"]
            self.qrcode_key = data["qrcode_key"]
        except (requests.RequestException, requests.HTTPError)  as e:
            logger.error(f"重复获取登入二维码多次后失败! {e}")
            logger.exception(e)
            QMessageBox.warning(
                self.mainGUI, "警告", "重复获取登入二维码多次后失败!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件"
            )
            return None

        img = qrcode.make(self.code_url)

        image_bytes = io.BytesIO()
        img.save(image_bytes, format="PNG")
        image_bytes = image_bytes.getvalue()

        return image_bytes

    def confirm(self) -> dict | None:
        """确认登入

        Returns:
            str: SESSDATA cookie
        """

        @retry(stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX)
        def _() -> dict:
            try:
                res = requests.get(
                    self.poll_url,
                    headers=self.headers,
                    params={
                        "qrcode_key": self.qrcode_key,
                    },
                    timeout=TIMEOUT_SMALL,
                )
            except requests.RequestException as e:
                logger.warning(f"确认二维码登入失败! 重试中...\n {e}")
                raise e
            if res.status_code != 200:
                logger.warning(f"确认二维码登入失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中...")
                raise requests.HTTPError()
            return res.json()["data"]

        try:
            data = _()
        except (requests.RequestException, requests.HTTPError) as e:
            logger.error(f"重复确认登入多次后失败! {e}")
            logger.exception(e)
            self.mainGUI.signal_message_box.emit("重复确认登入多次后失败!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件")
            return None

        return data

    def get_cookie(self, qr_res: SignalInstance) -> None:
        """获取cookie

        Args:
            qr_res (SignalInstance): 信号槽，用于传递二维码扫描结果

        """

        while not self.close_flag:
            data = self.confirm()

            # 扫码登录成功或者二维码过期或者请求失败
            if data is None or data["code"] in [0, 86038]:
                qr_res.emit(data)
                break

            qr_res.emit(data)

            # 每隔1秒确认一次
            time.sleep(1)
