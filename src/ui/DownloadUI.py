import json
import logging
import os
import re
import sys
from functools import partial
from logging import handlers

import requests

from PySide6.QtCore import (Q_ARG, QEvent, QMetaObject, QSize, Qt, QThread,
                            QTimer, QUrl, Slot)
from PySide6.QtGui import (QColor, QDesktopServices, QFont, QImage, QPixmap,
                           QStandardItem, QStandardItemModel, QTextCharFormat,
                           QTextCursor)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox,
                               QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                               QLayout, QListView, QListWidget,
                               QListWidgetItem, QMenu, QMessageBox,
                               QPushButton, QRadioButton, QSizePolicy,
                               QVBoxLayout, QWidget)
from ui_mainWidget import Ui_MainWidget

from src.Comic import Comic
from src.searchComic import SearchComic
from src.utils import *


class DownloadUI(): 
    
    def __init__(self, mainGUI): 
        self.init_totalProgressUI(mainGUI)
        self.init_processingUI(mainGUI)
        self.init_finishedUI(mainGUI)
    
    
    
    def init_totalProgressUI(self, mainGUI):
        pass
    def init_processingUI(self, mainGUI):
        pass
    
    def init_finishedUI(self, mainGUI):
        pass
    
    def addTask(self, comic):
        pass