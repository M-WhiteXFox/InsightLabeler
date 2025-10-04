import sys
import Utils
import frame_splitter
import ui_components
from functools import partial
import threading

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, \
    QSizePolicy, QFileDialog, QLineEdit, QSpinBox, QStackedWidget, QGroupBox, QFrame
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class FrameExtractorThread(QThread):
    """帧提取线程，避免阻塞UI"""
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        
    def run(self):
        success = frame_splitter.extract_frames(self.config)
        self.finished_signal.emit(success)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Utils.load_config()
        self.current_frame_index = 0
        self.frame_files = []
        self.extract_thread = None

        self.setWindowTitle("InsightLabeler - 智能视频标注工具")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(self.get_main_style())

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
        self.refresh_frame_files()
        
        # 加载第一帧
        if self.frame_files:
            self.load_frame(0)

    def get_main_style(self):
        """获取主样式表"""
        return """
            QMainWindow {
                background-color: #f0f0f0;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QPushButton {
                background-color: #6c757d;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;  /* 其他按钮使用16px */
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                margin: 4px 2px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
            QPushButton:checked {
                background-color: #495057;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 16px;  /* 其他组件使用16px */
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #6c757d;
            }
            QLabel {
                font-size: 16px;  /* 其他组件使用16px */
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                color: #333;
            }
            QSpinBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 16px;  /* 其他组件使用16px */
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 1ex;
                font-weight: bold;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #f0f0f0;
                color: #333;
                font-size: 16px;  /* 其他组件使用16px */
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """

    def create_top_button_bar(self, main_layout):
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
        self.video_btn = ui_components.create_top_button("视频处理", "#6c757d", None, False)
        self.video_btn.clicked.connect(lambda: self.switch_function_panel(0))
        # 去除按钮焦点边框
        self.video_btn.setFocusPolicy(Qt.NoFocus)
        button_layout.addWidget(self.video_btn)
        
        self.annotate_btn = ui_components.create_top_button("图像标注", "#6c757d", None, False)
        self.annotate_btn.clicked.connect(lambda: self.switch_function_panel(1))
        # 去除按钮焦点边框
        self.annotate_btn.setFocusPolicy(Qt.NoFocus)
        button_layout.addWidget(self.annotate_btn)
        
        self.settings_btn = ui_components.create_top_button("设置", "#6c757d", None, False)
        self.settings_btn.clicked.connect(lambda: self.switch_function_panel(2))
        # 去除按钮焦点边框
        self.settings_btn.setFocusPolicy(Qt.NoFocus)
        button_layout.addWidget(self.settings_btn)
        
        button_layout.addStretch()
        main_layout.addWidget(button_bar)

    def create_middle_area(self, main_layout):
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

    def create_image_display_area(self, parent_layout):
        """创建图片显示区域"""
        # 初始化图片标签
        self.image_label = QLabel()
        self.original_pixmap = QPixmap()
        
        # 尝试加载默认图片
        tmp_pixmap = QPixmap("output/frame_0.jpg")
        if not tmp_pixmap.isNull():
            self.original_pixmap = tmp_pixmap
            self.image_label.setPixmap(self.original_pixmap)
            # 清除无图片时的样式
            self.image_label.setStyleSheet("")
        
        # 使用ui_components创建图片显示区域
        ui_components.create_image_display_area(parent_layout, self.image_label)

    def create_function_panel_area(self, parent_layout):
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

    def switch_function_panel(self, index):
        """切换功能面板"""
        self.function_panel.setCurrentIndex(index)
        
        # 更新按钮状态 - 使用样式来表示选中状态
        buttons = [self.video_btn, self.annotate_btn, self.settings_btn]
        for i, btn in enumerate(buttons):
            # 去除按钮焦点边框
            btn.setFocusPolicy(Qt.NoFocus)
            if i == index:
                # 为选中的按钮设置不同的样式
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #495057;
                        border: 2px solid #6c757d;
                        color: white;
                        padding: 14px 28px;
                        text-align: center;
                        text-decoration: none;
                        font-size: 20px;
                        font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                        font-weight: normal;
                        margin: 4px 2px;
                        border-radius: 8px;
                        min-width: 140px;
                    }
                    QPushButton:hover {
                        background-color: #5a6268;
                    }
                    QPushButton:pressed {
                        background-color: #545b62;
                    }
                """)
            else:
                # 为未选中的按钮恢复默认样式
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #6c757d;
                        border: none;
                        color: white;
                        padding: 14px 28px;
                        text-align: center;
                        text-decoration: none;
                        font-size: 20px;
                        font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                        font-weight: normal;
                        margin: 4px 2px;
                        border-radius: 8px;
                        min-width: 140px;
                    }
                    QPushButton:hover {
                        background-color: #5a6268;
                    }
                    QPushButton:pressed {
                        background-color: #545b62;
                    }
                """)

    def extract_frames_handler(self):
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
        
        # 使用线程避免阻塞UI
        self.extract_thread = FrameExtractorThread(self.config)
        self.extract_thread.finished_signal.connect(self.on_extraction_finished)
        self.extract_thread.start()
        
        # 禁用提取按钮，防止重复点击
        self.extract_btn.setText("提取中...")
        self.extract_btn.setEnabled(False)

    def on_extraction_finished(self, success):
        """帧提取完成回调"""
        # 重新启用提取按钮
        self.extract_btn.setText("提取帧")
        self.extract_btn.setEnabled(True)
        
        if success:
            # 刷新帧文件列表
            self.refresh_frame_files()

    def goto_frame(self):
        """跳转到指定帧"""
        if self.frame_files:
            max_index = len(self.frame_files) - 1
            target_index = frame_splitter.goto_frame_index(
                self.frame_spinbox.value(), 
                max_index
            )
            self.load_frame(target_index)

    def previous_frame(self):
        """上一张图片"""
        if self.frame_files and self.current_frame_index > 0:
            # 获取用户设置的间隔
            interval = self.interval_spinbox.value()
            # 计算上一张图片的索引
            prev_index = max(0, self.current_frame_index - interval)
            self.load_frame(prev_index)

    def next_frame(self):
        """下一张图片"""
        if self.frame_files and self.current_frame_index < len(self.frame_files) - 1:
            # 获取用户设置的间隔
            interval = self.interval_spinbox.value()
            # 计算下一张图片的索引
            max_index = len(self.frame_files) - 1
            next_index = min(max_index, self.current_frame_index + interval)
            self.load_frame(next_index)

    def load_frame(self, index):
        """加载指定索引的帧"""
        if 0 <= index < len(self.frame_files):
            frame_path = frame_splitter.load_frame(self.frame_files, index)
            if frame_path:
                self.current_frame_index = index
                self.frame_spinbox.setValue(index)
                
                # 加载图片
                pixmap = QPixmap(frame_path)
                if not pixmap.isNull():
                    self.original_pixmap = pixmap
                    self.image_label.setPixmap(self.original_pixmap)
                    self.image_label.setStyleSheet("")  # 清除之前的样式
                    self.image_label.setScaledContents(False)
                    self.resizeEvent(None)  # 调整图片大小以适应窗口

    def refresh_frame_files(self):
        """刷新帧文件列表"""
        output_dir = self.config.get("output_dir", "./output")
        self.frame_files = frame_splitter.get_frame_files(output_dir)
        
        # 更新帧选择框的最大值
        if self.frame_files:
            self.frame_spinbox.setMaximum(len(self.frame_files) - 1)

    def resizeEvent(self, event):
        """窗口缩放自动调整图片大小"""
        if hasattr(self, "original_pixmap") and not self.original_pixmap.isNull():
            self.image_label.setPixmap(
                self.original_pixmap.scaled(
                    self.image_label.size() * 0.95,  # 留一些边距
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
        super().resizeEvent(event)

    def select_file(self, line_edit, key):
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

    def select_output_dir(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录", "./")
        if directory:
            self.output_dir_line_edit.setText(directory)
            self.config["output_dir"] = directory
            Utils.save_config(self.config)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())