from sys import argv, exit
from ctypes import windll


from PySide6.QtWidgets import QApplication, QMessageBox

from src.ui.MainGUI import MainGUI
from src.Utils import __version__


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(argv)

    if windll.user32.FindWindowW(None, f"哔哩哔哩漫画下载器 v{__version__}") != 0:
        box = QMessageBox.information(None, "提示", "有一个我已经不满足不了你吗？\n\t...(｡•ˇ‸ˇ•｡) ...")
        exit(0)

    window = MainGUI(app)
    window.show()
    app.exec()
