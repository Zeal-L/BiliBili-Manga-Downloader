import os
import sys
from ctypes import windll

sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'ui'))

from PySide6.QtWidgets import QApplication, QMessageBox

from src.ui.MainGUI import MainGUI


if __name__ == '__main__':
    app = QApplication.instance() or QApplication(sys.argv)

    if windll.user32.FindWindowW(None, "哔哩哔哩漫画下载器 v1.0.0") != 0:
        box = QMessageBox.information(None, "提示", "有一个我已经不满足不了你吗？\n\t...(｡•ˇ‸ˇ•｡) ...")
        sys.exit(0)

    window = MainGUI()
    window.show()
    app.exec()


# 妹子太多只好飞升了

# TODO: 检查Cookie过期
# TODO: 缓存更多资源，减少网络请求
# TODO: 添加二维码登入功能
# TODO: 添加不同的主题
# TODO: 添加一个启动加载进度条
# TODO: 给漫画UI中间添加一个可拖动布局的线，鼠标拖动线来调整UI的大小