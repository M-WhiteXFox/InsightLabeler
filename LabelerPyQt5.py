"""
主窗口模块
负责UI界面的创建和用户交互处理
"""

import sys
import os
from typing import Dict, Any
from functools import partial

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, \
    QSizePolicy, QFileDialog, QLineEdit, QSpinBox, QStackedWidget, QGroupBox, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer

import Utils
import ui_components
from controllers import FrameController
import styles
import cv2

from annotate_canvas import AnnotateCanvas
from auto_annotator import AutoAnnotator


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Utils.load_config()
        self.frame_controller = FrameController()
        
        # 初始化自动标注器
        self.auto_annotator = AutoAnnotator(self.config.get("model_path", ""))
        self._last_model_path = self.config.get("model_path", "")

        # ====== UI组件引用 ======
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
        self.current_preview_image = None  # 防止 QImage 被 GC
        self.current_frame_mat = None  # 缓存当前帧的numpy数组

        # ====== 窗口设置 ======
        self.setWindowTitle("InsightLabeler - 智能视频标注工具")
        self.setMinimumSize(1200, 800)
        self.showMaximized()
        self.setStyleSheet(styles.get_main_style())

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(18, 18, 18, 18)

        self.create_top_button_bar(main_layout)
        self.create_middle_area(main_layout)

        # 初始化帧文件列表
        self.frame_controller.refresh_frame_files()
        self.frame_controller.frame_loaded.connect(self.on_frame_loaded)
        self.frame_controller.extraction_finished.connect(self.on_extraction_finished)

        # 优先检查是否有视频文件，如果有则进入预览模式
        video_path = self.config.get("video_path", "")
        if video_path and os.path.exists(video_path):
            try:
                self.frame_controller.open_video(video_path)
                # 清空磁盘帧列表，强制进入预览模式
                self.frame_controller.frame_files = []
                # 读取首帧（从视频开头开始）
                self.frame_controller.read_frame(0)
            except Exception as e:
                print(f"自动加载视频失败: {e}")
                # 如果视频加载失败，回退到文件模式
                if self.frame_controller.frame_files:
                    self.frame_controller.load_frame(0)
        elif self.frame_controller.frame_files:
            # 没有视频文件时，使用磁盘帧文件
            self.frame_controller.load_frame(0)

    # =============================
    # 顶部功能按钮栏
    # =============================
    def create_top_button_bar(self, main_layout: QVBoxLayout) -> None:
        button_bar = QWidget()
        button_bar.setStyleSheet("""
            QWidget {
                background-color: #495057;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        button_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        button_layout = QHBoxLayout(button_bar)
        button_layout.setSpacing(15)

        self.video_btn = ui_components.create_top_button("视频处理")
        self.video_btn.clicked.connect(lambda: self.switch_function_panel(0))
        button_layout.addWidget(self.video_btn)

        self.annotate_tab_btn = ui_components.create_top_button("图像标注")
        self.annotate_tab_btn.clicked.connect(lambda: self.switch_function_panel(1))
        button_layout.addWidget(self.annotate_tab_btn)

        self.settings_btn_top = ui_components.create_top_button("设置")
        self.settings_btn_top.clicked.connect(lambda: self.switch_function_panel(2))
        button_layout.addWidget(self.settings_btn_top)

        button_layout.addStretch()
        main_layout.addWidget(button_bar)

    # =============================
    # 中间区域：预览 + 功能面板
    # =============================
    def create_middle_area(self, main_layout: QVBoxLayout) -> None:
        middle_widget = QWidget()
        middle_layout = QHBoxLayout(middle_widget)
        middle_layout.setSpacing(15)
        middle_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # 左侧：图片预览
        self.image_label = AnnotateCanvas()
        self.image_label.original_pixmap = QPixmap()
        ui_components.create_image_display_area(middle_layout, self.image_label)

        # 右侧：功能区
        self.create_function_panel_area(middle_layout)
        main_layout.addWidget(middle_widget, stretch=1)

    # =============================
    # 功能区：视频 / 标注 / 设置
    # =============================
    def create_function_panel_area(self, parent_layout: QHBoxLayout) -> None:
        self.function_panel = ui_components.create_function_panel_area(parent_layout)

        # 视频面板
        video_panel_data = ui_components.create_video_panel(
            self.config,
            self.select_file,
            self.extract_frames_handler
        )
        self.video_panel = video_panel_data[0]
        (self.video_line_edit, self.interval_spinbox, self.max_frames_spinbox,
         self.extract_btn, self.prev_frame_btn, self.next_frame_btn,
         self.frame_spinbox, self.goto_btn, self.frame_info_label, 
         self.save_frame_btn, self.progress_slider) = video_panel_data[1:]

        self.prev_frame_btn.clicked.connect(self.previous_frame)
        self.next_frame_btn.clicked.connect(self.next_frame)
        self.goto_btn.clicked.connect(self.goto_frame)
        self.save_frame_btn.clicked.connect(self.save_current_frame)
        self.progress_slider.sliderPressed.connect(self.on_progress_pressed)
        self.progress_slider.sliderReleased.connect(self.on_progress_released)
        self.progress_slider.valueChanged.connect(self.on_progress_changed)
        
        # 添加拖动状态标志
        self.is_slider_dragging = False
        # 添加防抖定时器
        self.progress_timer = QTimer()
        self.progress_timer.setSingleShot(True)
        self.progress_timer.timeout.connect(self._jump_to_progress_frame)

        self.function_panel.addWidget(self.video_panel)

        # 标注面板
        annotate_panel_data = ui_components.create_annotate_panel()
        self.annotate_panel = annotate_panel_data[0]
        self.new_box_btn = annotate_panel_data[1]
        
        # 连接新建框按钮信号
        self.new_box_btn.toggled.connect(self.toggle_draw_mode)
        
        self.function_panel.addWidget(self.annotate_panel)

        # 设置面板
        settings_panel_data = ui_components.create_settings_panel(self.config)
        self.settings_panel = settings_panel_data[0]
        (self.output_dir_line_edit, self.settings_btn,
         self.output_browse_btn, self.model_path_line_edit, 
         self.model_browse_btn, self.model_status_label) = settings_panel_data[1:]
        self.output_browse_btn.clicked.connect(self.select_output_dir)
        self.model_browse_btn.clicked.connect(self.select_model_file)
        self.settings_btn.clicked.connect(self.save_settings)
        
        # 初始化模型状态显示
        self.update_model_status()

        self.function_panel.addWidget(self.settings_panel)
        parent_layout.addWidget(self.function_panel, stretch=1)

    # =============================
    # 文件选择与事件响应
    # =============================
    def select_file(self, line_edit: QLineEdit, key: str) -> None:
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "./", "视频文件 (*.mp4 *.avi *.mov);;所有文件 (*)"
        )

        if file_path:
            line_edit.setText(file_path)
            self.config[key] = file_path
            Utils.save_config(self.config)
            self.frame_controller.config = self.config

            if key == "video_path":
                try:
                    # 打开视频进入"预览模式"
                    self.frame_controller.open_video(file_path)
                    # 清空磁盘帧列表，强制上下张/跳转走内存预览
                    self.frame_controller.frame_files = []
                    # 读取首帧（从视频开头开始）
                    self.frame_controller.read_frame(0)
                except Exception as e:
                    QMessageBox.warning(self, "错误", str(e))

    def save_current_frame(self):
        """保存当前帧"""
        if hasattr(self.frame_controller, 'save_current_frame') and self.frame_controller.is_preview_mode():
            output_dir = self.config.get("output_dir", "./output")
            try:
                saved_path = self.frame_controller.save_current_frame(output_dir)
                if saved_path:
                    QMessageBox.information(self, "成功", f"帧已保存到: {saved_path}")
                else:
                    QMessageBox.warning(self, "失败", "无法保存当前帧")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存帧时出错: {str(e)}")
        else:
            QMessageBox.warning(self, "提示", "当前不在预览模式下，无法保存帧")

    def select_output_dir(self) -> None:
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录", "./")
        if directory:
            self.output_dir_line_edit.setText(directory)
            self.config["output_dir"] = directory
            Utils.save_config(self.config)
            self.frame_controller.config = self.config
    
    def select_model_file(self) -> None:
        """选择YOLO模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择YOLO模型文件", "./", "PyTorch模型文件 (*.pt);;所有文件 (*)"
        )
        if file_path:
            self.model_path_line_edit.setText(file_path)
            self.config["model_path"] = file_path
            Utils.save_config(self.config)
            
            # 重新初始化自动标注器
            self.auto_annotator = AutoAnnotator(file_path)
            
            # 更新模型状态显示
            if self.auto_annotator.is_available():
                self.model_status_label.setText("模型状态: 已加载")
                self.model_status_label.setStyleSheet("""
                    QLabel { 
                        font-weight: normal; 
                        font-size: 14px;
                        font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                        color: #28a745;
                        margin-top: 5px;
                    }
                """)
            else:
                self.model_status_label.setText("模型状态: 加载失败")
                self.model_status_label.setStyleSheet("""
                    QLabel { 
                        font-weight: normal; 
                        font-size: 14px;
                        font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                        color: #dc3545;
                        margin-top: 5px;
                    }
                """)
    
    def save_settings(self) -> None:
        """保存设置"""
        # 更新配置
        self.config["output_dir"] = self.output_dir_line_edit.text()
        self.config["model_path"] = self.model_path_line_edit.text()
        
        # 保存配置
        Utils.save_config(self.config)
        self.frame_controller.config = self.config
        
        # 如果模型路径发生变化，重新初始化自动标注器
        if self.config["model_path"] != getattr(self, '_last_model_path', ''):
            self.auto_annotator = AutoAnnotator(self.config["model_path"])
            self._last_model_path = self.config["model_path"]
            
            # 更新模型状态显示
            if self.auto_annotator.is_available():
                self.model_status_label.setText("模型状态: 已加载")
                self.model_status_label.setStyleSheet("""
                    QLabel { 
                        font-weight: normal; 
                        font-size: 14px;
                        font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                        color: #28a745;
                        margin-top: 5px;
                    }
                """)
            else:
                self.model_status_label.setText("模型状态: 加载失败")
                self.model_status_label.setStyleSheet("""
                    QLabel { 
                        font-weight: normal; 
                        font-size: 14px;
                        font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                        color: #dc3545;
                        margin-top: 5px;
                    }
                """)
        
        QMessageBox.information(self, "成功", "设置已保存！")
    
    def update_model_status(self) -> None:
        """更新模型状态显示"""
        if hasattr(self, 'model_status_label'):
            if self.auto_annotator.is_available():
                self.model_status_label.setText("模型状态: 已加载")
                self.model_status_label.setStyleSheet("""
                    QLabel { 
                        font-weight: normal; 
                        font-size: 14px;
                        font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                        color: #28a745;
                        margin-top: 5px;
                    }
                """)
            else:
                self.model_status_label.setText("模型状态: 未加载")
                self.model_status_label.setStyleSheet("""
                    QLabel { 
                        font-weight: normal; 
                        font-size: 14px;
                        font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                        color: #6c757d;
                        margin-top: 5px;
                    }
                """)

    # =============================
    # 其他逻辑保持不变
    # =============================
    def switch_function_panel(self, index: int) -> None:
        self.function_panel.setCurrentIndex(index)
        buttons = [self.video_btn, self.annotate_tab_btn, self.settings_btn_top]
        for i, btn in enumerate(buttons):
            btn.setStyleSheet(styles.get_top_button_style(selected=(i == index)))
        
        # 控制图像标注画布的编辑状态
        if hasattr(self, 'image_label') and isinstance(self.image_label, AnnotateCanvas):
            if index == 1:  # 图像标注面板
                self.image_label.set_edit_enabled(True)
                self.image_label.set_draw_mode(self.new_box_btn.isChecked())
                
                # 切换到图像标注面板时，如果当前帧不为空，进行自动标注
                if self.current_frame_mat is not None:
                    boxes = self.auto_annotator.predict(self.current_frame_mat)
                    if boxes:
                        self.image_label.load_boxes(boxes)
            else:  # 离开标注面板
                self.image_label.set_edit_enabled(False)
                self.new_box_btn.setChecked(False)
                self.image_label.set_draw_mode(False)

    def extract_frames_handler(self) -> None:
        self.config["video_path"] = self.video_line_edit.text()
        self.config["frame_interval"] = self.interval_spinbox.value()
        self.config["max_frames"] = (
            self.max_frames_spinbox.value() if self.max_frames_spinbox.value() > 0 else None
        )
        Utils.save_config(self.config)
        self.frame_controller.config = self.config
        self.extract_btn.setText("提取中...")
        self.extract_btn.setEnabled(False)
        self.frame_controller.extract_frames()

    def on_extraction_finished(self, success: bool) -> None:
        self.extract_btn.setText("提取帧")
        self.extract_btn.setEnabled(True)
        if success:
            self.frame_controller.refresh_frame_files()

    def goto_frame(self) -> None:
        target_index = self.frame_spinbox.value()
        # 预览优先：有 VideoCapture 就直接读视频帧
        if hasattr(self.frame_controller, "is_preview_mode") and self.frame_controller.is_preview_mode():
            self.frame_controller.read_frame(target_index)
        elif self.frame_controller.frame_files:
            self.frame_controller.goto_frame(target_index)

    def previous_frame(self) -> None:
        interval = self.interval_spinbox.value()
        # 预览优先
        if hasattr(self.frame_controller, "is_preview_mode") and self.frame_controller.is_preview_mode():
            self.frame_controller.previous_frame_preview(interval)
        elif self.frame_controller.frame_files:
            self.frame_controller.previous_frame(interval)

    def next_frame(self) -> None:
        interval = self.interval_spinbox.value()
        # 预览优先
        if hasattr(self.frame_controller, "is_preview_mode") and self.frame_controller.is_preview_mode():
            self.frame_controller.next_frame_preview(interval)
        elif self.frame_controller.frame_files:
            self.frame_controller.next_frame(interval)

    def on_frame_loaded(self, frame_data) -> None:
        """支持两种类型：文件路径 或 OpenCV图像矩阵"""
        import numpy as np
        pixmap = None

        # 如果是字符串路径（文件模式）
        if isinstance(frame_data, str):
            pixmap = QPixmap(frame_data)

        # 如果是 numpy.ndarray（视频预览模式）
        elif isinstance(frame_data, np.ndarray):
            # 缓存numpy数组防止GC
            self.current_frame_mat = frame_data.copy()
            rgb_frame = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            # 缓存QImage防止GC
            self.current_preview_image = q_img
            pixmap = QPixmap.fromImage(q_img)

        if pixmap is None or pixmap.isNull():
            return

        # 使用新的annotate_canvas设置图像
        self.image_label.set_image(pixmap)
        self.image_label.update()
        
        # 如果在图像标注面板且当前帧不为空，进行自动标注
        if self.function_panel.currentIndex() == 1 and self.current_frame_mat is not None:
            boxes = self.auto_annotator.predict(self.current_frame_mat)
            if boxes:
                self.image_label.load_boxes(boxes)
        
        # 更新帧信息标签
        self.update_frame_info()

    def resizeEvent(self, event) -> None:
        if getattr(self.image_label, "auto_fit", False):
            self.image_label.fit_to_window()
        super().resizeEvent(event)
        
    def toggle_draw_mode(self, checked: bool):
        """切换绘制模式"""
        if isinstance(self.image_label, AnnotateCanvas):
            self.image_label.set_draw_mode(checked)
            
    def update_frame_info(self):
        """更新帧信息标签和进度条"""
        if hasattr(self, 'frame_info_label'):
            try:
                if hasattr(self.frame_controller, 'total_frames') and self.frame_controller.total_frames > 0:
                    # 预览模式
                    current = self.frame_controller.current_frame_index
                    total = self.frame_controller.total_frames
                    self.frame_info_label.setText(f"帧：{current} / {total}")
                    
                    # 更新进度条
                    if hasattr(self, 'progress_slider') and total > 0:
                        progress = int((current / total) * 1000)  # 使用1000作为最大值
                        # 临时禁用信号，避免循环更新
                        self.progress_slider.blockSignals(True)
                        self.progress_slider.setValue(progress)
                        self.progress_slider.setMaximum(1000)
                        self.progress_slider.blockSignals(False)
                        
                elif hasattr(self.frame_controller, 'frame_files'):
                    # 文件模式
                    if self.frame_controller.frame_files:
                        current = self.frame_controller.current_frame_index
                        total = len(self.frame_controller.frame_files)
                        self.frame_info_label.setText(f"帧：{current} / {total}")
                        
                        # 更新进度条
                        if hasattr(self, 'progress_slider') and total > 0:
                            progress = int((current / total) * 1000)  # 使用1000作为最大值
                            # 临时禁用信号，避免循环更新
                            self.progress_slider.blockSignals(True)
                            self.progress_slider.setValue(progress)
                            self.progress_slider.setMaximum(1000)
                            self.progress_slider.blockSignals(False)
                    else:
                        self.frame_info_label.setText("帧：- / -")
                        if hasattr(self, 'progress_slider'):
                            self.progress_slider.setValue(0)
                else:
                    self.frame_info_label.setText("帧：- / -")
                    if hasattr(self, 'progress_slider'):
                        self.progress_slider.setValue(0)
            except Exception as e:
                print(f"更新帧信息时出错: {e}")
                self.frame_info_label.setText("帧：- / -")
                if hasattr(self, 'progress_slider'):
                    self.progress_slider.setValue(0)
                    
    def on_progress_pressed(self):
        """进度条开始拖动"""
        self.is_slider_dragging = True
        
    def on_progress_released(self):
        """进度条拖动结束"""
        self.is_slider_dragging = False
        # 拖动结束时才真正跳转帧
        self._jump_to_progress_frame()
        
    def on_progress_changed(self, value):
        """进度条值改变事件处理"""
        # 使用防抖机制，避免频繁跳转
        if not self.is_slider_dragging:
            # 停止之前的定时器
            self.progress_timer.stop()
            # 启动新的定时器，延迟100ms执行
            self.progress_timer.start(100)
            
    def _jump_to_progress_frame(self):
        """根据进度条值跳转到对应帧"""
        try:
            value = self.progress_slider.value()
            if hasattr(self.frame_controller, 'total_frames') and self.frame_controller.total_frames > 0:
                # 预览模式
                target_frame = int((value / 1000) * self.frame_controller.total_frames)
                target_frame = max(0, min(target_frame, self.frame_controller.total_frames - 1))
                # 临时禁用进度条更新，避免循环更新
                self.progress_slider.blockSignals(True)
                self.frame_controller.read_frame(target_frame)
                self.progress_slider.blockSignals(False)
            elif hasattr(self.frame_controller, 'frame_files') and self.frame_controller.frame_files:
                # 文件模式
                target_frame = int((value / 1000) * len(self.frame_controller.frame_files))
                target_frame = max(0, min(target_frame, len(self.frame_controller.frame_files) - 1))
                # 临时禁用进度条更新，避免循环更新
                self.progress_slider.blockSignals(True)
                self.frame_controller.load_frame(target_frame)
                self.progress_slider.blockSignals(False)
        except Exception as e:
            print(f"进度条跳转时出错: {e}")
            
    def keyPressEvent(self, event):
        """处理键盘事件"""
        # 将键盘事件传递给图像标注画布
        if hasattr(self, 'image_label') and isinstance(self.image_label, AnnotateCanvas):
            self.image_label.keyPressEvent(event)
        super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())