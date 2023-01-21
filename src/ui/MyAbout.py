from PySide6.QtWidgets import QWidget
from ui_myAbout import Ui_My_about

from src.utils import *
from PySide6.QtCore import Qt

class MyAbout(QWidget, Ui_My_about): 
    
    def __init__(self): 
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("关于") 
        self.outline.setOpenExternalLinks(True)
        self.setWindowModality(Qt.ApplicationModal)
        