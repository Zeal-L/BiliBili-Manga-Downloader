import json
import logging
import os
import re
import sys
from functools import partial
from logging import handlers

import requests

from PySide6.QtCore import (Q_ARG, QEvent, QMetaObject, QSize, Qt, QThread,
                            QTimer, QUrl, Slot, QObject, Signal)
from PySide6.QtGui import (QColor, QDesktopServices, QFont, QImage, QPixmap,
                           QStandardItem, QStandardItemModel, QTextCharFormat,
                           QTextCursor)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox,
                               QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                               QLayout, QListView, QListWidget,
                               QListWidgetItem, QMenu, QMessageBox,
                               QPushButton, QRadioButton, QSizePolicy,
                               QVBoxLayout, QWidget, QProgressBar)
from ui_mainWidget import Ui_MainWidget

from src.Comic import Comic
from src.searchComic import SearchComic
from src.utils import *
from concurrent.futures import ThreadPoolExecutor, as_completed

class DownloadUI(QObject): 
    rate_progress = Signal(dict)
    def __init__(self, mainGUI): 
        super().__init__()
        self.mainGUI = mainGUI
        self.executor = ThreadPoolExecutor(max_workers=mainGUI.getConfig("num_thread"))
        self.future_to_task = []
        self.allTasks = {}
        self.idCount = 0
        self.init_DownloadUI(mainGUI)
        self.remainingTime = RemainingTime()

    def init_DownloadUI(self, mainGUI):
        self.mainGUI.verticalLayout_processing.setAlignment(Qt.AlignTop)
        def _(result):
            
            currTask = self.allTasks[result['taskID']]
            currTask['rate'] = result['rate']
            currTask['bar'].setValue(result['rate'])
            mainGUI.progressBar_total_progress.setValue(
                sum(self.allTasks[i]['rate'] for i in self.allTasks.keys())
                / len(self.allTasks)
            )
            
            
            # mainGUI.label_total_progress_timer.setText(f"预计剩余时间：{self.remainingTime.getTotalRmainingTime()}")
            
            
            if result['rate'] == 100:

                # 删除以下载完成的条目
                for i in range(mainGUI.verticalLayout_processing.count()):
                    # 如果widget的ObjectName和当前任务的id一致
                    if mainGUI.verticalLayout_processing.itemAt(i).widget().objectName() == result['taskID']:
                        toRemove = mainGUI.verticalLayout_processing.itemAt(i).widget()
                        toRemove.deleteLater()
                        # 取出标题组件用于添加到已完成列表
                        label_title = toRemove.layout().itemAt(0).widget()
                        self.addFinished(mainGUI, label_title, result['path'])
                # 删除字典中的条目
                del currTask
                
                
        self.rate_progress.connect(lambda result: _(result))
        mainGUI.verticalLayout_finished.setAlignment(Qt.AlignTop)
        
        # 绑定清空已完成列表按钮
        def __():
            for i in range(mainGUI.verticalLayout_finished.count()):
                mainGUI.verticalLayout_finished.itemAt(i).widget().deleteLater()
        
        mainGUI.pushButton_clear_tasks.clicked.connect(__)
        

    def addFinished(self, mainGUI, label_title, path):
        # 添加到已完成列表
        h_Layout_donwlowdList = QHBoxLayout()
        h_Layout_donwlowdList.addWidget(label_title)
        h_Layout_donwlowdList.addStretch(1)
        # 超链接打开保存路径
        label_filePath = QLabel("<a href='file:///'>打开文件夹</a>")
        label_filePath.linkActivated.connect(lambda: openFolderAndSelectItems(path))
        h_Layout_donwlowdList.addWidget(label_filePath)

        widget = QWidget()
        widget.setLayout(h_Layout_donwlowdList)
        mainGUI.verticalLayout_finished.addWidget(widget)
    
    
    
    def addTask(self, epi):
        # 初始化储存文件夹
        if not os.path.exists(epi.savePath):
            os.makedirs(epi.savePath)
            
        taskID = str(self.idCount)
        
        self.allTasks[taskID] = {
            'rate': 0,
            'size': epi.getEpiSize(),
            'future': self.executor.submit(epi.download, self.rate_progress, taskID)
        }
        

        # 添加任务组件到正在下载列表
        h_Layout_donwlowdList = QHBoxLayout()
        h_Layout_donwlowdList.addWidget(QLabel(f"<span style='color:blue;font-weight:bold'>{epi.comicName}</span>   >  {epi.title}"))
        bar = QProgressBar()
        bar.setTextVisible(True)

        self.allTasks[taskID]['bar'] = bar
        h_Layout_donwlowdList.addWidget(bar)
        h_Layout_donwlowdList.setStretch(0, 1)
        h_Layout_donwlowdList.setStretch(1, 1)
        widget = QWidget()
        widget.setObjectName(taskID)
        widget.setLayout(h_Layout_donwlowdList)
        self.mainGUI.verticalLayout_processing.addWidget(widget)
        self.idCount += 1