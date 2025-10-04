"""
主窗口模块
负责UI界面的创建和用户交互处理
"""

import sys
from typing import Dict, Any
from functools import partial

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, \
    QSizePolicy, QFileDialog, QLineEdit, QSpinBox, QStackedWidget, QGroupBox, QFrame
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

import Utils
import ui_components
from controllers import FrameController
import styles


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Utils.load_config()
        self.frame_controller = FrameController()
        
        # UI组件引用
        self.image_label: QLabel = None
        self.function_panel: QStackedWidget = None
        self.video_line_edit: QLineEdit = None
        self.interval_spinbox: QSpinBox = None
        self.max_frames_spinbox: QSpinBox = None
        self.extract_btn: QPushButton = None
        self.prev_frame_btn: QPushButton = None
        self.next_frame_btn: QPushButton = None
        self.frame_spinbox: QSpinBox = None
        self.goto_btn: QPushButton = None
        self.output_dir_line_edit: QLineEdit = None
        self.settings_btn: QPushButton = None
        self.output_browse_btn: QPushButton = None
        
        # 顶部按钮引用
        self.video_btn: QPushButton = None
        self.annotate_btn: QPushButton = None
        self.settings_btn_top: QPushButton = None

        self.setWindowTitle("InsightLabeler - 智能视频标注工具")
        self.setMinimumSize(1200, 800)
        self.showMaximized()
        self.setStyleSheet(styles.get_main_style())

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(18, 18, 18, 18)
        
        # 顶部按钮区域
        self.create_top_button_bar(main_layout)
        
        # 中间区域 - 图片显示区和功能区
        self.create_middle_area(main_layout)
        
        # 初始化帧文件列表
        self.frame_controller.refresh_frame_files()
        self.frame_controller.frame_loaded.connect(self.on_frame_loaded)
        self.frame_controller.extraction_finished.connect(self.on_extraction_finished)
        
        # 加载第一帧
        if self.frame_controller.frame_files:
            self.frame_controller.load_frame(0)

    def create_top_button_bar(self, main_layout: QVBoxLayout) -> None:
        """创建顶部按钮栏"""
        button_bar = QWidget()
        button_bar.setStyleSheet("""
            QWidget {
                background-color: #495057;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        # 设置按钮栏的尺寸策略
        button_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        button_layout = QHBoxLayout(button_bar)
        button_layout.setSpacing(15)
        
        # 创建样式化的按钮，不使用可切换模式
        # 使用顶部按钮的样式
        self.video_btn = ui_components.create_top_button("视频处理")
        self.video_btn.clicked.connect(lambda: self.switch_function_panel(0))
        button_layout.addWidget(self.video_btn)
        
        self.annotate_btn = ui_components.create_top_button("图像标注")
        self.annotate_btn.clicked.connect(lambda: self.switch_function_panel(1))
        button_layout.addWidget(self.annotate_btn)
        
        self.settings_btn_top = ui_components.create_top_button("设置")
        self.settings_btn_top.clicked.connect(lambda: self.switch_function_panel(2))
        button_layout.addWidget(self.settings_btn_top)
        
        button_layout.addStretch()
        main_layout.addWidget(button_bar)

    def create_middle_area(self, main_layout: QVBoxLayout) -> None:
        """创建中间区域 - 图片显示区和功能区"""
        middle_widget = QWidget()
        middle_layout = QHBoxLayout(middle_widget)
        middle_layout.setSpacing(15)
        
        # 设置中间区域的尺寸策略
        middle_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # 左侧 - 图片显示区 (3/4)
        self.create_image_display_area(middle_layout)
        
        # 右侧 - 功能区 (1/4)
        self.create_function_panel_area(middle_layout)
        
        main_layout.addWidget(middle_widget, stretch=1)

    def create_image_display_area(self, parent_layout: QHBoxLayout) -> None:
        """创建图片显示区域"""
        # 初始化图片标签
        self.image_label = QLabel()
        self.image_label.original_pixmap = QPixmap()
        
        # 尝试加载默认图片
        tmp_pixmap = QPixmap("output/frame_0.jpg")
        if not tmp_pixmap.isNull():
            self.image_label.original_pixmap = tmp_pixmap
            self.image_label.setPixmap(self.image_label.original_pixmap)
            # 清除无图片时的样式
            self.image_label.setStyleSheet("")
        
        # 使用ui_components创建图片显示区域
        ui_components.create_image_display_area(parent_layout, self.image_label)

    def create_function_panel_area(self, parent_layout: QHBoxLayout) -> None:
        """创建功能面板区域"""
        self.function_panel = ui_components.create_function_panel_area(parent_layout)
        
        # 视频处理面板
        video_panel_data = ui_components.create_video_panel(
            self.config, 
            self.select_file, 
            self.extract_frames_handler
        )
        self.video_panel = video_panel_data[0]
        (self.video_line_edit, self.interval_spinbox, self.max_frames_spinbox, 
         self.extract_btn, self.prev_frame_btn, self.next_frame_btn, 
         self.frame_spinbox, self.goto_btn) = video_panel_data[1:]
        
        # 连接按钮信号
        self.prev_frame_btn.clicked.connect(self.previous_frame)
        self.next_frame_btn.clicked.connect(self.next_frame)
        self.goto_btn.clicked.connect(self.goto_frame)
        
        self.function_panel.addWidget(self.video_panel)
        
        # 标注面板
        self.annotate_panel = ui_components.create_annotate_panel()
        self.function_panel.addWidget(self.annotate_panel)
        
        # 设置面板
        settings_panel_data = ui_components.create_settings_panel(self.config)
        self.settings_panel = settings_panel_data[0]
        (self.output_dir_line_edit, self.settings_btn, 
         self.output_browse_btn) = settings_panel_data[1:]
        
        # 连接设置面板按钮信号
        self.output_browse_btn.clicked.connect(self.select_output_dir)
        
        self.function_panel.addWidget(self.settings_panel)
        
        parent_layout.addWidget(self.function_panel, stretch=1)

    def switch_function_panel(self, index: int) -> None:
        """切换功能面板"""
        self.function_panel.setCurrentIndex(index)
        
        # 更新按钮状态 - 使用样式来表示选中状态
        buttons = [self.video_btn, self.annotate_btn, self.settings_btn_top]
        for i, btn in enumerate(buttons):
            if i == index:
                # 为选中的按钮设置不同的样式
                btn.setStyleSheet(styles.get_top_button_style(selected=True))
            else:
                # 为未选中的按钮恢复默认样式
                btn.setStyleSheet(styles.get_top_button_style(selected=False))

    def extract_frames_handler(self) -> None:
        """处理帧提取的槽函数"""
        # 更新配置
        self.config["video_path"] = self.video_line_edit.text()
        self.config["frame_interval"] = self.interval_spinbox.value()
        max_frames = self.max_frames_spinbox.value()
        if max_frames > 0:
            self.config["max_frames"] = max_frames
        else:
            self.config["max_frames"] = None
        Utils.save_config(self.config)
        
        # 更新控制器配置
        self.frame_controller.config = self.config
        
        # 使用控制器处理帧提取
        self.extract_btn.setText("提取中...")
        self.extract_btn.setEnabled(False)
        self.frame_controller.extract_frames()

    def on_extraction_finished(self, success: bool) -> None:
        """帧提取完成回调"""
        # 重新启用提取按钮
        self.extract_btn.setText("提取帧")
        self.extract_btn.setEnabled(True)
        
        if success:
            # 刷新帧文件列表
            self.frame_controller.refresh_frame_files()

    def goto_frame(self) -> None:
        """跳转到指定帧"""
        target_index = self.frame_spinbox.value()
        self.frame_controller.goto_frame(target_index)

    def previous_frame(self) -> None:
        """上一张图片"""
        interval = self.interval_spinbox.value()
        self.frame_controller.previous_frame(interval)

    def next_frame(self) -> None:
        """下一张图片"""
        interval = self.interval_spinbox.value()
        self.frame_controller.next_frame(interval)

    def on_frame_loaded(self, frame_path: str) -> None:
        """帧加载完成回调"""
        self.frame_spinbox.setValue(self.frame_controller.current_frame_index)
        
        # 加载图片
        pixmap = QPixmap(frame_path)
        if not pixmap.isNull():
            self.image_label.original_pixmap = pixmap
            self.image_label.setPixmap(self.image_label.original_pixmap)
            self.image_label.setStyleSheet("")  # 清除之前的样式
            self.image_label.setScaledContents(False)
            self.resizeEvent(None)  # 调整图片大小以适应窗口

    def resizeEvent(self, event) -> None:
        """窗口缩放自动调整图片大小"""
        if hasattr(self.image_label, "original_pixmap") and not self.image_label.original_pixmap.isNull():
            self.image_label.setPixmap(
                self.image_label.original_pixmap.scaled(
                    self.image_label.size() * 0.95,  # 留一些边距
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
        super().resizeEvent(event)

    def select_file(self, line_edit: QLineEdit, key: str) -> None:
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            "./",
            "所有文件 (*);;视频文件 (*.mp4 *.avi *.mov)"
        )

        if file_path:
            line_edit.setText(file_path)
            self.config[key] = file_path
            Utils.save_config(self.config)
            # 更新控制器配置
            self.frame_controller.config = self.config

    def select_output_dir(self) -> None:
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录", "./")
        if directory:
            self.output_dir_line_edit.setText(directory)
            self.config["output_dir"] = directory
            Utils.save_config(self.config)
            # 更新控制器配置
            self.frame_controller.config = self.config


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())