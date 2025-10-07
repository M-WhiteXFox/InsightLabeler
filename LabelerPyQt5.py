"""
主窗口模块
负责UI界面的创建和用户交互处理
"""

import sys
import os
from typing import Dict, Any
from functools import partial
import label2yolo

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, \
    QSizePolicy, QFileDialog, QLineEdit, QSpinBox, QDoubleSpinBox, QStackedWidget, QGroupBox, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer

import Utils
import ui_components
from controllers import FrameController
import styles
import cv2

from annotate_canvas import AnnotateCanvas
from auto_annotator import AutoAnnotator
from label2yolo import Labelme2Yolo
from training_panel import TrainingPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.config = Utils.load_config()
            self.frame_controller = FrameController()
            
            # 初始化自动标注器
            self.auto_annotator = AutoAnnotator(self.config.get("model_path", ""))
            self._last_model_path = self.config.get("model_path", "")
        except Exception as e:
            print(f"初始化主窗口时出错: {e}")
            # 使用默认配置
            self.config = {"video_path": "", "output_dir": "./output", "model_path": ""}
            self.frame_controller = FrameController()
            self.auto_annotator = AutoAnnotator("")
            self._last_model_path = ""

        # ====== UI组件引用 ======
        self.image_label: QLabel = None
        self.function_panel: QStackedWidget = None
        self.file_line_edit: QLineEdit = None
        self.video_mode_btn: QPushButton = None
        self.folder_mode_btn: QPushButton = None
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
        self.setWindowTitle("InsightLabeler - 智能视频/图片标注工具")
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

        # 选中第一个按钮
        self.switch_function_panel(0)

        # 优先检查是否有视频文件或照片文件夹，如果有则进入相应模式
        video_path = self.config.get("video_path", "")
        if video_path and os.path.exists(video_path):
            # 检查是文件还是文件夹
            if os.path.isfile(video_path):
                # 视频文件模式
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
            elif os.path.isdir(video_path):
                # 照片文件夹模式
                try:
                    self.frame_controller.open_image_folder(video_path)
                    # 清空磁盘帧列表，强制进入文件夹模式
                    self.frame_controller.frame_files = []
                    # 读取首张图片
                    self.frame_controller.load_image_from_folder(0)
                except Exception as e:
                    print(f"自动加载照片文件夹失败: {e}")
                    # 如果文件夹加载失败，回退到文件模式
                    if self.frame_controller.frame_files:
                        self.frame_controller.load_frame(0)
        elif self.frame_controller.frame_files:
            # 没有视频文件时，使用磁盘帧文件
            self.frame_controller.load_frame(0)

    def __del__(self):
        """析构函数，确保资源正确释放"""
        try:
            if hasattr(self, 'frame_controller'):
                self.frame_controller.close_video()
        except Exception as e:
            print(f"释放资源时出错: {e}")

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

        self.video_annotate_btn = ui_components.create_top_button("视频/图片标注")
        self.video_annotate_btn.clicked.connect(lambda: self.switch_function_panel(0))
        button_layout.addWidget(self.video_annotate_btn)

        self.training_btn = ui_components.create_top_button("模型训练")
        self.training_btn.clicked.connect(lambda: self.switch_function_panel(1))
        button_layout.addWidget(self.training_btn)

        self.label2yolo = ui_components.create_top_button("格式转换")
        self.label2yolo.clicked.connect(lambda: self.switch_function_panel(2))
        button_layout.addWidget(self.label2yolo)

        self.settings_btn_top = ui_components.create_top_button("设置")
        self.settings_btn_top.clicked.connect(lambda: self.switch_function_panel(3))
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
        """创建功能面板区域"""
        # 创建功能面板容器
        self.function_panel = ui_components.create_function_panel_area(parent_layout)
        
        # 创建各个功能面板
        self._create_video_annotate_panel()
        self._create_training_panel()
        self._create_format_conversion_panel()
        self._create_settings_panel()
        
        # 初始化面板状态
        self._initialize_panel_states()
        
        # 将功能面板添加到父布局
        parent_layout.addWidget(self.function_panel, stretch=1)

    def _create_video_annotate_panel(self) -> None:
        """创建视频标注面板"""
        # 创建视频标注整合面板
        video_annotate_panel_data = ui_components.create_video_annotate_panel(
            self.config,
            self.select_file,
            self.extract_frames_handler
        )
        self.video_annotate_panel = video_annotate_panel_data[0]
        
        # 解包控件引用
        (self.file_line_edit, self.video_mode_btn, self.folder_mode_btn, 
         self.interval_spinbox, self.max_frames_spinbox, self.max_frames_set_btn,
         self.extract_btn, self.prev_frame_btn, self.next_frame_btn,
         self.frame_spinbox, self.goto_btn, self.frame_info_label, 
         self.save_prediction_btn, self.progress_slider, self.new_box_btn, 
         self.refresh_btn, self.model_path_line_edit, self.model_browse_btn, 
         self.model_status_label, self.prediction_switch, self.confidence_slider, 
         self.confidence_value_label) = video_annotate_panel_data[1:]

        # 连接信号槽
        self._connect_video_annotate_signals()
        
        # 初始化进度条相关状态
        self._initialize_progress_controls()
        
        # 添加到功能面板
        self.function_panel.addWidget(self.video_annotate_panel)

    def _connect_video_annotate_signals(self) -> None:
        """连接视频标注面板的信号槽"""
        # 视频处理相关信号
        self.prev_frame_btn.clicked.connect(self.previous_frame)
        self.next_frame_btn.clicked.connect(self.next_frame)
        self.goto_btn.clicked.connect(self.goto_frame)
        self.max_frames_set_btn.clicked.connect(self.set_max_frames_limit)
        self.save_prediction_btn.clicked.connect(self.save_prediction_results)
        
        # 进度条信号
        self.progress_slider.sliderPressed.connect(self.on_progress_pressed)
        self.progress_slider.sliderReleased.connect(self.on_progress_released)
        self.progress_slider.valueChanged.connect(self.on_progress_changed)
        
        # 标注相关信号
        self.new_box_btn.toggled.connect(self.toggle_draw_mode)
        self.refresh_btn.clicked.connect(self.refresh_prediction)
        
        # 模型设置相关信号
        self.model_browse_btn.clicked.connect(self.select_model_file_annotate)
        self.prediction_switch.toggled.connect(self.toggle_prediction_switch)
        self.confidence_slider.valueChanged.connect(self.update_confidence_value)
        
        # 模式切换信号
        self.video_mode_btn.clicked.connect(self.on_mode_changed)
        self.folder_mode_btn.clicked.connect(self.on_mode_changed)

    def _initialize_progress_controls(self) -> None:
        """初始化进度条相关控件"""
        # 添加拖动状态标志
        self.is_slider_dragging = False
        
        # 添加防抖定时器
        self.progress_timer = QTimer()
        self.progress_timer.setSingleShot(True)
        self.progress_timer.timeout.connect(self._jump_to_progress_frame)

    def _create_training_panel(self) -> None:
        """创建训练面板"""
        self.training_panel = TrainingPanel(self.config)
        self.function_panel.addWidget(self.training_panel)

    def _create_format_conversion_panel(self) -> None:
        """创建格式转换面板"""
        self.format_conversion_panel = QWidget()
        layout = QVBoxLayout(self.format_conversion_panel)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("Labelme转YOLO格式")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 15px;
            }
        """)
        layout.addWidget(title_label)
        
        # 输入数据集选择组
        input_group = QGroupBox("输入数据集")
        input_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                color: #2c3e50;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
            }
        """)
        input_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        input_layout = QVBoxLayout(input_group)
        input_layout.setSpacing(10)
        
        # 输入数据集路径
        input_path_layout = QHBoxLayout()
        input_path_layout.setSpacing(8)
        input_path_label = QLabel("Labelme数据集路径:")
        input_path_label.setStyleSheet("""
            QLabel { 
                font-weight: normal; 
                font-size: 14px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        self.labelme_dir_line_edit = QLineEdit()
        self.labelme_dir_line_edit.setPlaceholderText("请选择Labelme数据集文件夹")
        self.labelme_dir_line_edit.setStyleSheet("""
            QLineEdit { 
                font-size: 14px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                padding: 6px;
            }
        """)
        self.labelme_browse_btn = ui_components.create_button("浏览", styles.COLORS["primary"], "small")
        
        input_path_layout.addWidget(input_path_label)
        input_path_layout.addWidget(self.labelme_dir_line_edit)
        input_path_layout.addWidget(self.labelme_browse_btn)
        input_layout.addLayout(input_path_layout)
        
        layout.addWidget(input_group)
        
        # 输出数据集选择组
        output_group = QGroupBox("输出数据集")
        output_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                color: #2c3e50;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
            }
        """)
        output_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        output_layout = QVBoxLayout(output_group)
        output_layout.setSpacing(10)
        
        # 输出数据集路径
        output_path_layout = QHBoxLayout()
        output_path_layout.setSpacing(8)
        output_path_label = QLabel("YOLO数据集输出路径:")
        output_path_label.setStyleSheet("""
            QLabel { 
                font-weight: normal; 
                font-size: 14px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        self.yolo_dir_line_edit = QLineEdit()
        self.yolo_dir_line_edit.setPlaceholderText("请选择YOLO数据集输出文件夹")
        self.yolo_dir_line_edit.setStyleSheet("""
            QLineEdit { 
                font-size: 14px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                padding: 6px;
            }
        """)
        self.yolo_browse_btn = ui_components.create_button("浏览", styles.COLORS["primary"], "small")
        
        output_path_layout.addWidget(output_path_label)
        output_path_layout.addWidget(self.yolo_dir_line_edit)
        output_path_layout.addWidget(self.yolo_browse_btn)
        output_layout.addLayout(output_path_layout)
        
        layout.addWidget(output_group)
        
        # 参数设置组
        params_group = QGroupBox("转换参数")
        params_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                color: #2c3e50;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
            }
        """)
        params_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        params_layout = QVBoxLayout(params_group)
        params_layout.setSpacing(10)
        
        # 标签文件路径
        label_path_layout = QHBoxLayout()
        label_path_layout.setSpacing(8)
        label_path_label = QLabel("标签文件路径:")
        label_path_label.setStyleSheet("""
            QLabel { 
                font-weight: normal; 
                font-size: 14px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        self.label_path_line_edit = QLineEdit()
        self.label_path_line_edit.setPlaceholderText("请选择标签文件")
        self.label_path_line_edit.setStyleSheet("""
            QLineEdit { 
                font-size: 14px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                padding: 6px;
            }
        """)
        self.label_path_browse_btn = ui_components.create_button("浏览", styles.COLORS["primary"], "small")
        
        label_path_layout.addWidget(label_path_label)
        label_path_layout.addWidget(self.label_path_line_edit)
        label_path_layout.addWidget(self.label_path_browse_btn)
        params_layout.addLayout(label_path_layout)
        
        # 验证集比例和线程数
        val_thread_layout = QHBoxLayout()
        val_thread_layout.setSpacing(15)
        
        # 验证集比例
        val_size_layout = QVBoxLayout()
        val_size_label = QLabel("验证集比例 (0-1):")
        val_size_label.setStyleSheet("""
            QLabel { 
                font-weight: normal; 
                font-size: 14px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        self.val_size_spinbox = QDoubleSpinBox()
        self.val_size_spinbox.setMinimum(0.0)
        self.val_size_spinbox.setMaximum(1.0)
        self.val_size_spinbox.setSingleStep(0.1)
        self.val_size_spinbox.setValue(0.2)
        self.val_size_spinbox.setDecimals(2)
        self.val_size_spinbox.setStyleSheet("""
            QDoubleSpinBox { 
                font-size: 14px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                padding: 6px;
            }
        """)
        val_size_layout.addWidget(val_size_label)
        val_size_layout.addWidget(self.val_size_spinbox)
        
        # 线程数
        thread_layout = QVBoxLayout()
        thread_label = QLabel("线程数:")
        thread_label.setStyleSheet("""
            QLabel { 
                font-weight: normal; 
                font-size: 14px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        self.thread_num_spinbox = QSpinBox()
        self.thread_num_spinbox.setMinimum(1)
        self.thread_num_spinbox.setMaximum(32)
        self.thread_num_spinbox.setValue(15)
        self.thread_num_spinbox.setStyleSheet("""
            QSpinBox { 
                font-size: 14px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                padding: 6px;
            }
        """)
        thread_layout.addWidget(thread_label)
        thread_layout.addWidget(self.thread_num_spinbox)
        
        val_thread_layout.addLayout(val_size_layout)
        val_thread_layout.addLayout(thread_layout)
        params_layout.addLayout(val_thread_layout)
        
        layout.addWidget(params_group)
        
        # 转换按钮
        self.convert_btn = ui_components.create_button("开始转换", styles.COLORS["primary"], "large")
        self.convert_btn.setStyleSheet(styles.get_button_style("large", styles.COLORS["primary"]) + """
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                min-height: 45px;
            }
        """)
        self.convert_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(self.convert_btn)
        
        # 进度显示
        self.convert_progress_label = QLabel("准备就绪")
        self.convert_progress_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                color: #6c757d;
                margin-top: 10px;
            }
        """)
        layout.addWidget(self.convert_progress_label)
        
        # 占位空间
        layout.addStretch()
        
        # 设置面板的尺寸策略
        self.format_conversion_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.function_panel.addWidget(self.format_conversion_panel)
        
        # 连接信号槽
        self._connect_format_conversion_signals()

    def _create_settings_panel(self) -> None:
        """创建设置面板"""
        settings_panel_data = ui_components.create_settings_panel(self.config)
        self.settings_panel = settings_panel_data[0]
        
        # 解包控件引用
        (self.output_dir_line_edit, self.settings_btn,
         self.output_browse_btn, self.model_path_line_edit, 
         self.model_browse_btn, self.model_status_label,
         self.current_video_path_label) = settings_panel_data[1:]
        
        # 连接信号槽
        self.output_browse_btn.clicked.connect(self.select_output_dir)
        self.model_browse_btn.clicked.connect(self.select_model_file)
        self.settings_btn.clicked.connect(self.save_settings)
        
        # 添加到功能面板
        self.function_panel.addWidget(self.settings_panel)

    def _initialize_panel_states(self) -> None:
        """初始化面板状态"""
        # 初始化模型状态显示
        self.update_model_status()
        
        # 初始化预测开关状态
        self.prediction_switch.setChecked(self.config.get("prediction_enabled", False))
        self.toggle_prediction_switch(self.prediction_switch.isChecked())
        
        # 初始化置信度值显示
        confidence_value = int(self.config.get("confidence_threshold", 0.5) * 100)
        self.confidence_slider.setValue(confidence_value)
        self.confidence_value_label.setText(f"{confidence_value}%")
        
        # 初始化当前视频输出目录显示
        self.update_current_video_path_display()
        
        # 初始化模式状态
        self.on_mode_changed()

    def _connect_format_conversion_signals(self) -> None:
        """连接格式转换面板的信号槽"""
        self.labelme_browse_btn.clicked.connect(self.select_labelme_dir)
        self.yolo_browse_btn.clicked.connect(self.select_yolo_dir)
        self.label_path_browse_btn.clicked.connect(self.select_label_path)
        self.convert_btn.clicked.connect(self.start_labelme_to_yolo_conversion)

    # =============================
    # 格式转换功能
    # =============================
    def select_labelme_dir(self) -> None:
        """选择Labelme数据集目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择Labelme数据集文件夹", "./")
        if directory:
            normalized_path = self.normalize_path(directory)
            self.labelme_dir_line_edit.setText(normalized_path)
    
    def select_yolo_dir(self) -> None:
        """选择YOLO数据集输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择YOLO数据集输出文件夹", "./")
        if directory:
            normalized_path = self.normalize_path(directory)
            self.yolo_dir_line_edit.setText(normalized_path)
    
    def select_label_path(self) -> None:
        """选择标签文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择标签文件", "./", 
            "文本文件 (*.txt);;所有文件 (*)"
        )
        if file_path:
            normalized_path = self.normalize_path(file_path)
            self.label_path_line_edit.setText(normalized_path)
    
    def start_labelme_to_yolo_conversion(self) -> None:
        """开始Labelme到YOLO格式转换"""
        try:
            # 获取参数
            labelme_dir = self.labelme_dir_line_edit.text().strip()
            save_dir = self.yolo_dir_line_edit.text().strip()
            label_path = self.label_path_line_edit.text().strip()
            val_size = self.val_size_spinbox.value()
            thread_num = self.thread_num_spinbox.value()
            
            # 验证参数
            if not labelme_dir or not save_dir or not label_path:
                QMessageBox.warning(self, "错误", "请填写所有必需的路径")
                return
            
            if not os.path.exists(labelme_dir):
                QMessageBox.warning(self, "错误", "Labelme数据集路径不存在")
                return
            
            if not os.path.exists(label_path):
                QMessageBox.warning(self, "错误", "标签文件路径不存在")
                return
            
            # 创建输出目录
            os.makedirs(save_dir, exist_ok=True)
            
            # 更新UI状态
            self.convert_progress_label.setText("正在转换...")
            self.convert_btn.setEnabled(False)
            self.convert_btn.setText("转换中...")
            
            # 执行转换
            success = label2yolo.convert_labelme_to_yolo(
                labelme_dir=labelme_dir,
                save_dir=save_dir,
                label_path=label_path,
                val_size=val_size,
                thread_num=thread_num
            )
            
            if success:
                self.convert_progress_label.setText("转换完成！")
                QMessageBox.information(self, "成功", f"Labelme到YOLO格式转换完成！\n输出目录: {save_dir}")
            else:
                self.convert_progress_label.setText("转换失败")
                QMessageBox.warning(self, "错误", "格式转换失败，请检查输入数据")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"转换过程中出错: {str(e)}")
            self.convert_progress_label.setText("转换出错")
        finally:
            self.convert_btn.setEnabled(True)
            self.convert_btn.setText("开始转换")

    # =============================
    # 辅助方法
    # =============================

    # =============================
    # 文件选择与事件响应
    # =============================
    def select_file(self, line_edit: QLineEdit, key: str, video_mode_btn: QPushButton = None, folder_mode_btn: QPushButton = None) -> None:
        """选择视频文件或照片文件夹"""
        # 根据当前选择的模式决定文件选择类型
        if folder_mode_btn and folder_mode_btn.isChecked():
            # 照片文件夹模式
            folder_path = QFileDialog.getExistingDirectory(
                self, "选择照片文件夹", "./"
            )
            if folder_path:
                # 标准化路径
                normalized_path = self.normalize_path(folder_path)
                line_edit.setText(normalized_path)
                self.config[key] = normalized_path
                Utils.save_config(self.config)
                self.frame_controller.config = self.config
                
                try:
                    # 打开照片文件夹进入"文件夹模式"
                    self.frame_controller.open_image_folder(folder_path)
                    # 清空磁盘帧列表，强制上下张/跳转走文件夹模式
                    self.frame_controller.frame_files = []
                    # 读取首张图片
                    self.frame_controller.load_frame(0)
                    # 更新当前视频输出目录显示
                    self.update_current_video_path_display()
                    # 自动设置最大帧数为文件夹中的图片数量
                    self.auto_set_max_frames()
                    # 更新模式状态
                    self.on_mode_changed()
                except Exception as e:
                    QMessageBox.warning(self, "错误", str(e))
        else:
            # 视频文件模式
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择视频文件", "./", "视频文件 (*.mp4 *.avi *.mov);;所有文件 (*)"
            )

            if file_path:
                # 标准化路径
                normalized_path = self.normalize_path(file_path)
                line_edit.setText(normalized_path)
                self.config[key] = normalized_path
                Utils.save_config(self.config)
                self.frame_controller.config = self.config

                try:
                    # 打开视频进入"预览模式"
                    self.frame_controller.open_video(file_path)
                    # 清空磁盘帧列表，强制上下张/跳转走内存预览
                    self.frame_controller.frame_files = []
                    # 读取首帧（从视频开头开始）
                    self.frame_controller.read_frame(0)
                    # 更新当前视频输出目录显示
                    self.update_current_video_path_display()
                    # 自动设置最大帧数为视频总帧数
                    self.auto_set_max_frames()
                    # 更新模式状态
                    self.on_mode_changed()
                except Exception as e:
                    QMessageBox.warning(self, "错误", str(e))

    def save_prediction_results(self):
        """保存当前帧的标注框结果（包括AI预测和手动创建的标注框）"""
        try:
            # 获取当前帧数据
            current_frame_mat = None
            
            # 照片文件夹模式：从当前图片文件读取
            if hasattr(self.frame_controller, "is_image_folder_mode") and self.frame_controller.is_image_folder_mode():
                if (hasattr(self.frame_controller, 'current_frame_index') and 
                    hasattr(self.frame_controller, 'image_files') and 
                    self.frame_controller.current_frame_index < len(self.frame_controller.image_files)):
                    current_image_path = self.frame_controller.image_files[self.frame_controller.current_frame_index]
                    current_frame_mat = cv2.imread(current_image_path)
            # 视频模式：使用缓存的帧数据
            elif hasattr(self, 'current_frame_mat') and self.current_frame_mat is not None:
                current_frame_mat = self.current_frame_mat
            
            if current_frame_mat is None:
                QMessageBox.warning(self, "提示", "当前没有可用的帧数据")
                return
            
            # 获取画布上的所有标注框（包括手动创建的和AI预测的）
            boxes = []
            if hasattr(self.image_label, 'get_boxes'):
                boxes = self.image_label.get_boxes()
            
            # 如果没有标注框，尝试获取AI预测结果
            if not boxes and self.prediction_switch.isChecked() and self.auto_annotator.is_available():
                confidence_threshold = self.config.get("confidence_threshold", 0.5)
                boxes = self.auto_annotator.predict(current_frame_mat, confidence_threshold)
            
            if not boxes:
                QMessageBox.information(self, "提示", "当前帧没有任何标注框，请先创建标注框或开启AI预测功能")
                return
            
            # 获取输出名称并创建文件夹结构
            input_path = self.config.get("video_path", "")
            if input_path:
                if os.path.isfile(input_path):
                    # 视频文件模式：从视频路径中提取文件名
                    output_name = os.path.splitext(os.path.basename(input_path))[0]
                elif os.path.isdir(input_path):
                    # 照片文件夹模式：从文件夹路径中提取文件夹名
                    output_name = os.path.basename(input_path.rstrip(os.sep))
                else:
                    output_name = "unknown_input"
            else:
                output_name = "unknown_input"
            
            # 创建基于输入名称的文件夹结构
            base_output_dir = self.config.get("output_dir", "./output")
            output_dir = os.path.join(base_output_dir, output_name)
            
            # 确保目录存在
            os.makedirs(output_dir, exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)
            
            # 获取当前帧索引
            current_frame_index = getattr(self.frame_controller, 'current_frame_index', 0)
            
            # 保存YOLO格式的txt文件
            txt_filename = f"frame_{current_frame_index:06d}.txt"
            txt_path = os.path.join(output_dir, txt_filename)
            
            # 保存图片文件
            image_filename = f"frame_{current_frame_index:06d}.jpg"
            image_path = os.path.join(output_dir, image_filename)
            
            # 获取图像尺寸
            h, w = current_frame_mat.shape[:2]
            
            # 保存图片
            cv2.imwrite(image_path, current_frame_mat)
            
            # 写入YOLO格式数据
            with open(txt_path, 'w') as f:
                for box in boxes:
                    x1, y1, x2, y2, label = box
                    
                    # 转换为YOLO格式 (center_x, center_y, width, height) 归一化
                    center_x = (x1 + x2) / 2.0 / w
                    center_y = (y1 + y2) / 2.0 / h
                    width = (x2 - x1) / w
                    height = (y2 - y1) / h
                    
                    # 提取类别ID（假设所有检测都是同一类别，类别ID为0）
                    class_id = 0
                    
                    # 写入YOLO格式行：class_id center_x center_y width height
                    f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
            
            QMessageBox.information(self, "成功", f"标注结果已保存到输出文件夹:\n输入: {output_name}\n图片: {image_path}\n标注: {txt_path}\n共保存 {len(boxes)} 个标注框")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存预测结果时出错: {str(e)}")

    def select_output_dir(self) -> None:
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录", "./")
        if directory:
            # 标准化路径
            normalized_path = self.normalize_path(directory)
            self.output_dir_line_edit.setText(normalized_path)
            self.config["output_dir"] = normalized_path
            Utils.save_config(self.config)
            self.frame_controller.config = self.config
            # 更新当前视频输出目录显示
            self.update_current_video_path_display()
    
    
    def select_model_file(self) -> None:
        """选择YOLO模型文件（设置面板）"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择YOLO模型文件", "./", "PyTorch模型文件 (*.pt);;所有文件 (*)"
        )
        if file_path:
            # 标准化路径
            normalized_path = self.normalize_path(file_path)
            self.model_path_line_edit.setText(normalized_path)
            self.config["model_path"] = normalized_path
            Utils.save_config(self.config)
            
            # 重新初始化自动标注器
            self.auto_annotator = AutoAnnotator(normalized_path)
            
            # 更新模型状态显示
            self.update_model_status()
    
    def select_model_file_annotate(self) -> None:
        """选择YOLO模型文件（标注面板）"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择YOLO模型文件", "./", "PyTorch模型文件 (*.pt);;所有文件 (*)"
        )
        if file_path:
            # 标准化路径
            normalized_path = self.normalize_path(file_path)
            self.model_path_line_edit.setText(normalized_path)
            self.config["model_path"] = normalized_path
            Utils.save_config(self.config)
            
            # 重新初始化自动标注器
            print(f"正在加载新模型: {normalized_path}")
            self.auto_annotator = AutoAnnotator(normalized_path)
            
            # 检查模型是否成功加载
            if self.auto_annotator.is_available():
                print(f"模型加载成功，类别数量: {len(self.auto_annotator.class_names)}")
                print(f"类别名称: {self.auto_annotator.class_names}")
            else:
                print("模型加载失败")
            
            # 更新模型状态显示
            self.update_model_status_annotate()
            
            # 如果当前在视频标注面板且有帧数据，立即刷新预测
            if (self.function_panel.currentIndex() == 0 and 
                hasattr(self, 'current_frame_mat') and 
                self.current_frame_mat is not None and 
                self.prediction_switch.isChecked()):
                print("模型更新后立即刷新预测...")
                self.refresh_prediction()
    
    def toggle_prediction_switch(self, checked: bool) -> None:
        """切换预测开关"""
        if checked:
            self.prediction_switch.setText("开启")
            self.prediction_switch.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 14px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
        else:
            self.prediction_switch.setText("关闭")
            self.prediction_switch.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 14px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
        
        # 保存预测开关状态
        self.config["prediction_enabled"] = checked
        Utils.save_config(self.config)
    
    def update_confidence_value(self, value: int) -> None:
        """更新置信度值显示"""
        self.confidence_value_label.setText(f"{value}%")
        self.config["confidence_threshold"] = value / 100.0
        Utils.save_config(self.config)
    
    def on_mode_changed(self) -> None:
        """处理模式切换事件"""
        if self.folder_mode_btn.isChecked():
            # 照片文件夹模式：禁用提取帧按钮
            self.extract_btn.setEnabled(False)
            self.extract_btn.setText("照片文件夹模式无需提取")
            self.extract_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-size: 16px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                }
            """)
        else:
            # 视频文件模式：启用提取帧按钮
            self.extract_btn.setEnabled(True)
            self.extract_btn.setText("提取帧")
            self.extract_btn.setStyleSheet(styles.get_button_style("medium", styles.COLORS["primary"]) + """
                QPushButton {
                    font-size: 16px;
                    font-weight: bold;
                    min-height: 35px;
                }
            """)
    
    def normalize_path(self, path: str) -> str:
        """标准化路径格式，统一使用正斜杠"""
        if not path:
            return ""
        # 将反斜杠转换为正斜杠，并处理重复的斜杠
        normalized = path.replace("\\", "/")
        # 处理重复的斜杠
        while "//" in normalized:
            normalized = normalized.replace("//", "/")
        return normalized
    
    def get_current_video_output_dir(self) -> str:
        """获取当前视频的输出目录"""
        video_path = self.config.get("video_path", "")
        if video_path:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
        else:
            video_name = "unknown_video"
        
        base_output_dir = self.config.get("output_dir", "./output")
        return os.path.join(base_output_dir, video_name)
    
    def update_current_video_path_display(self) -> None:
        """更新当前视频输出目录显示"""
        if hasattr(self, 'current_video_path_label'):
            video_path = self.config.get("video_path", "")
            if video_path:
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                base_output_dir = self.config.get("output_dir", "./output")
                video_output_dir = os.path.join(base_output_dir, video_name)
                
                # 标准化路径显示
                normalized_path = self.normalize_path(video_output_dir)
                
                # 显示完整的文件夹结构
                display_text = f"{normalized_path}\n├── images/\n└── labels/"
                self.current_video_path_label.setText(display_text)
                self.current_video_path_label.setStyleSheet("""
                    QLabel { 
                        font-weight: normal; 
                        font-size: 14px;
                        font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                        color: #2c3e50;
                        background-color: #e8f5e8;
                        border: 1px solid #28a745;
                        border-radius: 4px;
                        padding: 8px;
                        margin-top: 5px;
                    }
                """)
            else:
                self.current_video_path_label.setText("未选择视频")
                self.current_video_path_label.setStyleSheet("""
                    QLabel { 
                        font-weight: normal; 
                        font-size: 14px;
                        font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                        color: #6c757d;
                        background-color: #f8f9fa;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        padding: 8px;
                        margin-top: 5px;
                    }
                """)
    
    def set_max_frames_limit(self) -> None:
        """设置最大帧数限制为当前视频的总帧数或照片文件夹中的图片数量"""
        # 检查照片文件夹模式
        if hasattr(self.frame_controller, "is_image_folder_mode") and self.frame_controller.is_image_folder_mode():
            try:
                total_frames = self.frame_controller.total_frames
                if total_frames <= 0:
                    QMessageBox.warning(self, "错误", "无法获取图片数量信息")
                    return
                
                # 更新SpinBox的最大值
                self.max_frames_spinbox.setMaximum(total_frames)
                
                # 设置当前值为图片总数
                self.max_frames_spinbox.setValue(total_frames)
                
                # 显示成功消息
                QMessageBox.information(
                    self, 
                    "设置成功", 
                    f"最大图片数限制已设置为照片文件夹中的图片数量: {total_frames}"
                )
                return
            except Exception as e:
                QMessageBox.warning(self, "错误", f"获取图片数量时出错: {str(e)}")
                return
        
        # 检查是否有视频文件
        video_path = self.config.get("video_path", "")
        if not video_path:
            QMessageBox.warning(self, "警告", "请先选择视频文件或照片文件夹")
            return
        
        try:
            # 获取视频的总帧数
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                QMessageBox.warning(self, "错误", "无法打开视频文件")
                return
            
            # 获取视频的总帧数
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            
            if total_frames <= 0:
                QMessageBox.warning(self, "错误", "无法获取视频帧数信息")
                return
            
            # 更新SpinBox的最大值
            self.max_frames_spinbox.setMaximum(total_frames)
            
            # 设置当前值为视频总帧数
            self.max_frames_spinbox.setValue(total_frames)
            
            # 显示成功消息
            QMessageBox.information(
                self, 
                "设置成功", 
                f"最大帧数限制已设置为当前视频的总帧数: {total_frames}"
            )
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"获取视频帧数时出错: {str(e)}")
    
    def auto_set_max_frames(self) -> None:
        """自动设置最大帧数为当前视频的总帧数或照片文件夹中的图片数量"""
        try:
            # 照片文件夹模式
            if hasattr(self.frame_controller, "is_image_folder_mode") and self.frame_controller.is_image_folder_mode():
                total_frames = self.frame_controller.total_frames
                if total_frames > 0:
                    # 更新SpinBox的最大值
                    self.max_frames_spinbox.setMaximum(total_frames)
                    # 设置当前值为图片总数
                    self.max_frames_spinbox.setValue(total_frames)
                    print(f"自动设置最大帧数为照片文件夹中的图片数量: {total_frames}")
                return
            
            # 视频模式
            video_path = self.config.get("video_path", "")
            if not video_path:
                return
                
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return
            
            # 获取视频的总帧数
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            
            if total_frames > 0:
                # 更新SpinBox的最大值
                self.max_frames_spinbox.setMaximum(total_frames)
                # 设置当前值为视频总帧数
                self.max_frames_spinbox.setValue(total_frames)
                print(f"自动设置最大帧数为: {total_frames}")
                
        except Exception as e:
            print(f"自动设置最大帧数时出错: {str(e)}")
    
    def refresh_prediction(self) -> None:
        """刷新预测结果"""
        print("=== 刷新预测开始 ===")
        print(f"当前面板索引: {self.function_panel.currentIndex()}")
        print(f"当前帧数据: {self.current_frame_mat is not None}")
        print(f"预测开关状态: {self.prediction_switch.isChecked()}")
        print(f"模型可用性: {self.auto_annotator.is_available()}")
        
        # 检查是否在视频标注面板且当前帧不为空
        if (self.function_panel.currentIndex() == 0 and self.current_frame_mat is not None):
            # 清空当前标注框
            if hasattr(self.image_label, 'clear_boxes'):
                self.image_label.clear_boxes()
                print("已清空当前标注框")
            
            # 如果预测开关开启，重新进行预测
            if self.prediction_switch.isChecked():
                confidence_threshold = self.config.get("confidence_threshold", 0.5)
                print(f"使用置信度阈值: {confidence_threshold}")
                print(f"当前帧形状: {self.current_frame_mat.shape}")
                
                boxes = self.auto_annotator.predict(self.current_frame_mat, confidence_threshold)
                print(f"预测结果: {len(boxes)} 个检测框")
                
                if boxes:
                    self.image_label.load_boxes(boxes)
                    print(f"刷新预测完成，检测到 {len(boxes)} 个目标")
                    for i, box in enumerate(boxes):
                        print(f"  目标 {i+1}: {box}")
                else:
                    print("刷新预测完成，未检测到目标")
            else:
                print("预测开关已关闭，跳过预测")
        else:
            if self.function_panel.currentIndex() != 0:
                print("当前不在视频标注面板")
            if self.current_frame_mat is None:
                print("当前帧数据为空")
        print("=== 刷新预测结束 ===")
    
    def save_settings(self) -> None:
        """保存设置"""
        # 更新配置并标准化路径
        self.config["output_dir"] = self.normalize_path(self.output_dir_line_edit.text())
        self.config["model_path"] = self.normalize_path(self.model_path_line_edit.text())
        
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
        """更新模型状态显示（设置面板）"""
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
    
    def update_model_status_annotate(self) -> None:
        """更新模型状态显示（标注面板）"""
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

    # =============================
    # 其他逻辑保持不变
    # =============================
    def switch_function_panel(self, index: int) -> None:
        self.function_panel.setCurrentIndex(index)
        buttons = [self.video_annotate_btn, self.training_btn, self.label2yolo, self.settings_btn_top]
        for i, btn in enumerate(buttons):
            btn.setStyleSheet(styles.get_top_button_style(selected=(i == index)))
        
        # 控制图像标注画布的编辑状态
        if hasattr(self, 'image_label') and isinstance(self.image_label, AnnotateCanvas):
            if index == 0:  # 视频标注面板
                self.image_label.set_edit_enabled(True)
                self.image_label.set_draw_mode(self.new_box_btn.isChecked())
                
                # 切换到视频标注面板时，如果当前帧不为空且预测开关开启，进行自动标注
                if self.current_frame_mat is not None and self.prediction_switch.isChecked():
                    confidence_threshold = self.config.get("confidence_threshold", 0.5)
                    boxes = self.auto_annotator.predict(self.current_frame_mat, confidence_threshold)
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
        # 照片文件夹模式优先
        if hasattr(self.frame_controller, "is_image_folder_mode") and self.frame_controller.is_image_folder_mode():
            self.frame_controller.goto_image_from_folder(target_index)
        # 预览模式：有 VideoCapture 就直接读视频帧
        elif hasattr(self.frame_controller, "is_preview_mode") and self.frame_controller.is_preview_mode():
            self.frame_controller.read_frame(target_index)
        elif self.frame_controller.frame_files:
            self.frame_controller.goto_frame(target_index)

    def previous_frame(self) -> None:
        interval = self.interval_spinbox.value()
        # 照片文件夹模式优先
        if hasattr(self.frame_controller, "is_image_folder_mode") and self.frame_controller.is_image_folder_mode():
            self.frame_controller.previous_image_from_folder(interval)
        # 预览模式
        elif hasattr(self.frame_controller, "is_preview_mode") and self.frame_controller.is_preview_mode():
            self.frame_controller.previous_frame_preview(interval)
        elif self.frame_controller.frame_files:
            self.frame_controller.previous_frame(interval)

    def next_frame(self) -> None:
        interval = self.interval_spinbox.value()
        # 照片文件夹模式优先
        if hasattr(self.frame_controller, "is_image_folder_mode") and self.frame_controller.is_image_folder_mode():
            self.frame_controller.next_image_from_folder(interval)
        # 预览模式
        elif hasattr(self.frame_controller, "is_preview_mode") and self.frame_controller.is_preview_mode():
            self.frame_controller.next_frame_preview(interval)
        elif self.frame_controller.frame_files:
            self.frame_controller.next_frame(interval)

    def on_frame_loaded(self, frame_data) -> None:
        """支持两种类型：文件路径 或 OpenCV图像矩阵"""
        import numpy as np
        pixmap = None

        # 如果是字符串路径（文件模式或照片文件夹模式）
        if isinstance(frame_data, str):
            pixmap = QPixmap(frame_data)
            # 为了支持预测功能，需要将图片文件加载为numpy数组
            try:
                # 使用OpenCV读取图片文件为numpy数组
                frame_mat = cv2.imread(frame_data)
                if frame_mat is not None:
                    self.current_frame_mat = frame_mat.copy()
                    print(f"照片文件夹模式：成功加载图片为numpy数组，形状: {frame_mat.shape}")
                else:
                    print(f"照片文件夹模式：无法读取图片文件: {frame_data}")
                    self.current_frame_mat = None
            except Exception as e:
                print(f"照片文件夹模式：读取图片文件时出错: {e}")
                self.current_frame_mat = None

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
        
        # 如果在视频标注面板且当前帧不为空且预测开关开启，进行自动标注
        if (self.function_panel.currentIndex() == 0 and self.current_frame_mat is not None 
            and self.prediction_switch.isChecked()):
            confidence_threshold = self.config.get("confidence_threshold", 0.5)
            boxes = self.auto_annotator.predict(self.current_frame_mat, confidence_threshold)
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
                    # 照片文件夹模式优先
                    if hasattr(self.frame_controller, "is_image_folder_mode") and self.frame_controller.is_image_folder_mode():
                        current = self.frame_controller.current_frame_index
                        total = self.frame_controller.total_frames
                        self.frame_info_label.setText(f"图片：{current} / {total}")
                    # 预览模式
                    else:
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
                # 照片文件夹模式优先
                if hasattr(self.frame_controller, "is_image_folder_mode") and self.frame_controller.is_image_folder_mode():
                    target_frame = int((value / 1000) * self.frame_controller.total_frames)
                    target_frame = max(0, min(target_frame, self.frame_controller.total_frames - 1))
                    # 临时禁用进度条更新，避免循环更新
                    self.progress_slider.blockSignals(True)
                    self.frame_controller.goto_image_from_folder(target_frame)
                    self.progress_slider.blockSignals(False)
                # 预览模式
                else:
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