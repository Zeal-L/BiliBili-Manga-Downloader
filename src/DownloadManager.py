"""
该模块包含了一个下载管理器类，用于管理漫画下载任务的创建、更新和删除等操作
"""

import time
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import SignalInstance

from src.Episode import Episode


class DownloadManager:
    """下载管理器类，用于管理漫画下载任务的创建、更新和删除等操作"""

    def __init__(
        self,
        max_workers: int,
        signal_rate_progress: SignalInstance,
        signal_message_box: SignalInstance,
    ) -> None:
        self.id_count = 0
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.signal_rate_progress = signal_rate_progress
        self.signal_message_box = signal_message_box

        self.terminated = False
        self.all_tasks = {}
        self.avg_speed_in_last_three_sec = {}

    ############################################################

    def createEpisodeTask(self, epi: Episode) -> int:
        """创建一个新的漫画章节任务并将其添加到所有任务列表中

        Args:
            epi (Episode): 要下载的章节

        Returns:
            int: 新创建任务的ID。
        """
        self.all_tasks[self.id_count] = {
            "size": epi.size,
            "curr_rate": 0.0,
            "last_rate": 0.0,
            "last_time": time.time(),
            "curr_speed": 0.1,
            "avg_speed": 0.1,
            "future": self.executor.submit(self.__thread__EpisodeTask, self.id_count, epi),
        }
        self.id_count += 1
        return self.id_count - 1

    ############################################################

    def updateTaskInfo(self, curr_id: int, rate: float) -> None:
        """更新任务信息，包括当前速度、当前下载速率、上一次下载速率和上一次更新时间

        Args:
            curr_id (int): 当前任务的ID
            rate (float): 下载进度百分比
        """
        task: dict = self.all_tasks[curr_id]
        curr_time = time.time()

        task["curr_speed"] = (task["size"] * rate - task["size"] * task["last_rate"]) / (
            curr_time - task["last_time"]
        )

        task["curr_rate"] = rate
        task["last_rate"] = task["curr_rate"]
        task["last_time"] = curr_time

    ############################################################

    def getTotalRate(self) -> float:
        """获取所有任务的平均下载进度"""

        if len(self.all_tasks) == 0:
            return 100.0

        return (
            sum(task["curr_rate"] for task in self.all_tasks.values()) / len(self.all_tasks) * 100
        )

    ############################################################

    def getTotalSpeed(self) -> float:
        """获取所有任务的平均下载速度

        Returns:
            float: 平均下载速度
        """
        self.avg_speed_in_last_three_sec[time.time()] = sum(
            task["curr_speed"] for task in self.all_tasks.values() if task["curr_rate"] != 1
        )
        # 取3秒内的平均速度，以防止速度突然变化
        # 比如下载完一个文件 速度突然变为0
        # 或者开始一组新的下载，速度突然变为很大
        for key in list(self.avg_speed_in_last_three_sec.keys()):
            if key < time.time() - 3:
                self.avg_speed_in_last_three_sec.pop(key)

        return sum(self.avg_speed_in_last_three_sec.values()) / len(
            self.avg_speed_in_last_three_sec
        )

    ############################################################

    def getTotalSpeedStr(self) -> str:
        """获取所有任务的平均下载速度的字符串表示

        Returns:
            str: 平均下载速度的字符串表示
        """
        return self.formatSpeed(self.getTotalSpeed())

    ############################################################

    def getTotalRemainedTimeStr(self) -> str:
        """获取所有任务的剩余时间的字符串表示

        Returns:
            str: 剩余时间的字符串表示
        """
        total_size_left = sum(
            task["size"] * (1 - task["curr_rate"]) for task in self.all_tasks.values()
        )
        total_speed = self.getTotalSpeed()
        return self.formatTime(total_size_left / total_speed if total_speed != 0 else 1)

    ############################################################

    def __thread__EpisodeTask(self, curr_id: int, epi: Episode) -> None:
        """下载漫画章节的线程函数, 会在一个新的线程中运行, 包括下载图片和保存图片任务

        Args:
            curr_id (int): 当前任务的ID
            epi (Episode): 要下载的章节
        """
        # ?###########################################################
        # ? 初始化下载图片需要的参数
        if not epi.init_imgsList():
            self.reportError(curr_id)
            return

        # ?###########################################################
        # ? 下载所有图片
        imgs_path = []
        for index, img in enumerate(epi.imgs_token, start=1):
            if self.terminated:
                epi.clear(imgs_path)
                return
            if img.get("token") is not None:
                img_url = f"{img['url']}?token={img['token']}"
            else:
                img_url = img["url"]
            img_path = epi.downloadImg(index, img_url)
            if img_path is None:
                self.reportError(curr_id)
                epi.clearAfterSave(imgs_path)
                return

            rate = index / len(epi.imgs_token)

            imgs_path.append(img_path)

            # ?###########################################################
            # ? 保存图片
            save_path = None
            if rate == 1:
                save_path = epi.save(imgs_path)

            self.updateTaskInfo(curr_id, rate)
            self.signal_rate_progress.emit(
                {"taskID": curr_id, "rate": int(rate * 100), "path": save_path}
            )

    ############################################################
    # ? 为以后的特典下载留的接口

    # def createSCTask(self) -> int:
    #     pass

    # def thread_SCTask(self) -> None:
    #     pass

    ############################################################

    def clearAll(self) -> None:
        """任务完成后的清理工作

        Args:
            curr_id (int): 当前任务的ID
        """
        self.all_tasks.clear()

    ############################################################

    def reportError(self, curr_id: int) -> None:
        """任务出错时的处理

        Args:
            curr_id (int): 当前任务的ID
        """
        self.signal_rate_progress.emit(
            {
                "taskID": curr_id,
                "rate": -1,
            }
        )
        self.all_tasks.pop(curr_id)

    ############################################################
    def formatSpeed(self, speed: float) -> str:
        """格式化每秒速度大小

        Args:
            speed (float): 每秒速度大小 (字节)

        Returns:
            str: 格式化后的每秒速度大小, 例如: 1.23MB/s
        """
        if speed < 0:
            return "0B/s"
        if speed < 1024:
            return f"{speed:.0f}B/s"
        if speed < 1024 * 1024:
            return f"{speed / 1024:.2f}KB/s"
        if speed < 1024 * 1024 * 1024:
            return f"{speed / 1024 / 1024:.2f}MB/s"
        if speed < 1024 * 1024 * 1024 * 1024:
            return f"{speed / 1024 / 1024 / 1024:.2f}GB/s"

        return f"{speed / 1024 / 1024 / 1024 / 1024:.2f}TB/s"

    ############################################################
    def formatTime(self, seconds: float) -> str:
        """格式化剩余时间

        Args:
            seconds (float): 剩余时间

        Returns:
            str: 格式化后的剩余时间, 例如: 1天 23:59:59
        """
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 24:
            return "%d天 %02d:%02d:%02d" % (h // 24, h % 24, m, s)
        return "%02d:%02d:%02d" % (h, m, s)
