"""
该模块包含DownloadUI类，该类管理下载任务并更新进度条和相关信息
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget

from src.DownloadManager import DownloadManager
from src.Episode import Episode
from src.Utils import openFolderAndSelectItems

if TYPE_CHECKING:
    from src.ui.MainGUI import MainGUI


class DownloadUI(QObject):
    """下载UI类，用于管理下载任务以及相关进度条等信息的显示更新"""

    # ?###########################################################
    # ? 信号槽，用于更新下载进度条
    signal_rate_progress = Signal(dict)

    def __init__(self, mainGUI: MainGUI):
        super().__init__()
        self.tasks_bar = {}
        self.downloadManager = DownloadManager(
            max_workers=mainGUI.getConfig("num_thread"),
            signal_rate_progress=self.signal_rate_progress,
            signal_message_box=mainGUI.signal_message_box,
        )

        self.init_DownloadUI(mainGUI)

    ############################################################
    def init_DownloadUI(self, mainGUI: MainGUI) -> None:
        """初始化下载UI的相关事件绑定

        Args:
            mainGUI (MainGUI): 主窗口类实例
        """
        mainGUI.verticalLayout_processing.setAlignment(Qt.AlignTop)
        mainGUI.verticalLayout_finished.setAlignment(Qt.AlignTop)

        # ?###########################################################
        # ? 任务进度更新的信号槽绑定
        def _(result: dict) -> None:
            taskID = result["taskID"]
            rate = result["rate"]

            # ? 更新当前任务的进度条
            self.tasks_bar[taskID]["bar"].setValue(rate)

            # ? 在下载列表UI里删除下载完成的任务
            # ? 如果 rate 等于1 意味着下载出错跳过，删除任务相关信息
            if rate in (-1, 100):
                for i in reversed(range(mainGUI.verticalLayout_processing.count())):
                    to_delete = mainGUI.verticalLayout_processing.itemAt(i).widget()
                    # ? 如果widget的ObjectName和当前任务的id一致
                    if to_delete.objectName() == str(taskID):
                        if rate == 100:
                            # ? 取出标题组件用于添加到已完成列表
                            label_title = to_delete.layout().itemAt(0).widget()
                            self.addFinished(mainGUI, label_title, result["path"])
                        # ? deleteLater 会有延迟，为了显示效果，先将父控件设为None
                        to_delete.setParent(None)
                        to_delete.deleteLater()

                # ? 删除任务字典中的条目
                del self.tasks_bar[taskID]

            # ? 更新总进度条的进度，速度和剩余时间
            total_progress = self.downloadManager.getTotalRate()
            mainGUI.progressBar_total_progress.setValue(total_progress)
            if total_progress != 100:
                mainGUI.label_total_progress_speed.setText(
                    f"{self.downloadManager.getTotalSpeedStr()}"
                )
                mainGUI.label_total_progress_time.setText(
                    f"{self.downloadManager.getTotalRemainedTimeStr()}"
                )
            else:
                mainGUI.label_total_progress_speed.setText("总下载速度:")
                mainGUI.label_total_progress_time.setText("剩余时间：")
                self.downloadManager.clearAll()

        self.signal_rate_progress.connect(_)

        # ?###########################################################
        # ? 绑定清空已完成列表按钮
        def _() -> None:
            for i in reversed(range(mainGUI.verticalLayout_finished.count())):
                to_delete = mainGUI.verticalLayout_finished.itemAt(i).widget()
                to_delete.setParent(None)
                to_delete.deleteLater()

        mainGUI.pushButton_clear_tasks.clicked.connect(_)

    ############################################################

    def addFinished(self, mainGUI: MainGUI, label_title: QWidget, path: str) -> None:
        """添加已完成任务到已完成列表

        Args:
            mainGUI (MainGUI): 主窗口类实例
            label_title (QWidget): 标题组件
            path (str): 保存路径
        """
        # ?###########################################################
        # ? 添加到已完成列表
        h_layout_download_list = QHBoxLayout()
        h_layout_download_list.addWidget(label_title)
        h_layout_download_list.addStretch(1)

        # ?###########################################################
        # ? 超链接打开保存路径
        label_file_path = QLabel("<a href='file:///'>打开文件夹</a>")
        label_file_path.linkActivated.connect(
            lambda: openFolderAndSelectItems(mainGUI, path)
        )
        h_layout_download_list.addWidget(label_file_path)

        widget = QWidget()
        widget.setLayout(h_layout_download_list)
        mainGUI.verticalLayout_finished.addWidget(widget)

    ############################################################
    def addTask(self, mainGUI: MainGUI, epi: Episode) -> None:
        """添加漫画下载任务

        Args:
            epi (Episode): 漫画章节类实例
        """

        # ?###########################################################
        # ? 创建任务
        task_id = self.downloadManager.createEpisodeTask(epi)

        # ?###########################################################
        # ? 添加任务组件到正在下载列表
        h_layout_download_list = QHBoxLayout()
        h_layout_download_list.addWidget(
            QLabel(
                f"<span style='color:blue;font-weight:bold'>{epi.comic_name}</span>   >  {epi.title}"
            )
        )
        progress_bar = QProgressBar()
        progress_bar.setTextVisible(True)

        self.tasks_bar[task_id] = {
            "bar": progress_bar,
        }

        h_layout_download_list.addWidget(progress_bar)
        h_layout_download_list.setStretch(0, 1)
        h_layout_download_list.setStretch(1, 1)
        widget = QWidget()
        widget.setObjectName(str(task_id))
        widget.setLayout(h_layout_download_list)
        mainGUI.verticalLayout_processing.addWidget(widget)
