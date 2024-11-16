"""
该模块提供了一个用于操作网页的页面
"""

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PySide6.QtNetwork import QNetworkCookie
from PySide6.QtCore import QUrl, QDate
from PySide6.QtGui import QIcon


class WebWindow(QMainWindow):
    def __init__(self, mainGUI, title: str,  url: str, cookie: str):
        self.mainGUI = mainGUI
        mainGUI.web_ui = self
        super().__init__()
        self.setWindowIcon(QIcon(":/imgs/BiliBili_favicon.ico"))
        self.setWindowTitle(title)
        self.resize(800, 600)

        self.profile = QWebEngineProfile.defaultProfile()
        self.cookie_store = self.profile.cookieStore()
        if "SESSDATA=" in cookie:
            cookie = cookie.split("SESSDATA=")[1].split(";")[0]
        cookie = QNetworkCookie("SESSDATA".encode(), cookie.encode())
        cookie.setDomain("bilibili.com")
        cookie.setPath("/")
        self.cookie_store.setCookie(cookie)

        self.view = QWebEngineView()
        self.page = QWebEnginePage(self.profile)
        self.page.setUrl(QUrl(url))
        self.view.setPage(self.page)
        self.setCentralWidget(self.view)
        self.show()

        self.closeEvent = lambda _: setattr(self, "close_flag", True);

    def closeEvent(self, event):
        self.profile.clearHttpCache()
        self.deleteLater()
        event.accept()