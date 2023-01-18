import logging
import os
import re
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'ui'))

from PySide6.QtWidgets import QApplication
from rich.console import Console
from src.ui.MyGUI import MyGui
from src.utils import *
from src.Comic import Comic

console = Console()

if __name__ == '__main__':
    rootPath = "C://Users//Zeal//Desktop//漫画"
    
    # comicID = requireInt('请输入漫画ID: ', True)
    # userInput = input('请输入SESSDATA (免费漫画请直接按下enter): ')
    
    # comicID = 'mc26551'
    # comicID = re.sub(r'^mc', '', comicID)
    # sessdata = '160df8b2%2C1689459707%2C66993%2A11'
    # manga = Comic(logger, comicID, sessdata, rootPath)
    # manga.fetch()
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = MyGui()
    window.show()
    app.exec()
