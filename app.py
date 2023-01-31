
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
# TODO: 用户手动加载本地库存，避免启动时扫描 <-- 或者试一下多线程
# TODO: 检查Cookie过期
# TODO: 缓存更多资源，减少网络请求
# TODO: 所有网络申请处添加错误提示窗口
# FIXME: 处理跳过此章节的情况
# TODO: 重新规范一下不同网络请求的timeout时间以及retry Max
# TODO: 重新规范一下混乱的path 命名

