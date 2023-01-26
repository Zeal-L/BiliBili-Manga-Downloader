
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'ui'))

from PySide6.QtWidgets import QApplication
from rich.console import Console
from src.ui.MainGUI import MainGUI


console = Console()

if __name__ == '__main__':
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainGUI()
    window.show()
    app.exec()
