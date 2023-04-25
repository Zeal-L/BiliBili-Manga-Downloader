from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from hashlib import md5
from re import search, sub
from typing import TYPE_CHECKING

import requests
from pypinyin import lazy_pinyin
from PySide6.QtCore import QEvent, QPoint, QSize, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QWidget,
)
from retrying import RetryError, retry

from src.Comic import Comic
from src.searchComic import SearchComic
from src.utils import MAX_RETRY_SMALL, RETRY_WAIT_EX, TIMEOUT_SMALL, logger

if TYPE_CHECKING:
    from src.ui.MainGUI import MainGUI


class MangaUI:
    def __init__(self, mainGUI: MainGUI):
        self.search_info = None
        self.num_selected = 0
        self.epi_list = None
        self.init_mangaSearch(mainGUI)
        self.init_mangaDetails(mainGUI)
        self.init_myLibrary(mainGUI)
        self.init_episodesDetails(mainGUI)

    ############################################################

    def init_mangaSearch(self, mainGUI: MainGUI) -> None:
        """链接搜索漫画功能

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """

        def _() -> None:
            if not mainGUI.getConfig("cookie"):
                QMessageBox.critical(mainGUI, "警告", "请先在设置界面填写自己的Cookie！")
                return
            # ? 如果输入框为空，只有空格，提示用户输入
            if not mainGUI.lineEdit_manga_search_name.text().strip():
                QMessageBox.critical(mainGUI, "警告", "请输入漫画名！")
                return

            self.search_info = SearchComic(
                mainGUI.lineEdit_manga_search_name.text(), mainGUI.getConfig("cookie")
            ).getResults(mainGUI)
            mainGUI.listWidget_manga_search.clear()
            mainGUI.label_manga_search.setText(f"找到：{len(self.search_info)}条结果")
            for item in self.search_info:
                # ?###########################################################
                # ? 替换爬取信息里的html标签
                item["title"] = sub(r"</[^>]+>", "</span>", item["title"])
                item["title"] = sub(
                    r"<[^/>]+>",
                    '<span style="color:red;font-weight:bold">',
                    item["title"],
                )
                # ?###########################################################
                temp = QListWidgetItem()
                mainGUI.listWidget_manga_search.addItem(temp)
                mainGUI.listWidget_manga_search.setItemWidget(
                    temp,
                    QLabel(
                        f"{item['title']} by <span style='color:blue'>{item['author_name'][0]}</span>"
                    ),
                )

        mainGUI.lineEdit_manga_search_name.returnPressed.connect(_)
        mainGUI.pushButton_manga_search_name.clicked.connect(_)

    ############################################################
    def init_mangaDetails(self, mainGUI: MainGUI) -> None:
        """绑定双击显示漫画详情事件

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """

        def _(item: QListWidgetItem) -> None:
            index = mainGUI.listWidget_manga_search.indexFromItem(item).row()
            comic = Comic(self.search_info[index]["id"], mainGUI)
            self.updateComicInfo(mainGUI, comic)

        mainGUI.listWidget_manga_search.itemDoubleClicked.connect(_)
        # 鼠标移动到图片上的时候更改鼠标样式, 提示用户可以用鼠标点击
        mainGUI.label_manga_image.setCursor(Qt.PointingHandCursor)

    ############################################################
    def init_myLibrary(self, mainGUI: MainGUI) -> None:
        """绑定更新我的库存事件

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        # 布局对齐
        mainGUI.v_Layout_myLibrary.setAlignment(Qt.AlignTop)
        mainGUI.my_library_add_widget.connect(self.updateMyLibrarySingleAdd)
        if mainGUI.getConfig("cookie"):
            self.updateMyLibrary(mainGUI)

        def _() -> None:
            if not mainGUI.getConfig("cookie"):
                QMessageBox.critical(mainGUI, "警告", "请先在设置界面填写自己的Cookie！")
                return
            if self.updateMyLibrary(mainGUI):
                QMessageBox.information(mainGUI, "通知", "更新完成！")

        mainGUI.pushButton_myLibrary_update.clicked.connect(_)

    ############################################################
    # 以下三个函数是为了更新我的库存，是一个整体
    # 拆开的原因主要是为了绕开多线程访问 mainGUI 报错的情况，如下
    # QObject::setParent: Cannot set parent, new parent is in a different thread
    ############################################################

    def updateMyLibrary(self, mainGUI: MainGUI) -> bool:
        """扫描本地并且更新我的库存

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        # ?###########################################################
        # ? 清理v_Layout_myLibrary里的所有控件
        for i in reversed(range(mainGUI.v_Layout_myLibrary.count())):
            to_delete = mainGUI.v_Layout_myLibrary.itemAt(i).widget()
            # deleteLater 会有延迟，为了显示效果，先将父控件设为None
            to_delete.setParent(None)
            to_delete.deleteLater()

        # ?###########################################################
        # ? 读取本地库存
        my_library = {}
        path = mainGUI.getConfig("save_path")

        if os.path.exists(path):
            for item in os.listdir(path):
                if search(r"ID-\d+", item):
                    my_library[int(search(r"ID-(\d+)", item)[1])] = {
                        "comic_name": search(r"(《.*》)", item)[1],
                        "comic_path": os.path.join(path, item),
                    }
        else:
            mainGUI.lineEdit_save_path.setText(os.getcwd())
            mainGUI.updateConfig("save_path", os.getcwd())


        mainGUI.label_myLibrary_count.setText(f"我的库存：{len(my_library)}部")

        # ?###########################################################
        # ? 用多线程添加漫画，避免卡顿
        futures = []
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures.extend(
                executor.submit(
                    self.updateMyLibrarySingle,
                    mainGUI,
                    comic_id,
                    my_library[comic_id]["comic_path"],
                )
                for comic_id in my_library
            )

        if fail_comic := [
            future.result() for future in as_completed(futures) if future.result()
        ]:
            temp = "".join(my_library[i]["comic_name"] + "\n" for i in fail_comic)
            mainGUI.message_box.emit(
                f"以下漫画获取更新多次后失败!\n{temp}\n请检查网络连接或者重启软件\n更多详细信息请查看日志文件, 或联系开发者！"
            )
            return False

        return True

    ############################################################
    def updateMyLibrarySingle(
        self, mainGUI: MainGUI, comic_id: int, comic_path: str
    ) -> int | None:
        """添加单个漫画到我的库存

        Args:
            mainGUI (MainGUI): 主窗口类实例
            comic_id (int): 漫画ID
            comic_path (str): 漫画保存路径
        """
        comic = Comic(comic_id, mainGUI)
        data = comic.getComicInfo()
        # ? 获取漫画信息失败直接跳过
        if not data:
            return comic_id
        epi_list = comic.getEpisodesInfo()

        info = {
            "mainGUI": mainGUI,
            "data": data,
            "comic": comic,
            "epi_list": epi_list,
            "comic_path": comic_path,
        }

        mainGUI.my_library_add_widget.emit(info)
        return None

    ############################################################
    def updateMyLibrarySingleAdd(self, info: dict) -> None:
        """绑定我的库存中单个漫画的点击事件

        Args:
            info (dict): 漫画信息
        """
        mainGUI: MainGUI = info["mainGUI"]
        data: dict = info["data"]
        comic: Comic = info["comic"]
        epi_list: list = info["epi_list"]
        comic_path: str = info["comic_path"]

        h_layout_my_library = QHBoxLayout()
        h_layout_my_library.addWidget(
            QLabel(
                f"<span style='color:blue;font-weight:bold'>{data['title']}</span> by {data['author_name']}"
            )
        )
        h_layout_my_library.addStretch(1)
        h_layout_my_library.addWidget(
            QLabel(f"{comic.getNumDownloaded()}/{len(epi_list)}")
        )

        widget = QWidget()
        widget.setStyleSheet("font-size: 10pt;")

        # ?###########################################################
        # ? 绑定列表内漫画被点击事件：当前点击变色，剩余恢复
        def _(_event: QEvent, widget: QWidget) -> None:
            for i in range(mainGUI.v_Layout_myLibrary.count()):
                temp = mainGUI.v_Layout_myLibrary.itemAt(i).widget()
                temp.setStyleSheet("font-size: 10pt;")
            widget.setStyleSheet(
                "background-color:rgb(200, 200, 255); font-size: 10pt;"
            )

        widget.mousePressEvent = partial(_, widget=widget)
        widget.mouseDoubleClickEvent = partial(self.updateComicInfo, mainGUI, comic)
        widget.setLayout(h_layout_my_library)

        # ?###########################################################
        # ? 绑定右键漫画打开文件夹事件
        def myMenu_openFolder(widget: QWidget, comic_path: str, pos: QPoint) -> None:
            menu = QMenu()
            menu.addAction("打开文件夹", lambda: os.startfile(comic_path))
            menu.exec_(widget.mapToGlobal(pos))

        widget.setContextMenuPolicy(Qt.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            partial(myMenu_openFolder, widget, comic_path)
        )

        # ? 按照标题的拼音顺序插入我的库存列表
        if mainGUI.v_Layout_myLibrary.count() == 0:
            mainGUI.v_Layout_myLibrary.addWidget(widget)
        else:
            for i in range(mainGUI.v_Layout_myLibrary.count()):
                left: str = (
                    mainGUI.v_Layout_myLibrary.itemAt(i)
                    .widget()
                    .findChild(QLabel)
                    .text()
                )
                left_titile: str = left[left.find(">") + 1 : left.rfind("<")]
                if i == mainGUI.v_Layout_myLibrary.count() - 1:
                    mainGUI.v_Layout_myLibrary.addWidget(widget)
                    break
                if lazy_pinyin(data["title"]) <= lazy_pinyin(left_titile):
                    mainGUI.v_Layout_myLibrary.insertWidget(i, widget)
                    break

    ############################################################

    def updateComicInfo(
        self, mainGUI: MainGUI, comic: Comic, _event: QEvent = None
    ) -> None:
        """更新漫画信息详情界面

        Args:
            comic (Comic): 漫画类实例
            mainGUI (MainGUI): 主窗口类实例
        """
        # ?###########################################################
        # ? 更新漫画信息
        data = comic.getComicInfo()
        # ? 获取漫画信息失败直接跳过
        if not data:
            mainGUI.message_box.emit(
                "重复获取漫画信息多次后失败!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！"
            )
            return
        mainGUI.label_manga_title.setText(
            "<span style='color:blue;font-weight:bold'>标题：</span>" + data["title"]
        )
        mainGUI.label_manga_author.setText(
            "<span style='color:blue;font-weight:bold'>作者：</span>" + data["author_name"]
        )
        mainGUI.label_manga_style.setText(
            f"<span style='color:blue;font-weight:bold'>标签：</span>{data['styles'] or '无'}"
        )
        mainGUI.label_manga_isFinish.setText(
            f"<span style='color:blue;font-weight:bold'>状态：</span>{'已完结' if data['is_finish'] else '连载中'}"
        )
        mainGUI.label_manga_outline.setText(
            f"<span style='color:blue;font-weight:bold'>概要：</span>{data['evaluate'] or '无'}"
        )

        # ?###########################################################
        # ? 加载图片，以及绑定双击和悬停事件
        @retry(
            stop_max_delay=MAX_RETRY_SMALL, wait_exponential_multiplier=RETRY_WAIT_EX
        )
        def _() -> bytes:
            try:
                res = requests.get(data["vertical_cover"], timeout=TIMEOUT_SMALL)
            except requests.RequestException() as e:
                logger.warning(f"获取封面图片失败! 重试中...\n{e}")
                raise e
            if res.status_code != 200:
                logger.warning(
                    f"获取封面图片失败! 状态码：{res.status_code}, 理由: {res.reason} 重试中..."
                )
                raise requests.HTTPError()
            if res.headers["Etag"] != md5(res.content).hexdigest():
                logger.warning(
                    f"图片内容 Checksum 不正确! 重试中...\n\t{res.headers['Etag']} ≠ {md5(res.content).hexdigest()}"
                )
                raise requests.HTTPError()
            return res.content

        logger.info(f"获取《{data['title']}》的封面图片中...")
        try:
            img = _()
            label_img = QPixmap.fromImage(QImage.fromData(img))
        except RetryError as e:
            logger.error(f"获取封面图片多次后失败，跳过!\n{e}")
            label_img = QPixmap(":/imgs/fail_img.jpg")
            QMessageBox.warning(
                mainGUI, "警告", "获取封面图片多次后失败!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！"
            )

        mainGUI.label_manga_image.mouseDoubleClickEvent = (
            lambda _event: QDesktopServices.openUrl(
                QUrl(f"https://manga.bilibili.com/detail/mc{data['ID']}")
            )
        )
        mainGUI.label_manga_image.setToolTip(
            f"双击打开漫画详情页\nhttps://manga.bilibili.com/detail/mc{data['ID']}"
        )

        # ?###########################################################
        # ? 重写图片大小改变事件，使图片不会变形
        def _(event: QEvent = None) -> None:
            new_size = event.size() if event else mainGUI.label_manga_image.size()
            if new_size.width() < 200:
                new_size.setWidth(200)
            img = label_img.scaled(
                new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            mainGUI.label_manga_image.setPixmap(img)
            mainGUI.label_manga_image.setAlignment(Qt.AlignTop)

        mainGUI.label_manga_image.resizeEvent = _
        _()

        # ?###########################################################
        # ? 更新漫画章节详情
        mainGUI.listWidget_chp_detail.clear()
        self.num_selected = 0
        num_unlocked = 0
        if comic:
            self.epi_list = comic.getEpisodesInfo()
        for epi in self.epi_list:
            temp = QListWidgetItem(epi.title)
            temp.setCheckState(Qt.Unchecked)
            if epi.isDownloaded():
                temp.setFlags(Qt.NoItemFlags)
                temp.setCheckState(Qt.Checked)
                temp.setBackground(QColor(0, 255, 0, 50))
            if not epi.isAvailable():
                temp.setFlags(Qt.NoItemFlags)
            else:
                num_unlocked += 1
            temp.setSizeHint(QSize(160, 20))
            temp.setTextAlignment(Qt.AlignLeft)
            temp.setToolTip(epi.title)
            mainGUI.listWidget_chp_detail.addItem(temp)

        # ?###########################################################
        # ? 绑定总章节数和已下载章节数等等的显示
        mainGUI.label_chp_detail_total_chp.setText(f"总章数：{len(self.epi_list)}")
        mainGUI.label_chp_detail_num_unlocked.setText(f"已解锁：{num_unlocked}")
        mainGUI.label_chp_detail_num_downloaded.setText(
            f"已下载：{comic.getNumDownloaded()}"
        )
        mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")

    ############################################################

    def init_episodesDetails(self, mainGUI: MainGUI) -> None:
        """绑定章节界面的多选以及右键菜单事件

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        self.num_selected = 0
        mainGUI.listWidget_chp_detail.setDragEnabled(False)

        # ?###########################################################
        # ? 绑定鼠标点击选择信号
        def checkbox_change(item: QListWidgetItem) -> None:
            # 暂停itemChanged 信号，防止死循环
            mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            if item.flags() == Qt.NoItemFlags:
                return
            if item.checkState() == Qt.Checked:
                self.num_selected += 1
            elif item.checkState() == Qt.Unchecked:
                self.num_selected -= 1
            mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")
            mainGUI.listWidget_chp_detail.itemChanged.connect(checkbox_change)

        mainGUI.listWidget_chp_detail.itemChanged.connect(checkbox_change)

        def _(item: QListWidgetItem) -> None:
            mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            if item.flags() == Qt.NoItemFlags:
                return
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
                self.num_selected -= 1
            elif item.checkState() == Qt.Unchecked:
                item.setCheckState(Qt.Checked)
                self.num_selected += 1
            mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")
            mainGUI.listWidget_chp_detail.itemChanged.connect(checkbox_change)

        mainGUI.listWidget_chp_detail.itemPressed.connect(_)

        # ?###########################################################
        # ? 绑定右键菜单，让用户可以勾选或者全选等

        def checkSelected() -> None:
            mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            for item in mainGUI.listWidget_chp_detail.selectedItems():
                if item.flags() != Qt.NoItemFlags and item.checkState() == Qt.Unchecked:
                    item.setCheckState(Qt.Checked)
                    self.num_selected += 1
            mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")
            mainGUI.listWidget_chp_detail.itemChanged.connect(checkbox_change)

        def uncheckSelected() -> None:
            mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            for item in mainGUI.listWidget_chp_detail.selectedItems():
                if item.flags() != Qt.NoItemFlags and item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                    self.num_selected -= 1
            mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")
            mainGUI.listWidget_chp_detail.itemChanged.connect(checkbox_change)

        def checkAll() -> None:
            mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            self.num_selected = 0
            for i in range(mainGUI.listWidget_chp_detail.count()):
                if mainGUI.listWidget_chp_detail.item(i).flags() != Qt.NoItemFlags:
                    mainGUI.listWidget_chp_detail.item(i).setCheckState(Qt.Checked)
                    self.num_selected += 1
            mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")
            mainGUI.listWidget_chp_detail.itemChanged.connect(checkbox_change)

        def uncheckAll() -> None:
            mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            self.num_selected = 0
            for i in range(mainGUI.listWidget_chp_detail.count()):
                if mainGUI.listWidget_chp_detail.item(i).flags() != Qt.NoItemFlags:
                    mainGUI.listWidget_chp_detail.item(i).setCheckState(Qt.Unchecked)
            mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")
            mainGUI.listWidget_chp_detail.itemChanged.connect(checkbox_change)

        def myMenu(pos: QPoint) -> None:
            menu = QMenu()
            menu.addAction("勾选", checkSelected)
            menu.addAction("取消勾选", uncheckSelected)
            menu.addAction("全选", checkAll)
            menu.addAction("取消全选", uncheckAll)
            menu.exec_(mainGUI.listWidget_chp_detail.mapToGlobal(pos))

        mainGUI.listWidget_chp_detail.setContextMenuPolicy(Qt.CustomContextMenu)
        mainGUI.listWidget_chp_detail.customContextMenuRequested.connect(myMenu)

        # ?###########################################################
        # ? 绑定下载选中章节事件
        def _() -> None:
            if self.num_selected == 0:
                return
            logger.info(f"开始下载选中章节, 数量: {self.num_selected}")

            # ?###########################################################
            # ? 更新章节详情界面
            num_num_downloaded = (
                int(mainGUI.label_chp_detail_num_downloaded.text().split("：")[1])
                + self.num_selected
            )
            self.num_selected = 0
            mainGUI.label_chp_detail_num_downloaded.setText(f"已下载：{num_num_downloaded}")
            mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")

            mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            for i in range(mainGUI.listWidget_chp_detail.count()):
                item = mainGUI.listWidget_chp_detail.item(i)
                if item.flags() != Qt.NoItemFlags and item.checkState() == Qt.Checked:
                    mainGUI.downloadUI.addTask(mainGUI, self.epi_list[i])
                    item.setFlags(Qt.NoItemFlags)
                    item.setBackground(QColor(0, 255, 0, 50))
            mainGUI.listWidget_chp_detail.itemChanged.connect(checkbox_change)

            # ?###########################################################
            # ? 更新我的库存界面信息 也就是v_Layout_myLibrary里的章节数量信息
            for i in range(mainGUI.v_Layout_myLibrary.count()):
                temp = mainGUI.v_Layout_myLibrary.itemAt(i).widget().layout()
                if self.epi_list[0].comic_name in temp.itemAt(0).widget().text():
                    temp.itemAt(2).widget().setText(
                        f"{num_num_downloaded}/{len(self.epi_list)}"
                    )
                    break

            # ?###########################################################
            # ？ 跳转到下载界面的tab
            mainGUI.tabWidget.setCurrentIndex(1)
            mainGUI.tabWidget_download_list.setCurrentIndex(0)

        mainGUI.pushButton_chp_detail_download_selected.clicked.connect(_)
