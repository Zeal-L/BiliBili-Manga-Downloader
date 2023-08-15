from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from src.ui.PySide_src.qrCode_ui import Ui_QrCode


class QrCodeUI(QWidget, Ui_QrCode):
    """二维码窗口"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowModality(Qt.ApplicationModal)
