"""通过阅读器自身的网络请求保存原始响应体，不截图、不解密、不转码。"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import BrowserContext, Page, Request, sync_playwright
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QInputDialog, QMessageBox

from src.Utils import data_path, logger, myStrFilter, openFileOrDir


class 下载错误(RuntimeError):
    """浏览器原始响应下载失败。"""


@dataclass(frozen=True)
class 下载结果:
    """一次章节下载的统计结果。"""

    目录: str
    总数: int
    图片数: int
    其他响应数: int
    失败数: int
    声明页数: int = 0


@dataclass(frozen=True)
class 响应记录:
    """写入下载清单的单条响应信息，不保存签名地址或 Cookie。"""

    序号: int
    文件名: str
    状态: str
    响应类型: str
    字节数: int
    SHA256: str
    路径标识: str


def 校验章节地址(地址: str) -> str:
    """只接受哔哩哔哩漫画的具体章节阅读页。"""
    地址 = 地址.strip()
    地址部件 = urlsplit(地址)
    if 地址部件.scheme != "https" or 地址部件.hostname != "manga.bilibili.com":
        raise ValueError("请输入 https://manga.bilibili.com 的章节阅读页地址。")
    if not re.fullmatch(r"/mc\d+/\d+", 地址部件.path):
        raise ValueError("地址必须指向具体章节，例如 https://manga.bilibili.com/mc33584/1232755。")
    return 地址


def 识别图片格式(内容: bytes) -> str | None:
    """根据文件魔数识别格式，不信任 URL 后缀和响应声明。"""
    if 内容.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if 内容.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(内容) >= 16 and 内容[4:8] == b"ftyp":
        品牌 = 内容[8:16]
        if 品牌[:4] in {b"avif", b"avis"} or 品牌[4:] in {b"avif", b"avis"}:
            return "avif"
    if 内容.startswith(b"RIFF") and 内容[8:12] == b"WEBP":
        return "webp"
    return None


def 清理标题(标题: str, 备用标题: str) -> str:
    """生成可用于本地目录的短标题。"""
    标题 = re.sub(r"\s*-\s*漫画全集在线观看\s*-\s*哔哩哔哩漫画\s*$", "", 标题)
    标题 = myStrFilter(标题).strip(" .")
    return (标题 or 备用标题)[:120]


class 浏览器原始响应下载器:
    """在单个工作线程中驱动浏览器并顺序保存响应。"""

    def __init__(
        self,
        地址: str,
        保存根目录: str,
        Cookie: str = "",
        进度回调: Callable[[str], None] | None = None,
        最多页数: int | None = None,
    ) -> None:
        self.地址 = 校验章节地址(地址)
        self.保存根目录 = Path(保存根目录).expanduser().resolve()
        self.Cookie = Cookie.strip()
        self.进度回调 = 进度回调 or (lambda 消息: None)
        self.最多页数 = 最多页数
        self.停止事件 = threading.Event()
        self.已见路径: set[str] = set()
        self.响应地址: dict[str, str] = {}
        self.记录: list[响应记录] = []
        self.目标页数 = 0

    def 停止(self) -> None:
        """请求当前任务在安全点停止。"""
        self.停止事件.set()

    def 报告(self, 消息: str) -> None:
        """向界面报告不含凭据的进度。"""
        self.进度回调(消息)

    @staticmethod
    def 规范路径(地址: str) -> str:
        """去掉尺寸及格式后缀，保留服务器图片路径标识。"""
        路径 = unquote(urlsplit(地址).path)
        return 路径.split("@", 1)[0]

    @classmethod
    def 是否漫画图片地址(cls, 地址: str) -> bool:
        """过滤界面素材，只保留漫画内容服务器的响应。"""
        部件 = urlsplit(地址)
        return (
            部件.scheme == "https"
            and bool(部件.hostname and 部件.hostname.endswith(".hdslb.com"))
            and 部件.path.startswith("/bfs/manga/")
        )

    def 登记请求(self, 请求: Request) -> None:
        """只记录阅读器正常发出的图片请求，不主动重放签名接口。"""
        if self.是否漫画图片地址(请求.url):
            self.登记路径(请求.url)

    def 登记路径(self, 地址: str) -> None:
        """按实际网络请求的出现顺序登记路径并去重。"""
        路径 = self.规范路径(地址)
        if not 路径.startswith("/bfs/manga/") or 路径 in self.已见路径:
            return
        self.已见路径.add(路径)
        self.响应地址[路径] = 地址

    def 启动浏览器(self, 浏览器驱动):
        """优先使用系统 Edge，浏览器登录状态保存在应用专用目录。"""
        配置目录 = Path(data_path) / "浏览器配置"
        配置目录.mkdir(parents=True, exist_ok=True)
        参数 = {
            "user_data_dir": str(配置目录),
            "headless": False,
            "viewport": {"width": 1280, "height": 900},
            "locale": "zh-CN",
        }
        if os.name == "nt":
            return 浏览器驱动.chromium.launch_persistent_context(channel="msedge", **参数)
        return 浏览器驱动.chromium.launch_persistent_context(**参数)

    def 等待图片(self, 页: Page) -> None:
        """等待阅读器实际请求稳定；用户可在浏览器中正常滚动加载更多页。"""
        滑块 = 页.locator('input[type="range"][min="0"]').first
        if 滑块.count():
            self.目标页数 = int(滑块.get_attribute("max") or "0") + 1
        self.报告("正在捕获阅读器实际图片请求；可在浏览器中正常滚动加载需要的页，请不要快速翻页。")
        开始时间 = time.monotonic()
        上次变化时间 = 开始时间
        上次数量 = -1
        while time.monotonic() - 开始时间 < 90:
            if self.停止事件.is_set():
                raise 下载错误("任务已取消。")
            if 页.is_closed():
                raise 下载错误("浏览器页面已关闭，任务停止。")
            当前数量 = len(self.响应地址)
            if self.最多页数 is not None and 当前数量 >= self.最多页数:
                return
            if 当前数量 != 上次数量:
                上次数量 = 当前数量
                上次变化时间 = time.monotonic()
                self.报告(f"已捕获 {当前数量} 个实际图片请求，等待响应稳定。")
            经过时间 = time.monotonic() - 开始时间
            if 经过时间 >= 15 and time.monotonic() - 上次变化时间 >= 8:
                break
            页.wait_for_timeout(500)
        if not self.响应地址:
            raise 下载错误("没有捕获到漫画图片请求，请确认章节已打开且当前账号有权阅读。")

    def 读取响应(self, 页: Page, 地址: str) -> tuple[bytes, str]:
        """在页面上下文读取二进制响应；base64 仅用于进程间传输。"""
        脚本 = """
        async ({url}) => {
            const response = await fetch(url, {credentials: 'omit', cache: 'force-cache'});
            const buffer = await response.arrayBuffer();
            const bytes = new Uint8Array(buffer);
            const chunkSize = 32768;
            const chunks = [];
            for (let offset = 0; offset < bytes.length; offset += chunkSize) {
                chunks.push(btoa(String.fromCharCode(...bytes.subarray(offset, offset + chunkSize))));
            }
            return {status: response.status, ok: response.ok, contentType: response.headers.get('content-type') || '', base64Chunks: chunks};
        }
        """
        最后错误 = ""
        for 尝试 in range(3):
            if self.停止事件.is_set():
                raise 下载错误("任务已取消。")
            try:
                结果 = 页.evaluate(脚本, {"url": 地址})
                if not 结果["ok"]:
                    raise 下载错误(f"图片请求返回 HTTP {结果['status']}。")
                内容 = b"".join(base64.b64decode(块, validate=True) for 块 in 结果["base64Chunks"])
                return 内容, 结果["contentType"]
            except Exception as 异常:
                最后错误 = str(异常).split("\n", 1)[0]
                if 尝试 < 2:
                    time.sleep(1 + 尝试)
        raise 下载错误(f"读取图片响应失败：{最后错误}")

    def 保存清单(self, 目录: Path, 标题: str, 结果: 下载结果) -> None:
        """保存可审计的下载结果，清单不记录签名 URL 和登录信息。"""
        清单 = {
            "章节标题": 标题,
            "章节标识": urlsplit(self.地址).path.strip("/"),
            "说明": "文件为浏览器 HTTP 内容解码后的原始响应体，不经截图、canvas、图片解码或转码；无法识别的加密响应原样保存为 bin。",
            "结果": asdict(结果),
            "响应": [asdict(项) for 项 in self.记录],
        }
        (目录 / "下载清单.json").write_text(
            json.dumps(清单, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def 下载(self) -> 下载结果:
        """执行完整下载并始终关闭浏览器资源。"""
        with sync_playwright() as 浏览器驱动:
            上下文: BrowserContext | None = None
            try:
                上下文 = self.启动浏览器(浏览器驱动)
                if self.Cookie:
                    上下文.add_cookies(
                        [
                            {
                                "name": "SESSDATA",
                                "value": self.Cookie,
                                "domain": ".bilibili.com",
                                "path": "/",
                                "secure": True,
                                "httpOnly": True,
                            }
                        ]
                    )
                页 = 上下文.pages[0] if 上下文.pages else 上下文.new_page()
                页.on("request", self.登记请求)
                self.报告("正在打开章节阅读页；如需登录，请在浏览器中完成登录。")
                页.goto(self.地址, wait_until="domcontentloaded", timeout=60000)
                页.wait_for_timeout(3000)
                self.等待图片(页)
                标题 = 清理标题(页.title(), urlsplit(self.地址).path.rsplit("/", 1)[-1])
                目录 = self.保存根目录 / "浏览器原始响应" / 标题
                目录.mkdir(parents=True, exist_ok=True)
                候选路径 = list(self.响应地址)
                if self.最多页数 is not None:
                    候选路径 = 候选路径[: self.最多页数]
                总数 = len(候选路径)
                self.报告(f"本次捕获 {总数} 个实际网络响应，开始原样保存。")
                for 序号, 路径 in enumerate(候选路径, 1):
                    if self.停止事件.is_set():
                        raise 下载错误("任务已取消，已保存的文件和清单会保留。")
                    地址 = self.响应地址.get(路径)
                    if not 地址:
                        self.记录.append(响应记录(序号, "", "缺少实际响应地址", "", 0, "", 路径))
                        continue
                    try:
                        内容, 响应类型 = self.读取响应(页, 地址)
                        扩展名 = 识别图片格式(内容) or "bin"
                        文件名 = f"{序号:03d}.{扩展名}"
                        (目录 / 文件名).write_bytes(内容)
                        状态 = "标准图片" if 扩展名 != "bin" else "未识别原始响应"
                        self.记录.append(
                            响应记录(
                                序号,
                                文件名,
                                状态,
                                响应类型,
                                len(内容),
                                hashlib.sha256(内容).hexdigest(),
                                路径,
                            )
                        )
                    except (下载错误, binascii.Error, OSError) as 异常:
                        logger.warning(f"保存第 {序号} 页原始响应失败：{异常}")
                        self.记录.append(响应记录(序号, "", str(异常), "", 0, "", 路径))
                    self.报告(f"正在保存原始响应：{序号}/{总数}")
                失败记录 = [项 for 项 in self.记录 if not 项.文件名]
                结果 = 下载结果(
                    目录=str(目录),
                    总数=总数,
                    图片数=sum(
                        项.文件名.endswith((".avif", ".jpg", ".png", ".webp")) for 项 in self.记录
                    ),
                    其他响应数=sum(项.文件名.endswith(".bin") for 项 in self.记录),
                    失败数=len(失败记录),
                    声明页数=self.目标页数,
                )
                self.保存清单(目录, 标题, 结果)
                return 结果
            finally:
                if 上下文 is not None:
                    上下文.close()


class 浏览器原始响应下载控制器(QObject):
    """把阻塞的浏览器任务隔离到独立线程，并通过 Qt 信号更新界面。"""

    状态变化 = Signal(str)
    运行状态变化 = Signal(bool)
    下载完成 = Signal(object)
    下载失败 = Signal(str)

    def __init__(self, 主窗口) -> None:
        super().__init__(主窗口)
        self.主窗口 = 主窗口
        self.执行器 = ThreadPoolExecutor(max_workers=1, thread_name_prefix="浏览器原始响应")
        self.当前下载器: 浏览器原始响应下载器 | None = None
        self.正在运行 = False
        self.状态变化.connect(self.主窗口.statusBar().showMessage)
        self.运行状态变化.connect(self.主窗口.pushButton_浏览器原始响应下载.setDisabled)
        self.下载完成.connect(self.显示完成)
        self.下载失败.connect(self.显示失败)

    def 开始(self) -> None:
        """询问章节地址并启动一个独立下载任务。"""
        if self.正在运行:
            return
        地址, 已确认 = QInputDialog.getText(
            self.主窗口,
            "浏览器原始响应下载",
            "粘贴具体章节阅读页地址：\n程序会打开系统浏览器，由阅读器正常加载图片。\n标准图片按原格式保存，其他原始响应保存为 .bin。",
            text=self.主窗口.getConfig("浏览器章节地址") or "",
        )
        if not 已确认:
            return
        try:
            地址 = 校验章节地址(地址)
            下载器 = 浏览器原始响应下载器(
                地址,
                self.主窗口.getConfig("save_path") or os.getcwd(),
                self.主窗口.getConfig("cookie") or "",
                self.状态变化.emit,
            )
        except ValueError as 异常:
            QMessageBox.warning(self.主窗口, "地址不正确", str(异常))
            return
        self.主窗口.updateConfig("浏览器章节地址", 地址)
        self.当前下载器 = 下载器
        self.正在运行 = True
        self.运行状态变化.emit(True)
        self.执行器.submit(self.执行, 下载器)

    def 执行(self, 下载器: 浏览器原始响应下载器) -> None:
        """在工作线程中执行浏览器任务并发送最终结果。"""
        try:
            结果 = 下载器.下载()
            self.下载完成.emit(结果)
        except Exception as 异常:
            logger.exception(f"浏览器原始响应下载失败：{异常}")
            self.下载失败.emit(str(异常))
        finally:
            self.正在运行 = False
            self.运行状态变化.emit(False)

    def 显示完成(self, 结果: 下载结果) -> None:
        """在 GUI 主线程显示结果并打开保存目录。"""
        消息 = f"本次捕获并保存 {结果.总数 - 结果.失败数}/{结果.总数} 个响应：{结果.图片数} 张标准图片，{结果.其他响应数} 个其他原始响应。"
        if 结果.声明页数 > 结果.总数:
            消息 += f"阅读器标称共 {结果.声明页数} 页，未加载的页面不包含在本次结果中。"
        if 结果.失败数:
            消息 += f"另有 {结果.失败数} 个响应保存失败，详见下载清单。"
        self.状态变化.emit(消息)
        QMessageBox.information(
            self.主窗口, "原始响应下载完成", f"{消息}\n\n保存位置：\n{结果.目录}"
        )
        openFileOrDir(self.主窗口, 结果.目录)

    def 显示失败(self, 消息: str) -> None:
        """在 GUI 主线程显示错误。"""
        self.状态变化.emit("原始响应下载失败")
        QMessageBox.warning(self.主窗口, "原始响应下载失败", 消息)

    def 关闭(self) -> None:
        """请求停止任务并拒绝新的后台工作。"""
        if self.当前下载器 is not None:
            self.当前下载器.停止()
        self.执行器.shutdown(wait=False, cancel_futures=True)
