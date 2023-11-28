"""
漫画UI类，用于搜索、下载、管理漫画
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from re import sub
from typing import TYPE_CHECKING

from pypinyin import lazy_pinyin
from PySide6.QtCore import QEvent, QObject, QPoint, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QImage, QIntValidator, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QWidget,
)

from src.BiliPlus import BiliPlusComic
from src.Comic import Comic
from src.SearchComic import SearchComic
from src.Utils import logger, openFileOrDir

if TYPE_CHECKING:
    from src.ui.MainGUI import MainGUI


class MangaUI(QObject):
    """漫画UI类，用于搜索、下载、管理漫画"""

    # ?###########################################################
    # ? 用于多线程更新我的库存
    signal_my_library_add_widget = Signal(dict)

    # ? 用于多线程更新漫画详情
    signal_my_comic_detail_widget = Signal(dict)

    # ? 用于多线程更新封面图
    signal_my_cover_update_widget = Signal(dict)

    # ? 用于多线程刷新漫画章节列表
    signal_my_comic_list_widget = Signal(dict)

    def __init__(self, mainGUI: MainGUI):
        super().__init__()
        self.search_info = None
        self.num_selected = 0
        self.epi_list = None
        self.present_comic_id = 0
        self.mainGUI = mainGUI
        self.init_mangaSearch()
        self.init_mangaDetails()
        self.init_myLibrary()
        self.init_episodesDetails()
        self.init_episodesDownloadSelected()
        self.init_episodesResolve()
        self.executor = ThreadPoolExecutor()

    ############################################################

    def init_mangaSearch(self) -> None:
        """链接搜索漫画功能"""

        def _() -> None:
            if not self.mainGUI.getConfig("cookie"):
                QMessageBox.critical(self.mainGUI, "警告", "请先在设置界面填写自己的Cookie！")
                return
            # ? 如果输入框为空，只有空格，提示用户输入
            if not self.mainGUI.lineEdit_manga_search_name.text().strip():
                QMessageBox.critical(self.mainGUI, "警告", "请输入漫画名！")
                return

            self.search_info = SearchComic(
                self.mainGUI.lineEdit_manga_search_name.text(),
                self.mainGUI.getConfig("cookie"),
            ).getResults(self.mainGUI)
            self.mainGUI.listWidget_manga_search.clear()
            self.mainGUI.label_manga_search.setText(f"{len(self.search_info)}条结果")
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
                self.mainGUI.listWidget_manga_search.addItem(temp)
                self.mainGUI.listWidget_manga_search.setItemWidget(
                    temp,
                    QLabel(
                        f"{item['title']} by <span style='color:blue'>{item['author_name'][0]}</span>"
                    ),
                )

        self.mainGUI.lineEdit_manga_search_name.returnPressed.connect(_)
        self.mainGUI.pushButton_manga_search_name.clicked.connect(_)

    ############################################################
    def init_mangaDetails(self) -> None:
        """绑定漫画详情点击事件"""

        # ?###########################################################
        # ? 单击根据漫画id搜索的漫画详情绑定
        def _() -> None:
            comic_id = self.mainGUI.lineEdit_manga_search_id.text().strip()
            # ? 如果输入框为空，或者不是五位数字，提示用户输入正确的id
            if len(comic_id) < 5:
                QMessageBox.critical(self.mainGUI, "警告", "请输入五位漫画ID！")
                return
            self.present_comic_id = comic_id
            self.resolveEnable(self.mainGUI, "resolving")
            comic = Comic(self.present_comic_id, self.mainGUI)
            self.updateComicInfoEvent(self.mainGUI, comic, "bilibili")

        self.mainGUI.lineEdit_manga_search_id.returnPressed.connect(_)
        self.mainGUI.pushButton_manga_search_id.clicked.connect(_)

        # 漫画id搜索框只能输入数字
        self.mainGUI.lineEdit_manga_search_id.setValidator(QIntValidator())

        # ?###########################################################
        # ? 双击获取选中漫画详情绑定
        def _(item: QListWidgetItem) -> None:
            index = self.mainGUI.listWidget_manga_search.indexFromItem(item).row()
            self.present_comic_id = self.search_info[index]["id"]
            self.resolveEnable(self.mainGUI, "resolving")
            comic = Comic(self.present_comic_id, self.mainGUI)
            self.updateComicInfoEvent(self.mainGUI, comic, "bilibili")

        self.mainGUI.listWidget_manga_search.itemDoubleClicked.connect(_)

        # ?###########################################################
        # ? 单击修改当前选择id绑定
        def _(item: QListWidgetItem) -> None:
            index = self.mainGUI.listWidget_manga_search.indexFromItem(item).row()
            self.present_comic_id = self.search_info[index]["id"]

        self.mainGUI.listWidget_manga_search.itemClicked.connect(_)
        # 鼠标移动到图片上的时候更改鼠标样式, 提示用户可以用鼠标点击
        self.mainGUI.label_manga_image.setCursor(Qt.PointingHandCursor)

        # ?###########################################################
        # ? 漫画封面图更新触发函数绑定
        self.signal_my_cover_update_widget.connect(self.updateComicCover)

        # ?###########################################################
        # ? 漫画解析触发函数绑定
        self.signal_my_comic_detail_widget.connect(self.updateComicInfo)

        # ?###########################################################
        # ? 漫画章节列表更新触发函数绑定
        self.signal_my_comic_list_widget.connect(self.updateComicList)

    ############################################################
    def init_myLibrary(self) -> None:
        """初始化我的库存"""

        # ?###########################################################
        # ? 初始化我的库存漫画元数据
        path = self.mainGUI.getConfig("save_path")

        if os.path.exists(path):
            self.mainGUI.my_library = self.get_meta_dict(path)
        else:
            self.mainGUI.lineEdit_save_path.setText(os.getcwd())
            self.mainGUI.updateConfig("save_path", os.getcwd())

        self.mainGUI.label_myLibrary_count.setText(
            f"我的库存：{len(self.mainGUI.my_library)}部"
        )

        # ?###########################################################
        # ? 绑定更新我的库存事件
        # 布局对齐
        self.mainGUI.v_Layout_myLibrary.setAlignment(Qt.AlignTop)
        self.signal_my_library_add_widget.connect(self.updateMyLibrarySingleAdd)

        def _() -> None:
            if not self.mainGUI.getConfig("cookie"):
                QMessageBox.critical(self.mainGUI, "警告", "请先在设置界面填写自己的Cookie！")
                return
            self.updateMyLibrary()

        self.mainGUI.pushButton_myLibrary_update.clicked.connect(_)

    ############################################################
    # 以下四个函数是为了更新我的库存，是一个整体
    # 拆开的原因主要是为了绕开多线程访问 mainGUI 报错的情况，如下
    # QObject::setParent: Cannot set parent, new parent is in a different thread
    ############################################################

    def updateMyLibrary(self) -> bool:
        """扫描本地并且更新我的库存"""

        # ?###########################################################
        # ? 清理v_Layout_myLibrary里的所有控件
        for i in reversed(range(self.mainGUI.v_Layout_myLibrary.count())):
            to_delete = self.mainGUI.v_Layout_myLibrary.itemAt(i).widget()
            # deleteLater 会有延迟，为了显示效果，先将父控件设为None
            to_delete.setParent(None)
            to_delete.deleteLater()

        # ?###########################################################
        # ? 用多线程解析漫画，并添加漫画到列表
        my_library = self.mainGUI.my_library
        futures = []
        futures.extend(
            self.executor.submit(
                self.updateMyLibrarySingle,
                self.mainGUI,
                comic_id,
                comic_info["comic_path"],
            )
            for comic_id, comic_info in my_library.items()
        )
        self.mainGUI.pushButton_myLibrary_update.setEnabled(False)
        self.mainGUI.label_myLibrary_tip.setText("更新信息中...")
        self.executor.submit(
            self.updateMyLibraryWatcher,
            self.mainGUI,
            futures,
            my_library,
        )

    ############################################################
    def updateMyLibraryWatcher(
        self, mainGUI: MainGUI, futures: list, my_library: dict
    ) -> None:
        if fail_comic := [
            future.result() for future in as_completed(futures) if future.result()
        ]:
            temp = "".join(my_library[i]["comic_name"] + "\n" for i in fail_comic)
            mainGUI.signal_message_box.emit(
                f"以下漫画获取更新多次后失败!\n{temp}\n请检查网络连接或者重启软件\n更多详细信息请查看日志文件, 或联系开发者！"
            )
        else:
            mainGUI.signal_information_box.emit("更新完成！")

        mainGUI.pushButton_myLibrary_update.setEnabled(True)
        mainGUI.pushButton_myLibrary_update.setText("检查更新")
        mainGUI.label_myLibrary_tip.setText("(右键打开文件夹)")

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

        self.signal_my_library_add_widget.emit(info)
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
        def _(_event: QEvent, widget: QWidget, comic: Comic) -> None:
            self.present_comic_id = comic.comic_id
            for i in range(mainGUI.v_Layout_myLibrary.count()):
                temp = mainGUI.v_Layout_myLibrary.itemAt(i).widget()
                temp.setStyleSheet("font-size: 10pt;")
            widget.setStyleSheet(
                "background-color:rgb(200, 200, 255); font-size: 10pt;"
            )

        widget.mousePressEvent = partial(_, widget=widget, comic=comic)
        widget.mouseDoubleClickEvent = partial(
            self.updateComicInfoEvent, mainGUI, comic, "bilibili"
        )
        widget.setLayout(h_layout_my_library)

        # ?###########################################################
        # ? 绑定右键漫画打开文件夹事件
        def myMenu_openFolder(widget: QWidget, comic_path: str, pos: QPoint) -> None:
            menu = QMenu()
            menu.addAction(
                "打开文件夹",
                lambda: openFileOrDir(mainGUI, comic_path),
            )
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
                left_title: str = left[left.find(">") + 1 : left.rfind("<")]
                if i == mainGUI.v_Layout_myLibrary.count() - 1:
                    mainGUI.v_Layout_myLibrary.addWidget(widget)
                    break
                if lazy_pinyin(data["title"]) <= lazy_pinyin(left_title):
                    mainGUI.v_Layout_myLibrary.insertWidget(i, widget)
                    break

    ############################################################
    # 以下三个函数是为了获取漫画信息详情
    ############################################################

    ############################################################
    def updateComicInfoEvent(
        self, mainGUI: MainGUI, comic: Comic, resolve_type: str, _event: QEvent = None
    ) -> None:
        """更新漫画信息详情界面

        Args:
            comic (Comic): 漫画类实例
            mainGUI (MainGUI): 主窗口类实例
            resolve_type (str): 更新的解析类型
        """

        # 用多线程更新漫画信息，避免卡顿
        self.executor.submit(
            self.getComicInfo,
            mainGUI,
            comic,
            resolve_type,
        )

    ############################################################
    def getComicInfo(self, mainGUI: MainGUI, comic: Comic, resolve_type: str) -> None:
        """更新封面的执行函数

        Args:
            mainGUI (MainGUI): 主窗口类实例
            comic (Comic): 获取的漫画实例
            resolve_type (str): 更新的解析类型

        """
        mainGUI.signal_resolve_status.emit("正在解析漫画详情...")
        data = comic.getComicInfo()
        mainGUI.signal_resolve_status.emit("解析漫画详情完毕")
        self.signal_my_comic_detail_widget.emit(
            {
                "mainGUI": mainGUI,
                "comic": comic,
                "data": data,
                "resolve_type": resolve_type,
            }
        )

    ############################################################
    def updateComicInfo(self, info: dict) -> None:
        """更新漫画信息详情回调函数

        Args:
            info (dict): 执行更新漫画信息详情后返回的数据
        """

        mainGUI: MainGUI = info["mainGUI"]
        comic: Comic = info["comic"]
        data: dict = info["data"]
        resolve_type: str = info["resolve_type"]

        self.present_comic_id = comic.comic_id
        # ? 获取漫画信息失败直接跳过
        if not data:
            mainGUI.signal_message_box.emit(
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
        # ? 用多线程获取封面，避免卡顿
        self.executor.submit(self.getComicCover, mainGUI, comic, data)

        # ?###########################################################
        # ? 封面的绑定双击和悬停事件

        mainGUI.label_manga_image.mouseDoubleClickEvent = (
            lambda _event: QDesktopServices.openUrl(
                QUrl(f"https://manga.bilibili.com/detail/mc{data['id']}")
            )
        )
        mainGUI.label_manga_image.setToolTip(
            f"双击打开漫画详情页\nhttps://manga.bilibili.com/detail/mc{data['id']}"
        )

        # ?###########################################################
        # ? 用多线程更新漫画章节详情界面显示，避免卡顿
        self.executor.submit(self.getComicList, mainGUI, comic, resolve_type)

    ############################################################
    # 以下两个函数是为了获取漫画封面
    ############################################################

    ############################################################
    def getComicCover(self, mainGUI: MainGUI, comic: Comic, data: dict) -> None:
        """更新封面的执行函数

        Args:
            mainGUI (MainGUI): 主窗口类实例
            comic (Comic): 获取的漫画实例
            data (dict): 漫画实例的数据

        """
        img_byte = comic.getComicCover(data)
        self.signal_my_cover_update_widget.emit(
            {
                "mainGUI": mainGUI,
                "img_byte": img_byte,
            }
        )

    ############################################################
    def updateComicCover(self, info: dict) -> None:
        """更新封面的回调函数

        Args:
            info (dict): 执行更新封面后返回的数据

        """
        mainGUI: MainGUI = info["mainGUI"]
        img_byte: bytes = info["img_byte"]

        # 重写图片大小改变事件，使图片不会变形
        label_img = QPixmap.fromImage(QImage.fromData(img_byte))

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

    ############################################################
    # 以下两个函数是为了刷新漫画详情界面
    ############################################################

    ############################################################
    def getComicList(self, mainGUI: MainGUI, comic: Comic, resolve_type: str) -> None:
        """更新详情界面的执行函数

        Args:
            mainGUI (MainGUI): 主窗口类实例
            comic (Comic): 获取的漫画实例

        """
        mainGUI.signal_resolve_status.emit("正在解析漫画章节...")
        self.num_selected = 0
        num_unlocked = 0
        if comic:
            self.epi_list = comic.getEpisodesInfo()
        mainGUI.signal_resolve_status.emit("解析漫画章节完毕")
        self.signal_my_comic_list_widget.emit(
            {
                "mainGUI": mainGUI,
                "comic": comic,
                "resolve_type": resolve_type,
                "num_unlocked": num_unlocked,
            }
        )

    ############################################################
    def updateComicList(self, info: dict) -> None:
        """更新漫画详情界面的回调函数

        Args:
            info (dict): 执行更新封面后返回的数据

        """
        mainGUI: MainGUI = info["mainGUI"]
        comic: Comic = info["comic"]
        resolve_type: str = info["resolve_type"]
        num_unlocked: int = info["num_unlocked"]

        # ?###########################################################
        # ? 删除教学文本框
        if self.mainGUI.listWidget_chp_detail.maximumHeight() == 0:
            self.mainGUI.textBrowser_tutorial.deleteLater()
            self.mainGUI.listWidget_chp_detail.setMaximumHeight(16777215)

        # ?###########################################################
        # ? 更新漫画章节详情
        mainGUI.listWidget_chp_detail.clear()
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
        self.resolveEnable(mainGUI, resolve_type)
        mainGUI.signal_resolve_status.emit("")

    ############################################################

    def checkbox_change_callBack(self, item: QListWidgetItem) -> None:
        """章节详情界面的多选框状态改变时的回调函数

        Args:
            item (QListWidgetItem): 被点击的item
        """
        if item.flags() == Qt.NoItemFlags:
            return
        if item.checkState() == Qt.Checked:
            self.num_selected += 1
        elif item.checkState() == Qt.Unchecked:
            self.num_selected -= 1
        self.mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")

    ############################################################

    def init_episodesDetails(self) -> None:
        """绑定章节界面的多选以及右键菜单事件"""

        self.num_selected = 0
        self.mainGUI.listWidget_chp_detail.setDragEnabled(False)

        # ?###########################################################
        # ? 绑定鼠标点击选择信号
        self.mainGUI.listWidget_chp_detail.itemChanged.connect(
            self.checkbox_change_callBack
        )

        def _(item: QListWidgetItem) -> None:
            if item.flags() == Qt.NoItemFlags:
                return
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
            elif item.checkState() == Qt.Unchecked:
                item.setCheckState(Qt.Checked)

        self.mainGUI.listWidget_chp_detail.itemPressed.connect(_)

        # ?###########################################################
        # ? 绑定回车选择信号

        def _(currentItem: QListWidgetItem) -> None:
            checked = (
                Qt.Unchecked if currentItem.checkState() == Qt.Checked else Qt.Checked
            )
            selected_items = self.mainGUI.listWidget_chp_detail.selectedItems()
            for item in selected_items:
                item.setCheckState(checked)

        self.mainGUI.listWidget_chp_detail.itemActivated.connect(_)

        # ?###########################################################
        # ? 绑定更改当前选择项信号
        # 原本想实现按住Ctrl移动方向键进行多个选中，但影响按住Ctrl的鼠标选择，原因不明故注释
        # def _(current: QListWidgetItem, previous: QListWidgetItem) -> None:
        #     if not (self.mainGUI.CtrlPress or self.mainGUI.AltPress):
        #         return
        #     if self.mainGUI.CtrlPress and not self.mainGUI.AltPress:
        #         current.setSelected(True)
        #     if self.mainGUI.CtrlPress and self.mainGUI.AltPress:
        #         previous.setSelected(False)
        # self.mainGUI.listWidget_chp_detail.currentItemChanged.connect(_)

        # ?###########################################################
        # ? 绑定鼠标划过信号

        def _(item: QListWidgetItem) -> None:
            if item.flags() == Qt.NoItemFlags:
                return
            if not self.mainGUI.isFocus or not (
                self.mainGUI.ShiftPress or self.mainGUI.AltPress
            ):
                return
            if self.mainGUI.ShiftPress and self.mainGUI.AltPress:
                item.setCheckState(Qt.Unchecked)
            elif self.mainGUI.AltPress:
                item.setCheckState(Qt.Checked)

        self.mainGUI.listWidget_chp_detail.itemEntered.connect(_)

        # ?###########################################################
        # ? 绑定右键菜单，让用户可以勾选或者全选等

        def checkSelected() -> None:
            self.mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            for item in self.mainGUI.listWidget_chp_detail.selectedItems():
                if item.flags() != Qt.NoItemFlags and item.checkState() == Qt.Unchecked:
                    item.setCheckState(Qt.Checked)
                    self.num_selected += 1
            self.mainGUI.label_chp_detail_num_selected.setText(
                f"已选中：{self.num_selected}"
            )
            self.mainGUI.listWidget_chp_detail.itemChanged.connect(
                self.checkbox_change_callBack
            )

        def uncheckSelected() -> None:
            self.mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            for item in self.mainGUI.listWidget_chp_detail.selectedItems():
                if item.flags() != Qt.NoItemFlags and item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                    self.num_selected -= 1
            self.mainGUI.label_chp_detail_num_selected.setText(
                f"已选中：{self.num_selected}"
            )
            self.mainGUI.listWidget_chp_detail.itemChanged.connect(
                self.checkbox_change_callBack
            )

        def checkAll() -> None:
            self.mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            self.num_selected = 0
            for i in range(self.mainGUI.listWidget_chp_detail.count()):
                if self.mainGUI.listWidget_chp_detail.item(i).flags() != Qt.NoItemFlags:
                    self.mainGUI.listWidget_chp_detail.item(i).setCheckState(Qt.Checked)
                    self.num_selected += 1
            self.mainGUI.label_chp_detail_num_selected.setText(
                f"已选中：{self.num_selected}"
            )
            self.mainGUI.listWidget_chp_detail.itemChanged.connect(
                self.checkbox_change_callBack
            )

        def uncheckAll() -> None:
            self.mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            self.num_selected = 0
            for i in range(self.mainGUI.listWidget_chp_detail.count()):
                if self.mainGUI.listWidget_chp_detail.item(i).flags() != Qt.NoItemFlags:
                    self.mainGUI.listWidget_chp_detail.item(i).setCheckState(
                        Qt.Unchecked
                    )
            self.mainGUI.label_chp_detail_num_selected.setText(
                f"已选中：{self.num_selected}"
            )
            self.mainGUI.listWidget_chp_detail.itemChanged.connect(
                self.checkbox_change_callBack
            )

        def myMenu(pos: QPoint) -> None:
            menu = QMenu()
            menu.addAction("勾选", checkSelected)
            menu.addAction("取消勾选", uncheckSelected)
            menu.addAction("全选", checkAll)
            menu.addAction("取消全选", uncheckAll)
            menu.exec_(self.mainGUI.listWidget_chp_detail.mapToGlobal(pos))

        self.mainGUI.listWidget_chp_detail.setContextMenuPolicy(Qt.CustomContextMenu)
        self.mainGUI.listWidget_chp_detail.customContextMenuRequested.connect(myMenu)

    ############################################################

    def init_episodesResolve(self) -> None:
        """绑定章节界面的解析按钮事件"""

        # ?###########################################################
        # ? 绑定B站解析按钮事件
        def _() -> None:
            if self.present_comic_id == 0:
                QMessageBox.critical(self.mainGUI, "警告", "请先在搜索或库存列表选择一个漫画！")
                return
            if not self.mainGUI.getConfig("cookie"):
                QMessageBox.critical(self.mainGUI, "警告", "请先在设置界面填写自己的Cookie！")
                return
            self.resolveEnable(self.mainGUI, "resolving")
            comic = Comic(self.present_comic_id, self.mainGUI)
            self.updateComicInfoEvent(self.mainGUI, comic, "bilibili")

        self.mainGUI.pushButton_resolve_detail.clicked.connect(_)

        # ?###########################################################
        # ? 绑定BiliPlus解析按钮事件
        def _() -> None:
            if self.present_comic_id == 0:
                QMessageBox.critical(self.mainGUI, "警告", "请先在搜索或库存列表选择一个漫画！")
                return
            if not self.mainGUI.getConfig("biliplus_cookie"):
                QMessageBox.critical(self.mainGUI, "警告", "请先在设置界面填写自己的BiliPlus Cookie！")
                return
            self.resolveEnable(self.mainGUI, "resolving")
            comic = BiliPlusComic(self.present_comic_id, self.mainGUI)
            self.updateComicInfoEvent(self.mainGUI, comic, "biliplus")

        self.mainGUI.pushButton_biliplus_resolve_detail.clicked.connect(_)

    ############################################################

    def init_episodesDownloadSelected(self) -> None:
        """初始化章节详情界面的下载选中章节按钮事件"""

        # ?###########################################################
        # ? 绑定下载选中章节事件
        def _() -> None:
            if self.num_selected == 0:
                return
            logger.info(f"开始下载选中章节, 数量: {self.num_selected}")

            # ?###########################################################
            # ? 更新章节详情界面
            num_downloaded = (
                int(self.mainGUI.label_chp_detail_num_downloaded.text().split("：")[1])
                + self.num_selected
            )
            self.num_selected = 0
            self.mainGUI.label_chp_detail_num_downloaded.setText(
                f"已下载：{num_downloaded}"
            )
            self.mainGUI.label_chp_detail_num_selected.setText(
                f"已选中：{self.num_selected}"
            )

            # ?###########################################################
            # ? 初始化储存文件夹
            save_path = self.epi_list[0].save_path
            if not os.path.exists(save_path):
                os.makedirs(save_path)

            # ?###########################################################
            # ? 保存元数据
            if not os.path.exists(os.path.join(save_path, "元数据.json")):
                comic = Comic(self.present_comic_id, self.mainGUI)
                self.save_meta(comic.getComicInfo())

            # ?###########################################################
            # ? 开始下载选中章节
            self.mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            for i in range(self.mainGUI.listWidget_chp_detail.count()):
                item = self.mainGUI.listWidget_chp_detail.item(i)
                if item.flags() != Qt.NoItemFlags and item.checkState() == Qt.Checked:
                    comic = Comic(self.present_comic_id, self.mainGUI)
                    self.mainGUI.downloadUI.addTask(self.mainGUI, self.epi_list[i])
                    item.setFlags(Qt.NoItemFlags)
                    item.setBackground(QColor(0, 255, 0, 50))
            self.mainGUI.listWidget_chp_detail.itemChanged.connect(
                self.checkbox_change_callBack
            )

            # ?###########################################################
            # ? 更新我的库存界面信息 也就是v_Layout_myLibrary里的章节数量信息
            for i in range(self.mainGUI.v_Layout_myLibrary.count()):
                temp = self.mainGUI.v_Layout_myLibrary.itemAt(i).widget().layout()
                if self.epi_list[0].comic_name in temp.itemAt(0).widget().text():
                    temp.itemAt(2).widget().setText(
                        f"{num_downloaded}/{len(self.epi_list)}"
                    )
                    break

            # ?###########################################################
            # ？ 跳转到下载界面的tab
            self.mainGUI.tabWidget.setCurrentIndex(1)
            self.mainGUI.tabWidget_download_list.setCurrentIndex(0)

        self.mainGUI.pushButton_chp_detail_download_selected.clicked.connect(_)
        self.mainGUI.pushButton_biliplus_detail_download_selected.clicked.connect(_)

    ###########################################################

    def resolveEnable(self, mainGUI: MainGUI, resolve_type: str) -> None:
        # sourcery skip: extract-duplicate-method, switch
        """根据解析状态对按钮进行允许和禁用状态的改变

        Args:
            mainGUI (MainGUI): 主窗口类实例
            resolve_type (str): 解析状态
        """
        if resolve_type == "resolving":
            mainGUI.pushButton_resolve_detail.setEnabled(False)
            mainGUI.pushButton_biliplus_resolve_detail.setEnabled(False)
            mainGUI.pushButton_chp_detail_download_selected.setEnabled(False)
            mainGUI.pushButton_biliplus_detail_download_selected.setEnabled(False)
        else:
            mainGUI.pushButton_resolve_detail.setEnabled(True)
            mainGUI.pushButton_biliplus_resolve_detail.setEnabled(True)

        if resolve_type == "bilibili":
            mainGUI.pushButton_chp_detail_download_selected.setEnabled(True)
            mainGUI.pushButton_biliplus_detail_download_selected.setEnabled(False)
        elif resolve_type == "biliplus":
            mainGUI.pushButton_chp_detail_download_selected.setEnabled(False)
            mainGUI.pushButton_biliplus_detail_download_selected.setEnabled(True)

    ############################################################

    def save_meta(self, data: dict) -> None:
        """保存元数据

        Args:
            mainGUI (MainGUI): 主窗口类实例
            data (dict): 漫画元数据

        """

        meta = {
            "id": data["id"],
            "title": data["title"],
            "horizontal_cover": data["horizontal_cover"],
            "square_cover": data["square_cover"],
            "vertical_cover": data["vertical_cover"],
            "author_name": data["author_name"],
            "styles": data["styles"],
            "evaluate": data["evaluate"],
            "renewal_time": data["renewal_time"],
            "hall_icon_text": data["hall_icon_text"],
            "tags": [tag["name"] for tag in data["tags"]],
        }

        with open(
            os.path.join(data["save_path"], "元数据.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(meta, f, indent=4, ensure_ascii=False)

    ############################################################

    def get_meta_dict(self, path: str) -> dict:
        """读取指定库存目录下所有子漫画文件夹的元数据并返回

        Args:
            mainGUI (MainGUI): 主窗口类实例
            data (dict): 漫画元数据

        """
        meta_dict = {}
        try:
            for item in os.listdir(path):
                if os.path.exists(os.path.join(path, item, "元数据.json")):
                    with open(
                        os.path.join(path, item, "元数据.json"), "r", encoding="utf-8"
                    ) as f:
                        comic_path = os.path.join(path, item)
                        data = json.load(f)
                        meta_dict[data["id"]] = {
                            "comic_name": data["title"],
                            "comic_path": comic_path,
                        }
        except Exception as e:
            logger.error(f"读取元数据时发生错误\n {e}")
        return meta_dict

