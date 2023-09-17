"""
这是一个哔哩哔哩漫画下载器的应用程序，它提供了一个GUI界面，可以让用户下载漫画。这个文件是程序的入口文件，用于启动程序。
"""

from sys import argv, exit, platform
import ctypes


from PySide6.QtWidgets import QApplication, QMessageBox

from src.ui.MainGUI import MainGUI
from src.Utils import __version__


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(argv)

    if platform == "win32":
        if ctypes.windll.user32.FindWindowW(None, f"哔哩哔哩漫画下载器 v{__version__}") != 0:
            box = QMessageBox.information(None, "提示", "有一个我已经不满足不了你吗？\n\t...(｡•ˇ‸ˇ•｡) ...")
            exit(0)

    window = MainGUI(app)
    window.show()
    app.exec()
