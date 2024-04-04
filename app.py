"""
这是一个哔哩哔哩漫画下载器的应用程序，它提供了一个GUI界面，可以让用户下载漫画。这个文件是程序的入口文件，用于启动程序。
"""


import ctypes
import subprocess
from sys import argv, exit, platform

from PySide6.QtWidgets import QApplication, QMessageBox

from src.ui.MainGUI import MainGUI
from src.Utils import __main_window_title__, logger

if __name__ == "__main__":
    app = QApplication.instance() or QApplication(argv)

    if platform == "win32" and ctypes.windll.user32.FindWindowW(None, __main_window_title__) != 0:
        _box = QMessageBox.information(
            None, "提示", "有一个我已经满足不了你吗？\n\t...(｡•ˇ‸ˇ•｡) ..."
        )
        exit(0)
    elif platform == "darwin":
        script = """
        set windowTitle to "{}"
        tell application "System Events"
            set listOfProcesses to every process whose visible is true
            repeat with proc in listOfProcesses
                try
                    if exists (window 1 of proc where the name contains windowTitle) then
                        return true
                    end if
                end try
            end repeat
        end tell
        return false
        """.format(__main_window_title__)

        try:
            output = subprocess.check_output(["osascript", "-e", script], text=True).strip()
            if output == "true":
                QMessageBox.information(
                    None, "提示", "有一个我已经满足不了你吗？\n\t...(｡•ˇ‸ˇ•｡) ..."
                )
                exit(1)
        except subprocess.CalledProcessError as e:
            logger.error("检查是否有重复窗口时出错：", e)
            exit(1)

    window = MainGUI(app)
    window.show()
    app.exec()
