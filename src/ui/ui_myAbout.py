# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'myAbout.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QSizePolicy,
    QVBoxLayout, QWidget)
import src.ui.resource_rc

class Ui_My_about(object):
    def setupUi(self, My_about):
        if not My_about.objectName():
            My_about.setObjectName(u"My_about")
        My_about.resize(821, 610)
        icon = QIcon()
        icon.addFile(u":/imgs/BiliBili_favicon.ico", QSize(), QIcon.Normal, QIcon.Off)
        My_about.setWindowIcon(icon)
        self.horizontalLayout = QHBoxLayout(My_about)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(My_about)
        self.label.setObjectName(u"label")
        self.label.setPixmap(QPixmap(u":/imgs/blinblin.png"))

        self.horizontalLayout.addWidget(self.label)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.outline = QLabel(My_about)
        self.outline.setObjectName(u"outline")
        self.outline.setWordWrap(True)

        self.verticalLayout.addWidget(self.outline)


        self.horizontalLayout.addLayout(self.verticalLayout)


        self.retranslateUi(My_about)

        QMetaObject.connectSlotsByName(My_about)
    # setupUi

    def retranslateUi(self, My_about):
        My_about.setWindowTitle(QCoreApplication.translate("My_about", u"Form", None))
        self.label.setText("")
        self.outline.setText(QCoreApplication.translate("My_about", u"<html><head/><body><p align=\"center\"><span style=\" font-size:16pt; font-weight:700; color:#00aaff;\">\u54d4\u54e9\u54d4\u54e9</span><span style=\" font-size:16pt; font-weight:700;\">\u6f2b\u753b\u4e0b\u8f7d\u5668 </span><span style=\" font-size:16pt; font-weight:700; color:#aa00ff;\">v1.0.1</span></p><p align=\"center\"><span style=\" font-size:14pt; font-weight:700;\">\u4f5c\u8005\uff1aZeal-L</span></p><p align=\"center\"><span style=\" font-size:12pt; font-weight:700;\">\u9879\u76ee\u5730\u5740\uff1a</span><a href=\"https://github.com/Zeal-L/BiliBili-Manga-Downloader\"><span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">https://github.com/Zeal-L/BiliBili-Manga-Downloader</span></a></p><p align=\"center\"><span style=\" font-size:12pt; font-weight:700;\">\u672c\u7a0b\u5e8f\u4ec5\u4f9b\u5b66\u4e60\u4ea4\u6d41\u4f7f\u7528\uff0c\u4e25\u7981\u7528\u4e8e\u5546\u4e1a\u7528\u9014</span></p><p align=\"center\"><span style=\" font-size:16pt; font-weight:700; color:#00aa00;\">\u8054\u7cfb\u65b9"
                        "\u5f0f\uff1a</span><span style=\" font-size:12pt; font-weight:700;\">Q\u7fa4\u53f7\uff1a</span><span style=\" font-size:12pt; font-weight:700; color:#aa00ff;\">244029317</span><span style=\" font-size:12pt; font-weight:700;\"><br/>\u6b22\u8fce\u8fdb\u7fa4\u8ba8\u8bba\u7a0b\u5e8f\uff0c\u6f2b\u753b\uff0c\u8d44\u6e90\u5206\u4eab, \u63d0\u4ea4\u95ee\u9898\u7b49\u7b49</span></p><p align=\"center\"><span style=\" font-family:'HYWenHei-85W'; font-size:12pt; font-weight:700;\">-- LICENSE --</span></p><p align=\"center\"><span style=\" font-family:'HYWenHei-85W'; font-size:12pt;\">BiliBili-Manga-Downloader</span></p><p align=\"center\"><span style=\" font-family:'HYWenHei-85W'; font-size:12pt;\">Copyright (C) 2023 Zeal L</span></p><p align=\"center\"><span style=\" font-family:'HYWenHei-85W'; font-size:12pt;\">This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or ("
                        "at your option) any later version.</span></p><p align=\"center\"><span style=\" font-family:'HYWenHei-85W'; font-size:12pt;\">This program is distributed in the hope that it will be useful,but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.</span></p><p align=\"center\"><span style=\" font-family:'HYWenHei-85W'; font-size:12pt;\">You should have received a copy of the GNU Affero General Public License along with this program. If not, see </span><a href=\"https://www.gnu.org/licenses\"><span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">https://www.gnu.org/licenses</span></a><span style=\" font-family:'HYWenHei-85W'; font-size:12pt;\">.</span></p><p><br/></p></body></html>", None))
    # retranslateUi

