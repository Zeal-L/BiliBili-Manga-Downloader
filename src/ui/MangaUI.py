
import os
import re
from functools import partial

import requests
from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QImage, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidgetItem,
                               QMessageBox, QWidget, QMenu)

from src.Comic import Comic
from src.searchComic import SearchComic
from src.utils import *

class MangaUI(): 
    def __init__(self, mainGUI): 
        self.init_mangaSearch(mainGUI)
        self.init_mangaDetails(mainGUI)
        self.init_myLibrary(mainGUI)
        self.init_episodesDetails(mainGUI)
    
    ############################################################
    # 链接搜索漫画功能
    ############################################################
    def init_mangaSearch(self, mainGUI):
        def _():
            if not mainGUI.getConfig("cookie"):
                QMessageBox.critical(mainGUI, "Critical",  "请先在设置界面填写自己的Cookie！")
                return
                
            self.searchInfo = SearchComic(mainGUI.logger, mainGUI.lineEdit_manga_search_name.text(), mainGUI.getConfig("cookie")).getResults()['data']['list']
            mainGUI.listWidget_manga_search.clear()
            mainGUI.label_manga_search.setText(f"找到：{len(self.searchInfo)}条结果")
            for item in self.searchInfo:
                #?###########################################################
                #? 替换爬取信息里的html标签
                item['title'] = re.sub(r'</[^>]+>', '</span>', item['title'])
                item['title'] = re.sub(r'<[^/>]+>', '<span style="color:red;font-weight:bold">', item['title'])
                temp = QListWidgetItem()
                mainGUI.listWidget_manga_search.addItem(temp)
                mainGUI.listWidget_manga_search.setItemWidget(temp, QLabel(f"{item['title']} by <span style='color:blue'>{item['author_name'][0]}</span>"))
        mainGUI.lineEdit_manga_search_name.returnPressed.connect(_)
        mainGUI.pushButton_manga_search_name.clicked.connect(_)
    
    ############################################################
    # 绑定双击显示漫画详情事件
    ############################################################
    def init_mangaDetails(self, mainGUI):
        def _(item):
            index = mainGUI.listWidget_manga_search.indexFromItem(item).row()
            comic = Comic(mainGUI.logger, self.searchInfo[index]['id'], mainGUI.getConfig("cookie"), mainGUI.getConfig("save_path"), mainGUI.getConfig("num_thread"))
            self.updateComicInfo(comic, mainGUI)

        mainGUI.listWidget_manga_search.itemDoubleClicked.connect(_)
    
    ############################################################
    # 初始化我的库存
    ############################################################
    def init_myLibrary(self, mainGUI):
        
        self.UpdateMyLibrary(mainGUI)
        def _():
            self.UpdateMyLibrary(mainGUI)
            QMessageBox.information(mainGUI, "通知",  "更新完成！")
        mainGUI.pushButton_myLibrary_update.clicked.connect(_)
        
        
    ############################################################
    # 更新我的库存
    ############################################################
    def UpdateMyLibrary(self, mainGUI):
        #?###########################################################
        #? 清理v_Layout_myLibrary里的所有控件
        for i in reversed(range(mainGUI.v_Layout_myLibrary.count())):
            mainGUI.v_Layout_myLibrary.itemAt(i).widget().setParent(None)
        
        #?###########################################################
        #? 读取本地库存
        path = mainGUI.getConfig("save_path")
        myLibrary = []
        for item in os.listdir(path):
            if re.search(r'ID-\d+', item):
                myLibrary.append(int(re.search(r'ID-(\d+)', item)[1]))
        mainGUI.label_myLibrary_count.setText(f"我的库存：{len(myLibrary)}部")
        
        #?###########################################################
        #? 添加漫画
        for id in myLibrary:
            comic = Comic(mainGUI.logger, id, mainGUI.getConfig("cookie"), mainGUI.getConfig("save_path"), mainGUI.getConfig("num_thread"))
            data = comic.getComicInfo()
            epiList = comic.getEpisodeInfo()
            h_Layout_myLibrary = QHBoxLayout()
            h_Layout_myLibrary.addWidget(QLabel(f"<span style='color:blue;font-weight:bold'>{data['title']}</span> by {data['author_name']}"))
            h_Layout_myLibrary.addStretch(1)
            h_Layout_myLibrary.addWidget(QLabel(f"{comic.getNumDownloaded()}/{len(epiList)}"))
            
            widget = QWidget()
            widget.setStyleSheet("font-size: 10pt;")

            #?###########################################################
            #? 绑定点击事件
            def _(event, widget: QWidget):
                for i in range(mainGUI.v_Layout_myLibrary.count()):
                    temp = mainGUI.v_Layout_myLibrary.itemAt(i).widget()
                    temp.setStyleSheet("font-size: 10pt;")
                
                widget.setStyleSheet("background-color:rgb(200, 200, 255); font-size: 10pt;")
            widget.mousePressEvent = partial(_, widget=widget)
            widget.mouseDoubleClickEvent = partial(self.updateComicInfo, comic, mainGUI)
            widget.setLayout(h_Layout_myLibrary)
            mainGUI.v_Layout_myLibrary.addWidget(widget)
            
    ############################################################
    # 更新漫画信息详情界面
    ############################################################
    def updateComicInfo(self, comic: Comic, mainGUI, event=None):
        #?###########################################################
        #? 更新漫画信息
        data = comic.getComicInfo()
        mainGUI.label_manga_title.setText("<span style='color:blue;font-weight:bold'>标题：</span>" + data['title'])
        mainGUI.label_manga_author.setText("<span style='color:blue;font-weight:bold'>作者：</span>" + data['author_name'])
        mainGUI.label_manga_style.setText(f"<span style='color:blue;font-weight:bold'>标签：</span>{data['styles'] or '无'}")
        mainGUI.label_manga_isFinish.setText(f"<span style='color:blue;font-weight:bold'>状态：</span>{'已完结' if data['is_finish'] else '连载中'}")
        mainGUI.label_manga_outline.setText(f"<span style='color:blue;font-weight:bold'>概要：</span>{data['evaluate'] or '无'}")
        
        #?###########################################################
        #? 加载图片，以及绑定双击和悬停事件
        labelImg = QPixmap.fromImage(QImage.fromData(requests.get(data['vertical_cover']).content))
        mainGUI.label_manga_image.mouseDoubleClickEvent = lambda event: QDesktopServices.openUrl(QUrl(f"https://manga.bilibili.com/detail/mc{data['ID']}"))
        mainGUI.label_manga_image.setToolTip(f"双击打开漫画详情页\nhttps://manga.bilibili.com/detail/mc{data['ID']}")
        
        #?###########################################################
        #? 重写图片大小改变事件，使图片不会变形
        def __(event=None):
            newSize = event.size() if event else mainGUI.label_manga_image.size()
            if newSize.width() < 200:
                newSize.setWidth(200)
            img = labelImg.scaled(newSize, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            mainGUI.label_manga_image.setPixmap(img)
            mainGUI.label_manga_image.setAlignment(Qt.AlignTop)
        mainGUI.label_manga_image.resizeEvent = __
        __()
        
        #?###########################################################
        #? 更新漫画章节详情
        mainGUI.listWidget_chp_detail.clear()
        self.numSelected = 0
        num_unlocked = 0
        if comic:
            epiList = comic.getEpisodeInfo()
        for (title, isAvailable, isDownloaded) in epiList:
            temp = QListWidgetItem(title)
            temp.setCheckState(Qt.Unchecked)
            if isDownloaded:
                temp.setFlags(Qt.NoItemFlags)
                temp.setCheckState(Qt.Checked)
                temp.setBackground(QColor(0, 255, 0, 50))
            if not isAvailable:
                temp.setFlags(Qt.NoItemFlags)
            else:
                num_unlocked += 1
            temp.setSizeHint(QSize(160, 20))
            temp.setTextAlignment(Qt.AlignLeft)
            temp.setToolTip(title)
            mainGUI.listWidget_chp_detail.addItem(temp)
            
        #?###########################################################
        #? 绑定总章节数和已下载章节数等等的显示
        mainGUI.label_chp_detail_total_chp.setText(f"总章数：{len(epiList)}")
        mainGUI.label_chp_detail_num_unlocked.setText(f"已解锁：{num_unlocked}")
        mainGUI.label_chp_detail_num_downloaded.setText(f"已下载：{comic.getNumDownloaded()}")
        mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.numSelected}")


    ############################################################
    # 绑定章节界面的多选以及右键菜单事件
    ############################################################
    def init_episodesDetails(self, mainGUI):
        self.numSelected = 0
        mainGUI.listWidget_chp_detail.setDragEnabled(False)
        
        #?###########################################################
        #? 绑定鼠标点击选择信号
        def _(item):
            if item.flags() == Qt.NoItemFlags:
                return
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
                self.numSelected -= 1
            elif item.checkState() == Qt.Unchecked:
                item.setCheckState(Qt.Checked)
                self.numSelected += 1
            mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.numSelected}")
        mainGUI.listWidget_chp_detail.itemClicked.connect(_)
        
        #?###########################################################
        #? 绑定右键菜单，让用户可以勾选或者全选等        
        def checkSelected():
            for item in mainGUI.listWidget_chp_detail.selectedItems():
                if item.flags() != Qt.NoItemFlags and item.checkState() == Qt.Unchecked:
                    item.setCheckState(Qt.Checked)
                    self.numSelected += 1
            mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.numSelected}")
        
        def uncheckSelected():
            for item in mainGUI.listWidget_chp_detail.selectedItems():
                if item.flags() != Qt.NoItemFlags and item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                    self.numSelected -= 1
            mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.numSelected}")
        
        def checkAll():
            self.numSelected = 0
            for i in range(mainGUI.listWidget_chp_detail.count()):
                if mainGUI.listWidget_chp_detail.item(i).flags() != Qt.NoItemFlags:
                    mainGUI.listWidget_chp_detail.item(i).setCheckState(Qt.Checked)
                    self.numSelected += 1
            mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.numSelected}")
        
        def uncheckAll():
            self.numSelected = 0
            for i in range(mainGUI.listWidget_chp_detail.count()):
                if mainGUI.listWidget_chp_detail.item(i).flags() != Qt.NoItemFlags:
                    mainGUI.listWidget_chp_detail.item(i).setCheckState(Qt.Unchecked)
            mainGUI.label_chp_detail_num_selected.setText(f"已选中：{self.numSelected}")

        def myMenu(pos):
            menu = QMenu()
            menu.addAction("勾选", checkSelected)
            menu.addAction("取消勾选", uncheckSelected)
            menu.addAction("全选", checkAll)
            menu.addAction("取消全选", uncheckAll)
            menu.exec_(mainGUI.listWidget_chp_detail.mapToGlobal(pos))

        mainGUI.listWidget_chp_detail.setContextMenuPolicy(Qt.CustomContextMenu)
        mainGUI.listWidget_chp_detail.customContextMenuRequested.connect(myMenu)