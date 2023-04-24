from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from src.ui.PySide_src.myAbout_ui import Ui_My_about


class MyAbout(QWidget, Ui_My_about):
    """关于窗口类"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("关于")
        self.outline.setOpenExternalLinks(True)
        self.setWindowModality(Qt.ApplicationModal)
