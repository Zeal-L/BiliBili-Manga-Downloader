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

    # ? 用于多线程刷新漫画章节信息
    signal_episode_info_update_widget = Signal(dict)

    # ? 用于多线程刷新漫画章节列表
    signal_episode_list_update_widget = Signal(dict)

    def __init__(self, mainGUI: MainGUI):
        super().__init__()
        self.search_info = None
        self.num_selected = 0
        self.epi_list = []
        self.present_comic_id = 0
        self.mainGUI = mainGUI
        self.executor = ThreadPoolExecutor()
        self.init_mangaSearch()
        self.init_mangaDetails()
        self.init_myLibrary()
        self.init_episodesDetails()
        self.init_episodesDownloadSelected()
        self.init_episodesResolve()

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
            self.resolveEnable(False)
            comic = BiliPlusComic(self.present_comic_id, self.mainGUI)
            self.updateComicInfoEvent(comic)

        self.mainGUI.lineEdit_manga_search_id.returnPressed.connect(_)
        self.mainGUI.pushButton_manga_search_id.clicked.connect(_)

        # 漫画id搜索框只能输入数字
        self.mainGUI.lineEdit_manga_search_id.setValidator(QIntValidator())

        # ?###########################################################
        # ? 双击获取选中漫画详情绑定
        def _(item: QListWidgetItem) -> None:
            index = self.mainGUI.listWidget_manga_search.indexFromItem(item).row()
            self.present_comic_id = self.search_info[index]["id"]
            self.resolveEnable(False)
            comic = Comic(self.present_comic_id, self.mainGUI)
            self.updateComicInfoEvent(comic)

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
        self.signal_episode_info_update_widget.connect(self.updateEpisodeInfo)
        self.signal_episode_list_update_widget.connect(self.updateEpisodeList)

    ############################################################
    def init_myLibrary(self) -> None:
        """初始化我的库存"""

        # ?###########################################################
        # ? 检测cookie有效性并初始化我的库存漫画元数据
        stored_cookie = self.mainGUI.getConfig("cookie")

        def _() -> None:
            self.mainGUI.lineEdit_my_cookie.setEnabled(False)
            self.mainGUI.pushButton_my_cookie.setEnabled(False)
            if self.mainGUI.settingUI.check_cookie_valid(stored_cookie):
                self.updateMyLibrary()

        self.readMyLibrary()
        if stored_cookie:
            self.executor.submit(_)

        # ?###########################################################
        # ? 绑定更新我的库存事件
        # 布局对齐
        self.mainGUI.v_Layout_myLibrary.setAlignment(Qt.AlignTop)
        self.signal_my_library_add_widget.connect(self.updateMyLibrarySingleAdd)

        def _() -> None:
            if not self.mainGUI.getConfig("cookie"):
                QMessageBox.critical(self.mainGUI, "警告", "请先在设置界面填写自己的Cookie！")
                return
            self.readMyLibrary()
            self.updateMyLibrary(notice=True)

        self.mainGUI.pushButton_myLibrary_update.clicked.connect(_)

    ############################################################
    # 以下五个函数是为了更新我的库存，是一个整体
    # 拆开的原因主要是为了绕开多线程访问 mainGUI 报错的情况，如下
    # QObject::setParent: Cannot set parent, new parent is in a different thread
    ############################################################

    def readMyLibrary(self) -> None:
        """读取我的库存漫画元数据"""

        path = self.mainGUI.getConfig("save_path")

        if os.path.exists(path):
            self.mainGUI.my_library = self.get_meta_dict(path)
        else:
            self.mainGUI.lineEdit_save_path.setText(os.getcwd())
            self.mainGUI.updateConfig("save_path", os.getcwd())

        self.mainGUI.label_myLibrary_count.setText(f"我的库存：{len(self.mainGUI.my_library)}部")

    ############################################################
    def updateMyLibrary(self, notice: bool = False) -> bool:
        """扫描本地并且更新我的库存

        Args:
            notice (bool): 更新完毕是否弹窗提示
        """

        # ?###########################################################
        # ? 清理v_Layout_myLibrary里的所有控件
        for i in reversed(range(self.mainGUI.v_Layout_myLibrary.count())):
            to_delete = self.mainGUI.v_Layout_myLibrary.itemAt(i).widget()
            # deleteLater 会有延迟，为了显示效果，先将父控件设为None
            to_delete.setParent(None)
            to_delete.deleteLater()

        # ?###########################################################
        # ? 用多线程解析漫画，并添加漫画到列表
        futures = []
        futures.extend(
            self.executor.submit(
                self.updateMyLibrarySingle,
                comic_id,
                comic_info["comic_path"],
            )
            for comic_id, comic_info in self.mainGUI.my_library.items()
        )
        self.mainGUI.pushButton_myLibrary_update.setEnabled(False)
        self.mainGUI.label_myLibrary_tip.setText("更新信息中...")
        self.executor.submit(
            self.updateMyLibraryWatcher,
            futures,
            notice,
        )

    ############################################################
    def updateMyLibraryWatcher(self, futures: list, notice: bool) -> None:
        """监控我的库存是否更新完毕，并处理后续步骤

        Args:
            futures (list): 解析漫画的线程列表
            notice (bool): 更新完毕是否弹窗提示
        """

        if fail_comic := [future.result() for future in as_completed(futures) if future.result()]:
            temp = "".join(self.mainGUI.my_library[i]["comic_name"] + "\n" for i in fail_comic)
            self.mainGUI.signal_message_box.emit(
                f"以下漫画获取更新多次后失败!\n{temp}\n请检查网络连接或者重启软件\n更多详细信息请查看日志文件, 或联系开发者！"
            )
        elif notice:
            self.mainGUI.signal_information_box.emit("更新完成！")

        self.mainGUI.pushButton_myLibrary_update.setEnabled(True)
        self.mainGUI.pushButton_myLibrary_update.setText("检查更新")
        self.mainGUI.label_myLibrary_tip.setText("(右键打开文件夹)")

    ############################################################
    def updateMyLibrarySingle(self, comic_id: int, comic_path: str) -> int | None:
        """添加单个漫画到我的库存

        Args:
            comic_id (int): 漫画ID
            comic_path (str): 漫画保存路径
        """

        comic = Comic(comic_id, self.mainGUI)
        data = comic.getComicInfo()
        # ? 获取漫画信息失败直接跳过
        if not data:
            return comic_id
        epi_list = comic.getEpisodesInfo()

        info = {
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
        h_layout_my_library.addWidget(QLabel(f"{comic.getNumDownloaded()}/{len(epi_list)}"))

        widget = QWidget()
        widget.setStyleSheet("font-size: 10pt;")

        # ?###########################################################
        # ? 绑定列表内漫画被点击事件：当前点击变色，剩余恢复
        def _(_event: QEvent, widget: QWidget, comic: Comic) -> None:
            self.present_comic_id = comic.comic_id
            for i in range(self.mainGUI.v_Layout_myLibrary.count()):
                temp = self.mainGUI.v_Layout_myLibrary.itemAt(i).widget()
                temp.setStyleSheet("font-size: 10pt;")
            widget.setStyleSheet("background-color:rgb(200, 200, 255); font-size: 10pt;")

        widget.mousePressEvent = partial(_, widget=widget, comic=comic)
        widget.mouseDoubleClickEvent = partial(self.updateComicInfoEvent, comic)
        widget.setLayout(h_layout_my_library)

        # ?###########################################################
        # ? 绑定右键漫画打开文件夹事件
        def myMenu_openFolder(widget: QWidget, comic_path: str, pos: QPoint) -> None:
            menu = QMenu()
            menu.addAction(
                "打开文件夹",
                lambda: openFileOrDir(self.mainGUI, comic_path),
            )
            menu.exec_(widget.mapToGlobal(pos))

        widget.setContextMenuPolicy(Qt.CustomContextMenu)
        widget.customContextMenuRequested.connect(partial(myMenu_openFolder, widget, comic_path))

        # ? 按照标题的拼音顺序插入我的库存列表
        if self.mainGUI.v_Layout_myLibrary.count() == 0:
            self.mainGUI.v_Layout_myLibrary.addWidget(widget)
        else:
            for i in range(self.mainGUI.v_Layout_myLibrary.count()):
                left: str = (
                    self.mainGUI.v_Layout_myLibrary.itemAt(i).widget().findChild(QLabel).text()
                )
                left_title: str = left[left.find(">") + 1 : left.rfind("<")]
                if i == self.mainGUI.v_Layout_myLibrary.count() - 1:
                    self.mainGUI.v_Layout_myLibrary.addWidget(widget)
                    break
                if lazy_pinyin(data["title"]) <= lazy_pinyin(left_title):
                    self.mainGUI.v_Layout_myLibrary.insertWidget(i, widget)
                    break

    ############################################################
    # 以下三个函数是为了获取漫画信息详情
    ############################################################

    def updateComicInfoEvent(self, comic: Comic, _event: QEvent = None) -> None:
        """更新漫画信息详情界面

        Args:
            comic (Comic): 漫画类实例
        """

        if self.mainGUI.label_resolve_status.text() == "":
            # 用多线程更新漫画信息，避免卡顿
            self.executor.submit(
                self.getComicInfo,
                comic,
            )

    ############################################################
    def getComicInfo(self, comic: Comic) -> None:
        """更新封面的执行函数

        Args:
            comic (Comic): 获取的漫画实例

        """

        self.mainGUI.signal_resolve_status.emit("正在解析漫画详情...")
        data = comic.getComicInfo()
        self.signal_my_comic_detail_widget.emit(
            {
                "mainGUI": self.mainGUI,
                "comic": comic,
                "data": data,
            }
        )

    ############################################################
    def updateComicInfo(self, info: dict) -> None:
        """更新漫画信息详情回调函数

        Args:
            info (dict): 执行更新漫画信息详情后返回的数据
        """

        comic: Comic = info["comic"]
        data: dict = info["data"]

        self.present_comic_id = comic.comic_id
        # ? 获取漫画信息失败直接跳过
        if not data:
            self.mainGUI.signal_message_box.emit(
                "重复获取漫画信息多次后失败!\n请检查网络连接或者重启软件!\n\n更多详细信息请查看日志文件, 或联系开发者！"
            )
            self.resolveEnable(True)
            self.mainGUI.signal_resolve_status.emit("")
            return
        self.mainGUI.label_manga_title.setText(
            "<span style='color:blue;font-weight:bold'>标题：</span>" + data["title"]
        )
        self.mainGUI.label_manga_author.setText(
            "<span style='color:blue;font-weight:bold'>作者：</span>" + data["author_name"]
        )
        self.mainGUI.label_manga_style.setText(
            f"<span style='color:blue;font-weight:bold'>标签：</span>{data['styles'] or '无'}"
        )
        self.mainGUI.label_manga_isFinish.setText(
            f"<span style='color:blue;font-weight:bold'>状态：</span>{'已完结' if data['is_finish'] else '连载中'}"
        )
        self.mainGUI.label_manga_outline.setText(
            f"<span style='color:blue;font-weight:bold'>概要：</span>{data['evaluate'] or '无'}"
        )

        # ?###########################################################
        # ? 用多线程获取封面，避免卡顿
        self.executor.submit(self.getComicCover, comic, data)

        # ?###########################################################
        # ? 封面的绑定双击和悬停事件

        self.mainGUI.label_manga_image.mouseDoubleClickEvent = (
            lambda _event: QDesktopServices.openUrl(
                QUrl(f"https://manga.bilibili.com/detail/mc{data['id']}")
            )
        )
        self.mainGUI.label_manga_image.setToolTip(
            f"双击打开漫画详情页\nhttps://manga.bilibili.com/detail/mc{data['id']}"
        )

        # ?###########################################################
        # ? 用多线程更新漫画章节详情界面显示，避免卡顿
        self.executor.submit(self.getEpisodeList, comic)

    ############################################################
    # 以下两个函数是为了获取漫画封面
    ############################################################

    ############################################################
    def getComicCover(self, comic: Comic, data: dict) -> None:
        """更新封面的执行函数

        Args:
            comic (Comic): 获取的漫画实例
            data (dict): 漫画实例的数据

        """

        img_byte = comic.getComicCover(data)
        self.signal_my_cover_update_widget.emit(
            {
                "img_byte": img_byte,
            }
        )

    ############################################################
    def updateComicCover(self, info: dict) -> None:
        """更新封面的回调函数

        Args:
            info (dict): 执行更新封面后返回的数据

        """

        img_byte: bytes = info["img_byte"]

        # 重写图片大小改变事件，使图片不会变形
        label_img = QPixmap.fromImage(QImage.fromData(img_byte))

        def _(event: QEvent = None) -> None:
            new_size = event.size() if event else self.mainGUI.label_manga_image.size()
            if new_size.width() < 200:
                new_size.setWidth(200)
            img = label_img.scaled(
                new_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.mainGUI.label_manga_image.setPixmap(img)
            self.mainGUI.label_manga_image.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.mainGUI.label_manga_image.resizeEvent = _
        _()

    ############################################################
    def getEpisodeList(self, comic: Comic) -> None:
        """更新漫画详情的执行函数

        Args:
            comic (Comic): 获取的漫画实例

        """

        self.mainGUI.signal_resolve_status.emit("正在解析漫画章节...")
        self.num_selected = 0
        num_unlocked = 0
        if comic:
            self.epi_list = comic.getEpisodesInfo()
        self.mainGUI.signal_resolve_status.emit("正在处理章节详情...")

        # ?###########################################################
        # ? 分析章节信息
        # 清除历史章节列表
        self.signal_episode_list_update_widget.emit({})
        # 丝滑插入章节
        for epi in self.epi_list:
            title = epi.title
            check_state = Qt.CheckState.Unchecked
            flags = (
                Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsDragEnabled
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
            )
            background = QColor(0, 0, 0, 0)

            if epi.isDownloaded():
                flags = Qt.ItemFlag.NoItemFlags
                check_state = Qt.CheckState.Checked
                background = QColor(0, 255, 0, 50)
            if not epi.isAvailable():
                flags = Qt.ItemFlag.NoItemFlags
            else:
                num_unlocked += 1

            self.signal_episode_list_update_widget.emit(
                {
                    "title": title,
                    "check_state": check_state,
                    "background": background,
                    "flags": flags,
                }
            )

        self.signal_episode_info_update_widget.emit(
            {
                "comic": comic,
                "num_unlocked": num_unlocked,
            }
        )

    ############################################################
    def updateEpisodeInfo(self, info: dict) -> None:
        """更新漫画详情的回调函数

        Args:
            info (dict): 执行更新漫画详情后返回的数据

        """

        comic: Comic = info["comic"]
        num_unlocked: int = info["num_unlocked"]

        # ?###########################################################
        # ? 删除教学文本框
        if self.mainGUI.listWidget_chp_detail.maximumHeight() == 0:
            self.mainGUI.textBrowser_tutorial.deleteLater()
            self.mainGUI.listWidget_chp_detail.setMaximumHeight(16777215)

        # ?###########################################################
        # ? 各种章节数与状态显示的更新
        self.mainGUI.label_chp_detail_total_chp.setText(f"总章数：{len(self.epi_list)}")
        self.mainGUI.label_chp_detail_num_unlocked.setText(f"已解锁：{num_unlocked}")
        self.mainGUI.label_chp_detail_num_downloaded.setText(f"已下载：{comic.getNumDownloaded()}")
        self.mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")
        self.resolveEnable(True)
        self.mainGUI.signal_resolve_status.emit("")

    ############################################################
    def updateEpisodeList(self, info: dict) -> None:
        """插入漫画列表章节的回调函数

        Args:
            info (dict): 执行分析章节信息后返回的数据

        """

        if not info:
            self.mainGUI.listWidget_chp_detail.clear()
            return
        title: str = info["title"]
        check_state: Qt.CheckState = info["check_state"]
        background: QColor = info["background"]
        flags: Qt.ItemFlag = info["flags"]

        # ?###########################################################
        # ? 生成章节元素
        widget = QListWidgetItem(title)
        widget.setToolTip(title)
        widget.setFlags(flags)
        widget.setCheckState(check_state)
        widget.setBackground(background)
        widget.setSizeHint(QSize(160, 20))
        widget.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
        self.mainGUI.listWidget_chp_detail.addItem(widget)

    ############################################################

    def checkbox_change_callBack(self, item: QListWidgetItem) -> None:
        """章节详情界面的多选框状态改变时的回调函数

        Args:
            item (QListWidgetItem): 被点击的item
        """

        if item.flags() == Qt.ItemFlag.NoItemFlags:
            return
        if item.checkState() == Qt.CheckState.Checked:
            self.num_selected += 1
        elif item.checkState() == Qt.CheckState.Unchecked:
            self.num_selected -= 1
        self.mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")

    ############################################################

    def init_episodesDetails(self) -> None:
        """绑定章节界面的多选以及右键菜单事件"""

        self.num_selected = 0
        self.mainGUI.listWidget_chp_detail.setDragEnabled(False)

        # ?###########################################################
        # ? 绑定鼠标点击选择信号
        self.mainGUI.listWidget_chp_detail.itemChanged.connect(self.checkbox_change_callBack)

        def _(item: QListWidgetItem) -> None:
            if item.flags() == Qt.ItemFlag.NoItemFlags:
                return
            if item.checkState() == Qt.CheckState.Checked:
                item.setCheckState(Qt.CheckState.Unchecked)
            elif item.checkState() == Qt.CheckState.Unchecked:
                item.setCheckState(Qt.CheckState.Checked)

        self.mainGUI.listWidget_chp_detail.itemPressed.connect(_)

        # ?###########################################################
        # ? 绑定回车选择信号

        def _(currentItem: QListWidgetItem) -> None:
            checked = (
                Qt.CheckState.Unchecked
                if currentItem.checkState() == Qt.CheckState.Checked
                else Qt.CheckState.Checked
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
            if item.flags() == Qt.ItemFlag.NoItemFlags:
                return
            if not self.mainGUI.isFocus or not (self.mainGUI.ShiftPress or self.mainGUI.AltPress):
                return
            if self.mainGUI.ShiftPress and self.mainGUI.AltPress:
                item.setCheckState(Qt.CheckState.Unchecked)
            elif self.mainGUI.AltPress:
                item.setCheckState(Qt.CheckState.Checked)

        self.mainGUI.listWidget_chp_detail.itemEntered.connect(_)

        # ?###########################################################
        # ? 绑定右键菜单，让用户可以勾选或者全选等

        def checkSelected() -> None:
            self.mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            for item in self.mainGUI.listWidget_chp_detail.selectedItems():
                if (
                    item.flags() != Qt.ItemFlag.NoItemFlags
                    and item.checkState() == Qt.CheckState.Unchecked
                ):
                    item.setCheckState(Qt.CheckState.Checked)
                    self.num_selected += 1
            self.mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")
            self.mainGUI.listWidget_chp_detail.itemChanged.connect(self.checkbox_change_callBack)

        def uncheckSelected() -> None:
            self.mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            for item in self.mainGUI.listWidget_chp_detail.selectedItems():
                if (
                    item.flags() != Qt.ItemFlag.NoItemFlags
                    and item.checkState() == Qt.CheckState.Checked
                ):
                    item.setCheckState(Qt.CheckState.Unchecked)
                    self.num_selected -= 1
            self.mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")
            self.mainGUI.listWidget_chp_detail.itemChanged.connect(self.checkbox_change_callBack)

        def checkAll() -> None:
            self.mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            self.num_selected = 0
            for i in range(self.mainGUI.listWidget_chp_detail.count()):
                if self.mainGUI.listWidget_chp_detail.item(i).flags() != Qt.ItemFlag.NoItemFlags:
                    self.mainGUI.listWidget_chp_detail.item(i).setCheckState(Qt.CheckState.Checked)
                    self.num_selected += 1
            self.mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")
            self.mainGUI.listWidget_chp_detail.itemChanged.connect(self.checkbox_change_callBack)

        def uncheckAll() -> None:
            self.mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            self.num_selected = 0
            for i in range(self.mainGUI.listWidget_chp_detail.count()):
                if self.mainGUI.listWidget_chp_detail.item(i).flags() != Qt.ItemFlag.NoItemFlags:
                    self.mainGUI.listWidget_chp_detail.item(i).setCheckState(
                        Qt.CheckState.Unchecked
                    )
            self.mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")
            self.mainGUI.listWidget_chp_detail.itemChanged.connect(self.checkbox_change_callBack)

        def myMenu(pos: QPoint) -> None:
            menu = QMenu()
            menu.addAction("勾选", checkSelected)
            menu.addAction("取消勾选", uncheckSelected)
            menu.addAction("全选", checkAll)
            menu.addAction("取消全选", uncheckAll)
            menu.exec_(self.mainGUI.listWidget_chp_detail.mapToGlobal(pos))

        self.mainGUI.listWidget_chp_detail.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
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
            self.resolveEnable(False)
            comic = Comic(self.present_comic_id, self.mainGUI)
            self.updateComicInfoEvent(comic)

        self.mainGUI.pushButton_resolve_detail.clicked.connect(_)

        # ?###########################################################
        # ? 绑定BiliPlus解析按钮事件
        def _() -> None:
            if self.present_comic_id == 0:
                QMessageBox.critical(self.mainGUI, "警告", "请先在搜索或库存列表选择一个漫画！")
                return
            if not self.mainGUI.getConfig("biliplus_cookie"):
                QMessageBox.critical(
                    self.mainGUI, "警告", "请先在设置界面填写自己的BiliPlus Cookie！"
                )
                return
            self.resolveEnable(False)
            comic = BiliPlusComic(self.present_comic_id, self.mainGUI)
            self.updateComicInfoEvent(comic)

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
            self.mainGUI.label_chp_detail_num_downloaded.setText(f"已下载：{num_downloaded}")
            self.mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.num_selected}")

            # ?###########################################################
            # ? 初始化储存文件夹
            save_path = self.epi_list[0].save_path
            if not os.path.exists(save_path):
                os.makedirs(save_path)

            # ?###########################################################
            # ? 保存元数据
            if self.mainGUI.getConfig("save_meta") and not os.path.exists(
                os.path.join(save_path, "元数据.json")
            ):
                comic = BiliPlusComic(self.present_comic_id, self.mainGUI)
                self.save_meta(comic.getComicInfo())

            # ?###########################################################
            # ? 开始下载选中章节
            self.mainGUI.listWidget_chp_detail.itemChanged.disconnect()
            for i in range(self.mainGUI.listWidget_chp_detail.count()):
                item = self.mainGUI.listWidget_chp_detail.item(i)
                if (
                    item.flags() != Qt.ItemFlag.NoItemFlags
                    and item.checkState() == Qt.CheckState.Checked
                ):
                    comic = BiliPlusComic(self.present_comic_id, self.mainGUI)
                    self.mainGUI.downloadUI.addTask(self.mainGUI, self.epi_list[i])
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    item.setBackground(QColor(0, 255, 0, 50))
            self.mainGUI.listWidget_chp_detail.itemChanged.connect(self.checkbox_change_callBack)

            # ?###########################################################
            # ? 更新我的库存界面信息 也就是v_Layout_myLibrary里的章节数量信息
            for i in range(self.mainGUI.v_Layout_myLibrary.count()):
                temp = self.mainGUI.v_Layout_myLibrary.itemAt(i).widget().layout()
                if self.epi_list[0].comic_name in temp.itemAt(0).widget().text():
                    temp.itemAt(2).widget().setText(f"{num_downloaded}/{len(self.epi_list)}")
                    break

            # ?###########################################################
            # ？ 跳转到下载界面的tab
            self.mainGUI.tabWidget.setCurrentIndex(1)
            self.mainGUI.tabWidget_download_list.setCurrentIndex(0)

        self.mainGUI.pushButton_chp_detail_download_selected.clicked.connect(_)

    ###########################################################

    def resolveEnable(self, enable: bool) -> None:
        """根据解析状态对按钮进行允许和禁用状态的改变

        Args:
            enable (str): 是否允许解析
        """
        if enable:
            self.mainGUI.pushButton_resolve_detail.setEnabled(True)
            self.mainGUI.pushButton_biliplus_resolve_detail.setEnabled(True)
            self.mainGUI.pushButton_chp_detail_download_selected.setEnabled(True)
        else:
            self.mainGUI.pushButton_resolve_detail.setEnabled(False)
            self.mainGUI.pushButton_biliplus_resolve_detail.setEnabled(False)
            self.mainGUI.pushButton_chp_detail_download_selected.setEnabled(False)

    ############################################################

    def save_meta(self, data: dict) -> None:
        """保存元数据

        Args:
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

        with open(os.path.join(data["save_path"], "元数据.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4, ensure_ascii=False)

    ############################################################

    def get_meta_dict(self, path: str) -> dict:
        """读取指定库存目录下所有子漫画文件夹的元数据并返回

        Args:
            path (str): 库存目录路径

        """

        meta_dict = {}
        try:
            for item in os.listdir(path):
                if os.path.exists(os.path.join(path, item, "元数据.json")):
                    with open(os.path.join(path, item, "元数据.json"), "r", encoding="utf-8") as f:
                        comic_path = os.path.join(path, item)
                        data = json.load(f)
                        meta_dict[data["id"]] = {
                            "comic_name": data["title"],
                            "comic_path": comic_path,
                        }
        except (OSError, ValueError) as e:
            logger.error(f"读取元数据时发生错误\n {e}")
        return meta_dict
