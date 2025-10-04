"""
控制器模块
负责处理应用程序的业务逻辑，将UI与业务逻辑分离
"""

import os
from typing import Dict, List, Optional, Any
from PyQt5.QtCore import QObject, pyqtSignal
import frame_splitter
import Utils


class FrameController(QObject):
    """帧处理控制器，负责处理与帧相关的业务逻辑"""
    
    # 定义信号
    extraction_finished = pyqtSignal(bool)  # 提取完成信号
    frame_loaded = pyqtSignal(str)  # 帧加载完成信号
    
    def __init__(self):
        super().__init__()
        self.config = Utils.load_config()
        self.current_frame_index = 0
        self.frame_files: List[str] = []
        
    def update_config(self, key: str, value: Any) -> None:
        """更新配置项"""
        self.config[key] = value
        Utils.save_config(self.config)
        
    def get_config(self, key: str, default=None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)
        
    def refresh_frame_files(self) -> None:
        """刷新帧文件列表"""
        output_dir = self.config.get("output_dir", "./output")
        self.frame_files = frame_splitter.get_frame_files(output_dir)
        
    def extract_frames(self) -> None:
        """提取帧"""
        try:
            success = frame_splitter.extract_frames(self.config)
            self.extraction_finished.emit(success)
        except Exception as e:
            print(f"帧提取过程中发生错误: {e}")
            self.extraction_finished.emit(False)
            
    def load_frame(self, index: int) -> Optional[str]:
        """加载指定索引的帧"""
        if 0 <= index < len(self.frame_files):
            frame_path = frame_splitter.load_frame(self.frame_files, index)
            if frame_path:
                self.current_frame_index = index
                self.frame_loaded.emit(frame_path)
                return frame_path
        return None
        
    def previous_frame(self, interval: int = 1) -> Optional[str]:
        """加载上一帧"""
        if self.frame_files and self.current_frame_index > 0:
            prev_index = max(0, self.current_frame_index - interval)
            return self.load_frame(prev_index)
        return None
        
    def next_frame(self, interval: int = 1) -> Optional[str]:
        """加载下一帧"""
        if self.frame_files and self.current_frame_index < len(self.frame_files) - 1:
            next_index = min(len(self.frame_files) - 1, self.current_frame_index + interval)
            return self.load_frame(next_index)
        return None
        
    def goto_frame(self, target_index: int) -> Optional[str]:
        """跳转到指定帧"""
        if self.frame_files:
            max_index = len(self.frame_files) - 1
            valid_index = max(0, min(max_index, target_index))
            return self.load_frame(valid_index)
        return None