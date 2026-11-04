"""从哔哩哔哩漫画详情页读取官方页面数据，并转换为下载器所需结构。"""

from __future__ import annotations

import os

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright


class 浏览器漫画详情错误(RuntimeError):
    """浏览器未能取得有效的漫画详情。"""


def 获取漫画详情(漫画ID: int, Cookie: str = "") -> dict:
    """读取详情页的章节模型，不访问已失效的旧详情接口。"""
    try:
        漫画ID = int(漫画ID)
    except (TypeError, ValueError) as e:
        raise 浏览器漫画详情错误("漫画ID必须是整数。") from e
    if 漫画ID <= 0:
        raise 浏览器漫画详情错误("漫画ID必须是正整数。")

    脚本 = """
    () => {
        const season = document.querySelector('button.list-item')?.__vue__?.$props?.seasonData;
        if (!season || !Array.isArray(season.episodeList)) return null;
        return {
            id: season.id,
            title: season.title,
            author_name: season.authorName || [],
            styles: season.styles || [],
            is_finish: season.episodeStatusText.includes('完结') ? 1 : 0,
            evaluate: season.evaluate || '',
            vertical_cover: season.verticalCover || '',
            horizontal_cover: season.horizontalCover || '',
            square_cover: season.squareCover || '',
            renewal_time: season.releaseTime || '',
            hall_icon_text: '',
            tags: (season.styles || []).map(name => ({name})),
            ep_list: season.episodeList.map(episode => ({
                id: episode.id,
                ord: episode.ord,
                is_locked: episode.isLocked,
                short_title: episode.shortTitle || '',
                title: episode.title || '',
                size: episode.allImageSize || 0
            }))
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
                    f"https://manga.bilibili.com/detail/mc{漫画ID}",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                页.wait_for_selector("button.list-item", timeout=30000)
                数据 = 页.evaluate(脚本)
                if not isinstance(数据, dict) or not 数据.get("ep_list"):
                    raise 浏览器漫画详情错误("详情页未返回有效的章节数据。")
                return 数据
            finally:
                浏览器.close()
    except 浏览器漫画详情错误:
        raise
    except (PlaywrightError, OSError) as e:
        raise 浏览器漫画详情错误(f"浏览器读取漫画详情失败：{e}") from e
