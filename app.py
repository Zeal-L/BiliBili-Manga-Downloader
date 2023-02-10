
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

# 妹子太多只好飞升了

# TODO: 更改window任务栏右键显示信息 <-- 暂时先不管，可能是需要打包后才能解决
# TODO: 检查Cookie过期
# TODO: 缓存更多资源，减少网络请求
# TODO: 添加二维码登入功能
# TODO: 添加不同的主题