"""
控制器模块
负责处理应用程序的业务逻辑，将UI与业务逻辑分离
"""

import os
from typing import List, Optional, Any
from PyQt5.QtCore import QObject, pyqtSignal
import frame_splitter
import Utils
import cv2


class FrameController(QObject):
    """帧处理控制器，负责处理与帧相关的业务逻辑"""

    # 定义信号
    extraction_finished = pyqtSignal(bool)  # 提取完成信号
    frame_loaded = pyqtSignal(object)       # 帧加载完成信号（传入图片路径或numpy数组）

    def __init__(self):
        super().__init__()
        self.config = Utils.load_config()
        self.current_frame_index = 0
        self.frame_files: List[str] = []

        # 预览模式
        self.video_cap: Optional[cv2.VideoCapture] = None
        self.total_frames: int = 0
        self.last_frame_mat = None  # 缓存最近一次 read_frame 发出的帧（ndarray）

    # ----------------------------
    # 基础配置
    # ----------------------------
    def update_config(self, key: str, value: Any) -> None:
        self.config[key] = value
        Utils.save_config(self.config)

    def get_config(self, key: str, default=None) -> Any:
        return self.config.get(key, default)

    # ----------------------------
    # 文件模式：磁盘帧列表
    # ----------------------------
    def refresh_frame_files(self) -> None:
        """刷新帧文件列表（提取后浏览磁盘图片）"""
        output_dir = self.config.get("output_dir", "./output")
        self.frame_files = frame_splitter.get_frame_files(output_dir)

    def extract_frames(self) -> None:
        """提取帧（同步调用，完成后发信号）"""
        try:
            success = frame_splitter.extract_frames(self.config)
            self.extraction_finished.emit(success)
        except Exception as e:
            print(f"帧提取过程中发生错误: {e}")
            self.extraction_finished.emit(False)

    def load_frame(self, index: int) -> Optional[str]:
        """从磁盘帧文件加载并发出信号"""
        if 0 <= index < len(self.frame_files):
            frame_path = frame_splitter.load_frame(self.frame_files, index)
            if frame_path:
                self.current_frame_index = index
                self.frame_loaded.emit(frame_path)
                return frame_path
        return None

    def previous_frame(self, interval: int = 1) -> Optional[str]:
        if self.frame_files and self.current_frame_index > 0:
            prev_index = max(0, self.current_frame_index - interval)
            return self.load_frame(prev_index)
        return None

    def next_frame(self, interval: int = 1) -> Optional[str]:
        if self.frame_files and self.current_frame_index < len(self.frame_files) - 1:
            next_index = min(len(self.frame_files) - 1, self.current_frame_index + interval)
            return self.load_frame(next_index)
        return None

    def goto_frame(self, target_index: int) -> Optional[str]:
        if self.frame_files:
            max_index = len(self.frame_files) - 1
            valid_index = max(0, min(max_index, target_index))
            return self.load_frame(valid_index)
        return None

    # ----------------------------
    # 预览模式：直接读视频流
    # ----------------------------
    def open_video(self, video_path: str) -> None:
        """打开视频供预览/导航使用"""
        if self.video_cap:
            self.close_video()

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("无法打开视频文件")

        self.video_cap = cap
        self.total_frames = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        self.current_frame_index = 0

    def close_video(self) -> None:
        """关闭视频预览"""
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
        self.total_frames = 0
        self.current_frame_index = 0
        self.last_frame_mat = None

    def _emit_frame_from_mat(self, mat, index: int):
        """直接发送内存图像数据（无需写入磁盘）"""
        if mat is None:
            return None
        self.current_frame_index = index
        self.last_frame_mat = mat
        self.frame_loaded.emit(mat)  # 发出 numpy.ndarray
        return mat

    def read_frame(self, index: int):
        """随机访问读取指定帧（预览模式）"""
        if self.video_cap is None or self.total_frames <= 0:
            return None
        index = max(0, min(index, self.total_frames - 1))
        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ret, frame = self.video_cap.read()
        if not ret:
            return None
        return self._emit_frame_from_mat(frame, index)

    def next_frame_preview(self, interval: int = 1):
        """预览模式：下一帧"""
        if self.video_cap is None or self.total_frames <= 0:
            return None
        next_index = min(self.total_frames - 1, self.current_frame_index + interval)
        return self.read_frame(next_index)

    def previous_frame_preview(self, interval: int = 1):
        """预览模式：上一帧"""
        if self.video_cap is None or self.total_frames <= 0:
            return None
        prev_index = max(0, self.current_frame_index - interval)
        return self.read_frame(prev_index)

    def is_preview_mode(self) -> bool:
        """是否处于视频预览模式（直接从 VideoCapture 读帧而非磁盘图片）"""
        return self.video_cap is not None and self.total_frames > 0

    def save_current_frame(self, output_dir: str, quality: int = 95, prefix: str = "frame") -> Optional[str]:
        """
        仅在预览模式下，将当前显示的帧保存到 output_dir。文件名使用当前帧号。
        返回保存后的完整路径；若失败或无帧则返回 None。
        """
        import os
        import cv2
        try:
            if self.last_frame_mat is None:
                return None
            os.makedirs(output_dir, exist_ok=True)
            filename = f"{prefix}_{self.current_frame_index:06d}.jpg"
            path = os.path.join(output_dir, filename)
            success = cv2.imwrite(path, self.last_frame_mat, [cv2.IMWRITE_JPEG_QUALITY, int(quality)])
            if success:
                return path
            else:
                return None
        except Exception as e:
            print(f"保存帧时出错: {e}")
            return None
