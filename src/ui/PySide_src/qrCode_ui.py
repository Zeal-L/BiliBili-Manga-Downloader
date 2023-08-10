# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qrCode.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
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
from PySide6.QtWidgets import (QApplication, QLabel, QLayout, QSizePolicy,
    QVBoxLayout, QWidget)
import src.ui.PySide_src.resource_rc

class Ui_QrCode(object):
    def setupUi(self, QrCode):
        if not QrCode.objectName():
            QrCode.setObjectName(u"QrCode")
        QrCode.resize(418, 447)
        icon = QIcon()
        icon.addFile(u":/imgs/BiliBili_favicon.ico", QSize(), QIcon.Normal, QIcon.Off)
        QrCode.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(QrCode)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetFixedSize)
        self.label = QLabel(QrCode)
        self.label.setObjectName(u"label")
        self.label.setLayoutDirection(Qt.LeftToRight)
        self.label.setAutoFillBackground(False)
        self.label.setTextFormat(Qt.MarkdownText)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setIndent(-1)

        self.verticalLayout.addWidget(self.label)

        self.label_img = QLabel(QrCode)
        self.label_img.setObjectName(u"label_img")
        self.label_img.setPixmap(QPixmap(u":/imgs/fail_img.jpg"))

        self.verticalLayout.addWidget(self.label_img)

        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(QrCode)

        QMetaObject.connectSlotsByName(QrCode)
    # setupUi

    def retranslateUi(self, QrCode):
        QrCode.setWindowTitle(QCoreApplication.translate("QrCode", u"\u4e8c\u7ef4\u7801\u767b\u5165\u7a97\u53e3", None))
        self.label.setText(QCoreApplication.translate("QrCode", u"## \u8bf7\u4f7f\u7528BiliBili\u624b\u673a\u5ba2\u6237\u7aef\u626b\u63cf\u4e8c\u7ef4\u7801\u767b\u5165", None))
        self.label_img.setText("")
    # retranslateUi

