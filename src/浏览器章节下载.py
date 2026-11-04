"""使用阅读器逐页获取并保存标准图片，兼容新版加密图片容器。"""

from __future__ import annotations

import base64
import binascii
import os
from collections.abc import Callable
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from src.图片解密 import 图片解密错误, 解密图片
from src.浏览器原始响应下载 import 识别图片格式


class 浏览器章节下载错误(RuntimeError):
    """未能取得完整且可识别的章节图片。"""


查找阅读器脚本 = """
(element) => {
    while (element) {
        if (element.__vue__ && 'allEpisodeReaderImages' in (element.__vue__.$data || {})) {
            return element.__vue__;
        }
        element = element.parentElement;
    }
    return null;
}
"""


def 下载章节图片(
    漫画ID: int,
    章节ID: int,
    Cookie: str,
    保存目录: str,
    进度回调: Callable[[int, int], None] | None = None,
    停止检查: Callable[[], bool] | None = None,
) -> list[str]:
    """按阅读器页序下载完整章节，返回已校验的临时图片路径。"""
    目录 = Path(保存目录)
    目录.mkdir(parents=True, exist_ok=True)
    进度回调 = 进度回调 or (lambda 当前, 总数: None)
    停止检查 = 停止检查 or (lambda: False)
    单页脚本 = """
    async ({episodeId, index, findReader}) => {
        const reader = eval(`(${findReader})`)(document.querySelector('.image-item'));
        const image = reader?.episodeReaderImages?.find(item => item._episodeId === episodeId && item._imageIndex === index && item._type === 0);
        if (!image) throw new Error('阅读器缺少对应图片模型');
        await image.loadToken();
        const response = await fetch(image._completeUrl, {credentials: 'omit'});
        const buffer = await response.arrayBuffer();
        const bytes = new Uint8Array(buffer);
        const chunks = [];
        for (let offset = 0; offset < bytes.length; offset += 32768) {
            chunks.push(btoa(String.fromCharCode(...bytes.subarray(offset, offset + 32768))));
        }
        const keyEntry = image._m1Key.find(item => item.url === image._completeUrl);
        const privateKey = image._m1Info.find(item => item.key === keyEntry?.key)?.m1 || '';
        return {
            status: response.status,
            encrypted: image._hitEncrpyt === true,
            url: image._completeUrl,
            privateKey,
            chunks
        };
    }
    """
    try:
        with sync_playwright() as 浏览器驱动:
            参数 = {"headless": True}
            if os.name == "nt":
                参数["channel"] = "msedge"
            浏览器 = 浏览器驱动.chromium.launch(**参数)
            try:
                上下文 = 浏览器.new_context(
                    viewport={"width": 1280, "height": 900}, locale="zh-CN"
                )
                if Cookie.strip():
                    上下文.add_cookies(
                        [
                            {
                                "name": "SESSDATA",
                                "value": Cookie.strip(),
                                "domain": ".bilibili.com",
                                "path": "/",
                                "secure": True,
                                "httpOnly": True,
                            }
                        ]
                    )
                页 = 上下文.new_page()
                页.goto(
                    f"https://manga.bilibili.com/mc{漫画ID}/{章节ID}",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                页.wait_for_selector(".image-item", state="attached", timeout=45000)
                页.wait_for_function(
                    """
                    ({episodeId, findReader}) => {
                        const reader = eval(`(${findReader})`)(document.querySelector('.image-item'));
                        return (reader?.episodeReaderImages?.filter(item => item._episodeId === episodeId && item._type === 0).length || 0) > 0;
                    }
                    """,
                    arg={"episodeId": 章节ID, "findReader": 查找阅读器脚本},
                    timeout=30000,
                )
                总页数 = 页.evaluate(
                    """
                    ({episodeId, findReader}) => {
                        const reader = eval(`(${findReader})`)(document.querySelector('.image-item'));
                        return reader.episodeReaderImages.filter(item => item._episodeId === episodeId && item._type === 0).length;
                    }
                    """,
                    {"episodeId": 章节ID, "findReader": 查找阅读器脚本},
                )
                if not isinstance(总页数, int) or 总页数 <= 0:
                    raise 浏览器章节下载错误("阅读器未返回有效页数。")
                图片路径 = []
                for 序号 in range(总页数):
                    if 停止检查():
                        raise 浏览器章节下载错误("下载已取消。")
                    最后错误 = None
                    for 尝试 in range(3):
                        try:
                            结果 = 页.evaluate(
                                单页脚本,
                                {
                                    "episodeId": 章节ID,
                                    "index": 序号,
                                    "findReader": 查找阅读器脚本,
                                },
                            )
                            if 结果["status"] != 200:
                                raise 浏览器章节下载错误(
                                    f"第{序号 + 1}页请求返回HTTP {结果['status']}。"
                                )
                            内容 = b"".join(
                                base64.b64decode(块, validate=True) for 块 in 结果["chunks"]
                            )
                            if 结果["encrypted"]:
                                if not 结果["privateKey"]:
                                    raise 浏览器章节下载错误(f"第{序号 + 1}页缺少图片转换密钥。")
                                内容 = 解密图片(结果["privateKey"], 内容, 结果["url"])
                            扩展名 = 识别图片格式(内容)
                            if 扩展名 is None:
                                raise 浏览器章节下载错误(f"第{序号 + 1}页不是可识别的标准图片。")
                            break
                        except (PlaywrightError, ValueError, binascii.Error, 图片解密错误) as e:
                            最后错误 = e
                            if 尝试 < 2:
                                页.wait_for_timeout(1000 * (尝试 + 1))
                    else:
                        raise 浏览器章节下载错误(
                            f"第{序号 + 1}页多次处理失败：{最后错误}"
                        ) from 最后错误
                    路径 = 目录 / f"{序号 + 1:03d}.{扩展名}"
                    路径.write_bytes(内容)
                    图片路径.append(str(路径))
                    进度回调(序号 + 1, 总页数)
                return 图片路径
            finally:
                浏览器.close()
    except 浏览器章节下载错误:
        raise
    except (PlaywrightError, OSError, ValueError, binascii.Error, 图片解密错误) as e:
        摘要 = str(e).splitlines()[0][:200]
        raise 浏览器章节下载错误(f"浏览器章节下载失败：{摘要}") from e
