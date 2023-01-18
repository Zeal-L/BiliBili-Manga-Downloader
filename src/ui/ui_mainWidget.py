# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainWidget.ui'
##
## Created by: Qt User Interface Compiler version 6.4.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListView, QListWidget, QListWidgetItem, QProgressBar,
    QPushButton, QSizePolicy, QSlider, QSpacerItem,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)
import resource_rc

class Ui_MainWidget(object):
    def setupUi(self, MainWidget):
        if not MainWidget.objectName():
            MainWidget.setObjectName(u"MainWidget")
        MainWidget.resize(1058, 726)
        icon = QIcon()
        icon.addFile(u":/imgs/BiliBili_favicon.ico", QSize(), QIcon.Normal, QIcon.Off)
        MainWidget.setWindowIcon(icon)
        self.horizontalLayout_23 = QHBoxLayout(MainWidget)
        self.horizontalLayout_23.setObjectName(u"horizontalLayout_23")
        self.tabWidget = QTabWidget(MainWidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setAutoFillBackground(False)
        self.tab_my_manga = QWidget()
        self.tab_my_manga.setObjectName(u"tab_my_manga")
        self.horizontalLayout_19 = QHBoxLayout(self.tab_my_manga)
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.v_lLayout_my_manga = QVBoxLayout()
        self.v_lLayout_my_manga.setObjectName(u"v_lLayout_my_manga")
        self.tabWidget_my_manga = QTabWidget(self.tab_my_manga)
        self.tabWidget_my_manga.setObjectName(u"tabWidget_my_manga")
        self.tab_manga_search = QWidget()
        self.tab_manga_search.setObjectName(u"tab_manga_search")
        self.verticalLayout_17 = QVBoxLayout(self.tab_manga_search)
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.h_Layout_manga_search = QHBoxLayout()
        self.h_Layout_manga_search.setObjectName(u"h_Layout_manga_search")
        self.label_8 = QLabel(self.tab_manga_search)
        self.label_8.setObjectName(u"label_8")

        self.h_Layout_manga_search.addWidget(self.label_8)

        self.lineEdit_manga_search_name = QLineEdit(self.tab_manga_search)
        self.lineEdit_manga_search_name.setObjectName(u"lineEdit_manga_search_name")
        self.lineEdit_manga_search_name.setMaximumSize(QSize(300, 16777215))

        self.h_Layout_manga_search.addWidget(self.lineEdit_manga_search_name)

        self.pushButton_manga_search_name = QPushButton(self.tab_manga_search)
        self.pushButton_manga_search_name.setObjectName(u"pushButton_manga_search_name")

        self.h_Layout_manga_search.addWidget(self.pushButton_manga_search_name)

        self.label_manga_search = QLabel(self.tab_manga_search)
        self.label_manga_search.setObjectName(u"label_manga_search")

        self.h_Layout_manga_search.addWidget(self.label_manga_search)

        self.h_Layout_manga_search.setStretch(1, 1)

        self.verticalLayout_17.addLayout(self.h_Layout_manga_search)

        self.listWidget_manga_search = QListWidget(self.tab_manga_search)
        self.listWidget_manga_search.setObjectName(u"listWidget_manga_search")

        self.verticalLayout_17.addWidget(self.listWidget_manga_search)

        self.tabWidget_my_manga.addTab(self.tab_manga_search, "")
        self.tab_local_storage = QWidget()
        self.tab_local_storage.setObjectName(u"tab_local_storage")
        self.verticalLayout_10 = QVBoxLayout(self.tab_local_storage)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.listWidget_local_storage = QListWidget(self.tab_local_storage)
        self.listWidget_local_storage.setObjectName(u"listWidget_local_storage")

        self.verticalLayout_10.addWidget(self.listWidget_local_storage)

        self.tabWidget_my_manga.addTab(self.tab_local_storage, "")

        self.v_lLayout_my_manga.addWidget(self.tabWidget_my_manga)

        self.groupBox_my_manga = QGroupBox(self.tab_my_manga)
        self.groupBox_my_manga.setObjectName(u"groupBox_my_manga")
        self.horizontalLayout_8 = QHBoxLayout(self.groupBox_my_manga)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_manga_image = QLabel(self.groupBox_my_manga)
        self.label_manga_image.setObjectName(u"label_manga_image")
        self.label_manga_image.setEnabled(True)
        self.label_manga_image.setPixmap(QPixmap(u":/imgs/\u522b\u5f53\u54e5\u54e5\u4e86.jpg"))
        self.label_manga_image.setScaledContents(False)
        self.label_manga_image.setWordWrap(False)

        self.horizontalLayout_8.addWidget(self.label_manga_image, 0, Qt.AlignTop)

        self.v_Layout_manga_detail = QVBoxLayout()
        self.v_Layout_manga_detail.setSpacing(6)
        self.v_Layout_manga_detail.setObjectName(u"v_Layout_manga_detail")
        self.label_manga_title = QLabel(self.groupBox_my_manga)
        self.label_manga_title.setObjectName(u"label_manga_title")

        self.v_Layout_manga_detail.addWidget(self.label_manga_title)

        self.label_manga_author = QLabel(self.groupBox_my_manga)
        self.label_manga_author.setObjectName(u"label_manga_author")

        self.v_Layout_manga_detail.addWidget(self.label_manga_author)

        self.label_manga_tag = QLabel(self.groupBox_my_manga)
        self.label_manga_tag.setObjectName(u"label_manga_tag")

        self.v_Layout_manga_detail.addWidget(self.label_manga_tag)

        self.label_manga_outline = QLabel(self.groupBox_my_manga)
        self.label_manga_outline.setObjectName(u"label_manga_outline")
        self.label_manga_outline.setWordWrap(True)

        self.v_Layout_manga_detail.addWidget(self.label_manga_outline, 0, Qt.AlignTop)

        self.v_Layout_manga_detail.setStretch(3, 1)

        self.horizontalLayout_8.addLayout(self.v_Layout_manga_detail)


        self.v_lLayout_my_manga.addWidget(self.groupBox_my_manga)

        self.v_lLayout_my_manga.setStretch(0, 1)
        self.v_lLayout_my_manga.setStretch(1, 1)

        self.horizontalLayout_19.addLayout(self.v_lLayout_my_manga)

        self.groupBox_chp_detail = QGroupBox(self.tab_my_manga)
        self.groupBox_chp_detail.setObjectName(u"groupBox_chp_detail")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_chp_detail)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.h_Layout_chp_detail = QHBoxLayout()
        self.h_Layout_chp_detail.setObjectName(u"h_Layout_chp_detail")
        self.line_5 = QFrame(self.groupBox_chp_detail)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.VLine)
        self.line_5.setFrameShadow(QFrame.Sunken)

        self.h_Layout_chp_detail.addWidget(self.line_5)

        self.label_chp_detail_total_chp = QLabel(self.groupBox_chp_detail)
        self.label_chp_detail_total_chp.setObjectName(u"label_chp_detail_total_chp")

        self.h_Layout_chp_detail.addWidget(self.label_chp_detail_total_chp)

        self.line = QFrame(self.groupBox_chp_detail)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.h_Layout_chp_detail.addWidget(self.line)

        self.label_chp_detail_num_unlocked = QLabel(self.groupBox_chp_detail)
        self.label_chp_detail_num_unlocked.setObjectName(u"label_chp_detail_num_unlocked")

        self.h_Layout_chp_detail.addWidget(self.label_chp_detail_num_unlocked)

        self.line_2 = QFrame(self.groupBox_chp_detail)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.h_Layout_chp_detail.addWidget(self.line_2)

        self.label_chp_detail_num_downloaded = QLabel(self.groupBox_chp_detail)
        self.label_chp_detail_num_downloaded.setObjectName(u"label_chp_detail_num_downloaded")

        self.h_Layout_chp_detail.addWidget(self.label_chp_detail_num_downloaded)

        self.line_3 = QFrame(self.groupBox_chp_detail)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.VLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.h_Layout_chp_detail.addWidget(self.line_3)

        self.label_chp_detail_num_selected = QLabel(self.groupBox_chp_detail)
        self.label_chp_detail_num_selected.setObjectName(u"label_chp_detail_num_selected")

        self.h_Layout_chp_detail.addWidget(self.label_chp_detail_num_selected)

        self.line_4 = QFrame(self.groupBox_chp_detail)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.VLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.h_Layout_chp_detail.addWidget(self.line_4)

        self.pushButton_chp_detail_download_selected = QPushButton(self.groupBox_chp_detail)
        self.pushButton_chp_detail_download_selected.setObjectName(u"pushButton_chp_detail_download_selected")
        self.pushButton_chp_detail_download_selected.setMaximumSize(QSize(120, 25))

        self.h_Layout_chp_detail.addWidget(self.pushButton_chp_detail_download_selected)

        self.pushButton_chp_detail_download_all = QPushButton(self.groupBox_chp_detail)
        self.pushButton_chp_detail_download_all.setObjectName(u"pushButton_chp_detail_download_all")
        self.pushButton_chp_detail_download_all.setMaximumSize(QSize(120, 25))

        self.h_Layout_chp_detail.addWidget(self.pushButton_chp_detail_download_all)


        self.verticalLayout_4.addLayout(self.h_Layout_chp_detail)

        self.listWidget_chp_detail = QListWidget(self.groupBox_chp_detail)
        self.listWidget_chp_detail.setObjectName(u"listWidget_chp_detail")
        self.listWidget_chp_detail.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.listWidget_chp_detail.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.listWidget_chp_detail.setResizeMode(QListView.Adjust)
        self.listWidget_chp_detail.setViewMode(QListView.IconMode)

        self.verticalLayout_4.addWidget(self.listWidget_chp_detail)


        self.horizontalLayout_19.addWidget(self.groupBox_chp_detail)

        self.tabWidget.addTab(self.tab_my_manga, "")
        self.tab_download_list = QWidget()
        self.tab_download_list.setObjectName(u"tab_download_list")
        self.verticalLayout_2 = QVBoxLayout(self.tab_download_list)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.h_Layout_total_progress = QHBoxLayout()
        self.h_Layout_total_progress.setSpacing(20)
        self.h_Layout_total_progress.setObjectName(u"h_Layout_total_progress")
        self.label_total_progress = QLabel(self.tab_download_list)
        self.label_total_progress.setObjectName(u"label_total_progress")

        self.h_Layout_total_progress.addWidget(self.label_total_progress)

        self.progressBar_total_progress = QProgressBar(self.tab_download_list)
        self.progressBar_total_progress.setObjectName(u"progressBar_total_progress")
        self.progressBar_total_progress.setEnabled(True)
        self.progressBar_total_progress.setValue(50)

        self.h_Layout_total_progress.addWidget(self.progressBar_total_progress)


        self.verticalLayout_2.addLayout(self.h_Layout_total_progress)

        self.tabWidget_download_list = QTabWidget(self.tab_download_list)
        self.tabWidget_download_list.setObjectName(u"tabWidget_download_list")
        self.tab_processing = QWidget()
        self.tab_processing.setObjectName(u"tab_processing")
        self.verticalLayout_6 = QVBoxLayout(self.tab_processing)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.v_Layout_processing = QVBoxLayout()
        self.v_Layout_processing.setObjectName(u"v_Layout_processing")
        self.h_Layout_processing = QHBoxLayout()
        self.h_Layout_processing.setSpacing(10)
        self.h_Layout_processing.setObjectName(u"h_Layout_processing")
        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.h_Layout_processing.addItem(self.horizontalSpacer_8)

        self.pushButton_processing_start = QPushButton(self.tab_processing)
        self.pushButton_processing_start.setObjectName(u"pushButton_processing_start")
        self.pushButton_processing_start.setMinimumSize(QSize(100, 25))

        self.h_Layout_processing.addWidget(self.pushButton_processing_start)

        self.pushButton_processing_pause = QPushButton(self.tab_processing)
        self.pushButton_processing_pause.setObjectName(u"pushButton_processing_pause")
        self.pushButton_processing_pause.setMinimumSize(QSize(100, 25))

        self.h_Layout_processing.addWidget(self.pushButton_processing_pause)

        self.pushButton_processing_delete = QPushButton(self.tab_processing)
        self.pushButton_processing_delete.setObjectName(u"pushButton_processing_delete")
        self.pushButton_processing_delete.setMinimumSize(QSize(100, 25))

        self.h_Layout_processing.addWidget(self.pushButton_processing_delete)


        self.v_Layout_processing.addLayout(self.h_Layout_processing)

        self.tableWidget_processing = QTableWidget(self.tab_processing)
        self.tableWidget_processing.setObjectName(u"tableWidget_processing")

        self.v_Layout_processing.addWidget(self.tableWidget_processing)


        self.verticalLayout_6.addLayout(self.v_Layout_processing)

        self.tabWidget_download_list.addTab(self.tab_processing, "")
        self.tab_finished = QWidget()
        self.tab_finished.setObjectName(u"tab_finished")
        self.verticalLayout_7 = QVBoxLayout(self.tab_finished)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.v_Layout_finished = QVBoxLayout()
        self.v_Layout_finished.setObjectName(u"v_Layout_finished")
        self.tableWidget_finished = QTableWidget(self.tab_finished)
        self.tableWidget_finished.setObjectName(u"tableWidget_finished")

        self.v_Layout_finished.addWidget(self.tableWidget_finished)

        self.h_Layout_finished = QHBoxLayout()
        self.h_Layout_finished.setObjectName(u"h_Layout_finished")
        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.h_Layout_finished.addItem(self.horizontalSpacer_6)

        self.pushButton_clear_tasks = QPushButton(self.tab_finished)
        self.pushButton_clear_tasks.setObjectName(u"pushButton_clear_tasks")
        self.pushButton_clear_tasks.setMinimumSize(QSize(120, 25))

        self.h_Layout_finished.addWidget(self.pushButton_clear_tasks)


        self.v_Layout_finished.addLayout(self.h_Layout_finished)


        self.verticalLayout_7.addLayout(self.v_Layout_finished)

        self.tabWidget_download_list.addTab(self.tab_finished, "")

        self.verticalLayout_2.addWidget(self.tabWidget_download_list)

        self.tabWidget.addTab(self.tab_download_list, "")
        self.tab_setting = QWidget()
        self.tab_setting.setObjectName(u"tab_setting")
        self.verticalLayout_5 = QVBoxLayout(self.tab_setting)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.h_Layout_my_cookie = QHBoxLayout()
        self.h_Layout_my_cookie.setObjectName(u"h_Layout_my_cookie")
        self.label_my_cookie = QLabel(self.tab_setting)
        self.label_my_cookie.setObjectName(u"label_my_cookie")
        self.label_my_cookie.setMinimumSize(QSize(110, 0))
        self.label_my_cookie.setMaximumSize(QSize(16777215, 16777215))

        self.h_Layout_my_cookie.addWidget(self.label_my_cookie)

        self.lineEdit_my_cookie = QLineEdit(self.tab_setting)
        self.lineEdit_my_cookie.setObjectName(u"lineEdit_my_cookie")

        self.h_Layout_my_cookie.addWidget(self.lineEdit_my_cookie)

        self.pushButton_my_cookie = QPushButton(self.tab_setting)
        self.pushButton_my_cookie.setObjectName(u"pushButton_my_cookie")

        self.h_Layout_my_cookie.addWidget(self.pushButton_my_cookie)


        self.verticalLayout_5.addLayout(self.h_Layout_my_cookie)

        self.h_Layout_save_path = QHBoxLayout()
        self.h_Layout_save_path.setObjectName(u"h_Layout_save_path")
        self.label_save_path = QLabel(self.tab_setting)
        self.label_save_path.setObjectName(u"label_save_path")
        self.label_save_path.setMinimumSize(QSize(110, 0))
        self.label_save_path.setMaximumSize(QSize(16777215, 16777215))

        self.h_Layout_save_path.addWidget(self.label_save_path)

        self.lineEdit_save_path = QLineEdit(self.tab_setting)
        self.lineEdit_save_path.setObjectName(u"lineEdit_save_path")

        self.h_Layout_save_path.addWidget(self.lineEdit_save_path)

        self.pushButton_save_path = QPushButton(self.tab_setting)
        self.pushButton_save_path.setObjectName(u"pushButton_save_path")

        self.h_Layout_save_path.addWidget(self.pushButton_save_path)


        self.verticalLayout_5.addLayout(self.h_Layout_save_path)

        self.h_Layout_num_thread = QHBoxLayout()
        self.h_Layout_num_thread.setObjectName(u"h_Layout_num_thread")
        self.label_num_thread_count = QLabel(self.tab_setting)
        self.label_num_thread_count.setObjectName(u"label_num_thread_count")
        self.label_num_thread_count.setMinimumSize(QSize(110, 0))
        self.label_num_thread_count.setMaximumSize(QSize(16777215, 16777215))

        self.h_Layout_num_thread.addWidget(self.label_num_thread_count)

        self.h_Slider_num_thread = QSlider(self.tab_setting)
        self.h_Slider_num_thread.setObjectName(u"h_Slider_num_thread")
        self.h_Slider_num_thread.setMinimumSize(QSize(200, 0))
        self.h_Slider_num_thread.setMaximumSize(QSize(200, 16777215))
        self.h_Slider_num_thread.setMinimum(1)
        self.h_Slider_num_thread.setMaximum(36)
        self.h_Slider_num_thread.setSingleStep(2)
        self.h_Slider_num_thread.setPageStep(2)
        self.h_Slider_num_thread.setOrientation(Qt.Horizontal)

        self.h_Layout_num_thread.addWidget(self.h_Slider_num_thread)

        self.label_num_thread = QLabel(self.tab_setting)
        self.label_num_thread.setObjectName(u"label_num_thread")

        self.h_Layout_num_thread.addWidget(self.label_num_thread)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.h_Layout_num_thread.addItem(self.horizontalSpacer_2)


        self.verticalLayout_5.addLayout(self.h_Layout_num_thread)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer)

        self.h_Layout_buttons = QHBoxLayout()
        self.h_Layout_buttons.setSpacing(50)
        self.h_Layout_buttons.setObjectName(u"h_Layout_buttons")
        self.pushButton_open_log = QPushButton(self.tab_setting)
        self.pushButton_open_log.setObjectName(u"pushButton_open_log")
        self.pushButton_open_log.setMaximumSize(QSize(200, 16777215))

        self.h_Layout_buttons.addWidget(self.pushButton_open_log)

        self.pushButton_clear_data = QPushButton(self.tab_setting)
        self.pushButton_clear_data.setObjectName(u"pushButton_clear_data")
        self.pushButton_clear_data.setMaximumSize(QSize(200, 16777215))

        self.h_Layout_buttons.addWidget(self.pushButton_clear_data)

        self.pushButton_about = QPushButton(self.tab_setting)
        self.pushButton_about.setObjectName(u"pushButton_about")
        self.pushButton_about.setMaximumSize(QSize(200, 16777215))

        self.h_Layout_buttons.addWidget(self.pushButton_about)


        self.verticalLayout_5.addLayout(self.h_Layout_buttons)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_2)

        self.verticalLayout_5.setStretch(3, 1)
        self.tabWidget.addTab(self.tab_setting, "")

        self.horizontalLayout_23.addWidget(self.tabWidget)


        self.retranslateUi(MainWidget)

        self.tabWidget.setCurrentIndex(0)
        self.tabWidget_my_manga.setCurrentIndex(0)
        self.tabWidget_download_list.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWidget)
    # setupUi

    def retranslateUi(self, MainWidget):
        MainWidget.setWindowTitle(QCoreApplication.translate("MainWidget", u"Form", None))
        self.label_8.setText(QCoreApplication.translate("MainWidget", u"\u6f2b\u753b\u540d", None))
        self.lineEdit_manga_search_name.setText(QCoreApplication.translate("MainWidget", u"\u522b\u5f53\u4e86", None))
        self.pushButton_manga_search_name.setText(QCoreApplication.translate("MainWidget", u"\u641c\u7d22", None))
        self.label_manga_search.setText("")
        self.tabWidget_my_manga.setTabText(self.tabWidget_my_manga.indexOf(self.tab_manga_search), QCoreApplication.translate("MainWidget", u"\u641c\u7d22\u6f2b\u753b", None))
        self.tabWidget_my_manga.setTabText(self.tabWidget_my_manga.indexOf(self.tab_local_storage), QCoreApplication.translate("MainWidget", u"\u672c\u5730\u5e93\u5b58", None))
        self.groupBox_my_manga.setTitle(QCoreApplication.translate("MainWidget", u"\u6f2b\u753b\u4fe1\u606f", None))
        self.label_manga_image.setText("")
        self.label_manga_title.setText(QCoreApplication.translate("MainWidget", u"\u6807\u9898\uff1a\u522b\u5f53\u54e5\u54e5\u4e86\uff01", None))
        self.label_manga_author.setText(QCoreApplication.translate("MainWidget", u"\u4f5c\u8005\uff1a\u732b\u8c46\u8150\uff0c\u4e00\u8fc5\u793e", None))
        self.label_manga_tag.setText(QCoreApplication.translate("MainWidget", u"\u6807\u7b7e\uff1a\u90fd\u5e02", None))
        self.label_manga_outline.setText(QCoreApplication.translate("MainWidget", u"\u6982\u8981\uff1a  \u6b64\u6f2b\u753b\u7684\u7ffb\u8bd1\u7531\u7248\u6743\u65b9\u63d0\u4f9b\u3011\u6e38\u620f\u5b85\u7eea\u5c71\u771f\u5bfb\u67d0\u5929\u4e00\u89c9\u9192\u6765\u540e\u53d1\u73b0\u81ea\u5df1\u53d8\u6210\u5973\u751f\u4e86\uff01\u539f\u6765\u662f\u59b9\u59b9\u7f8e\u6ce2\u91cc\u4e3a\u4e86\u8fdb\u884c\u89c2\u5bdf\u5b9e\u9a8c\u800c\u5bf9\u4ed6\u4e0b\u836f\u6539\u9020\u3002\u4e8e\u662f\u771f\u5bfb\u88ab\u8feb\u5f00\u59cb\u4e86\u5973\u751f\u751f\u6d3b\uff0c\u4ed6\u80fd\u5426\u9002\u5e94\u5fc3\u8eab\u7684\u6539\u53d8\uff0c\u53c8\u662f\u5426\u53ef\u4ee5\u7ee7\u7eed\u5f53\u54e5\u54e5\u5462\uff1f  ", None))
        self.groupBox_chp_detail.setTitle(QCoreApplication.translate("MainWidget", u"\u7ae0\u8282\u8be6\u60c5", None))
        self.label_chp_detail_total_chp.setText(QCoreApplication.translate("MainWidget", u"\u603b\u7ae0\u8282\u6570\uff1a70", None))
        self.label_chp_detail_num_unlocked.setText(QCoreApplication.translate("MainWidget", u"\u5df2\u89e3\u9501\uff1a10\u7ae0", None))
        self.label_chp_detail_num_downloaded.setText(QCoreApplication.translate("MainWidget", u"\u5df2\u4e0b\u8f7d\uff1a0\u7ae0", None))
        self.label_chp_detail_num_selected.setText(QCoreApplication.translate("MainWidget", u"\u5df2\u9009\u4e2d\uff1a15\u7ae0", None))
        self.pushButton_chp_detail_download_selected.setText(QCoreApplication.translate("MainWidget", u"\u4e0b\u8f7d\u9009\u4e2d\u7ae0\u8282", None))
        self.pushButton_chp_detail_download_all.setText(QCoreApplication.translate("MainWidget", u"\u4e0b\u8f7d\u5168\u90e8\u7ae0\u8282", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_my_manga), QCoreApplication.translate("MainWidget", u"\u6211\u7684\u6f2b\u753b", None))
        self.label_total_progress.setText(QCoreApplication.translate("MainWidget", u"\u603b\u8fdb\u5ea6", None))
        self.pushButton_processing_start.setText(QCoreApplication.translate("MainWidget", u"\u5f00\u59cb\u9009\u4e2d\u4efb\u52a1", None))
        self.pushButton_processing_pause.setText(QCoreApplication.translate("MainWidget", u"\u6682\u505c\u9009\u4e2d\u4efb\u52a1", None))
        self.pushButton_processing_delete.setText(QCoreApplication.translate("MainWidget", u"\u5220\u9664\u9009\u4e2d\u4efb\u52a1", None))
        self.tabWidget_download_list.setTabText(self.tabWidget_download_list.indexOf(self.tab_processing), QCoreApplication.translate("MainWidget", u"\u8fdb\u884c\u4e2d", None))
        self.pushButton_clear_tasks.setText(QCoreApplication.translate("MainWidget", u"\u6e05\u7406\u5df2\u5b8c\u6210\u4efb\u52a1", None))
        self.tabWidget_download_list.setTabText(self.tabWidget_download_list.indexOf(self.tab_finished), QCoreApplication.translate("MainWidget", u"\u5df2\u5b8c\u6210", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_download_list), QCoreApplication.translate("MainWidget", u"\u4e0b\u8f7d\u5217\u8868", None))
        self.label_my_cookie.setText(QCoreApplication.translate("MainWidget", u"\u6211\u7684Cookie\uff1a", None))
        self.pushButton_my_cookie.setText(QCoreApplication.translate("MainWidget", u"\u786e\u8ba4", None))
        self.label_save_path.setText(QCoreApplication.translate("MainWidget", u"\u6f2b\u753b\u4fdd\u5b58\u8def\u5f84\uff1a", None))
        self.pushButton_save_path.setText(QCoreApplication.translate("MainWidget", u"\u6d4f\u89c8...", None))
        self.label_num_thread_count.setText(QCoreApplication.translate("MainWidget", u"\u540c\u65f6\u4e0b\u8f7d\u7ebf\u7a0b\u6570\uff1a", None))
        self.label_num_thread.setText(QCoreApplication.translate("MainWidget", u"\u7ebf\u7a0b\u6570\u5e76\u4e0d\u662f\u8d8a\u591a\u8d8a\u597d\uff0c\u8bf7\u6839\u636e\u81ea\u5df1\u7684\u7f51\u7edc\u60c5\u51b5\u5408\u7406\u914d\u7f6e\uff08\u63a8\u8350\uff1a8\uff09", None))
        self.pushButton_open_log.setText(QCoreApplication.translate("MainWidget", u"\u6253\u5f00\u65e5\u5fd7", None))
        self.pushButton_clear_data.setText(QCoreApplication.translate("MainWidget", u"\u6e05\u7a7a\u7528\u6237\u6570\u636e", None))
        self.pushButton_about.setText(QCoreApplication.translate("MainWidget", u"\u5173\u4e8e", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_setting), QCoreApplication.translate("MainWidget", u"\u8bbe\u7f6e", None))
    # retranslateUi

