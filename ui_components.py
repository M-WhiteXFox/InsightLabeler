"""
UI组件模块
负责创建和管理用户界面组件
"""

import sys
from typing import Tuple, Any
from functools import partial

from PyQt5.QtWidgets import QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox, QFrame, QSpinBox, QLineEdit, QStackedWidget, QSizePolicy, QWidget, QSlider, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import styles


class CustomScrollArea(QScrollArea):
    """自定义滚动区域，处理鼠标滚轮事件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(False)
    
    def wheelEvent(self, event):
        """处理鼠标滚轮事件，确保只影响滚动区域"""
        # 只处理垂直滚动
        if event.angleDelta().y() != 0:
            # 获取当前滚动位置
            scrollbar = self.verticalScrollBar()
            current_value = scrollbar.value()
            
            # 计算滚动步长
            wheel_delta = event.angleDelta().y()
            scroll_step = wheel_delta // 120 * 20  # 每次滚动20像素
            
            # 设置新的滚动位置
            new_value = current_value - scroll_step
            scrollbar.setValue(new_value)
            
            # 接受事件，防止传播到父组件
            event.accept()
        else:
            super().wheelEvent(event)


def create_button(text: str, color: str = styles.COLORS["primary"], size: str = "medium", 
                  parent: Any = None, checkable: bool = False) -> QPushButton:
    """
    创建统一样式的按钮
    
    参数:
        text: 按钮文本
        color: 按钮背景颜色
        size: 按钮大小 ("small", "medium", "large")
        parent: 父级组件
        checkable: 是否可切换
    """
    button = QPushButton(text, parent)
    button.setCheckable(checkable)
    
    # 设置按钮样式
    button.setStyleSheet(styles.get_button_style(size, color))
    
    # 设置按钮的尺寸策略，使其可以缩放
    button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return button


def create_top_button(text: str, color: str = styles.COLORS["primary"], 
                      parent: Any = None, checkable: bool = False) -> QPushButton:
    """创建顶部按钮"""
    return create_button(text, color, "large", parent, checkable)


def create_image_display_area(parent_layout: QHBoxLayout, image_label: QLabel) -> None:
    """创建图片显示区域"""
    image_container = QFrame()
    image_container.setStyleSheet("""
        QFrame {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
        }
    """)
    image_layout = QVBoxLayout(image_container)
    image_layout.setContentsMargins(15, 15, 15, 15)
    
    # 标题
    title_label = QLabel("图片预览")
    title_label.setStyleSheet("""
        QLabel {
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 12px;
        }
    """)
    # 设置标题的尺寸策略
    title_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    image_layout.addWidget(title_label)
    
    # 图片标签
    image_label.setAlignment(Qt.AlignCenter)
    image_label.setMinimumSize(450, 350)
    # 设置图片标签的尺寸策略，使其可以缩放
    image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    # 设置无图片时的提示和样式
    image_label.setText("暂无图片\n请选择视频并提取帧")
    image_label.setStyleSheet("""
        QLabel {
            background-color: #f8f9fa;
            border: 1px dashed #ddd;
            border-radius: 6px;
            padding: 25px;
            color: #6c757d;
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
        
    image_layout.addWidget(image_label)
    parent_layout.addWidget(image_container, stretch=3)


def create_function_panel_area(parent_layout: QHBoxLayout) -> QStackedWidget:
    """创建功能面板区域"""
    function_panel = QStackedWidget()
    function_panel.setStyleSheet("""
        QStackedWidget {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
        }
    """)
    
    # 设置功能面板的尺寸策略
    function_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    
    return function_panel


def create_video_panel(config: dict, select_file_handler: callable, 
                       extract_frames_handler: callable) -> Tuple:
    """创建视频处理面板"""
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setSpacing(15)
    
    # 视频文件选择组
    video_group = QGroupBox("视频文件")
    video_group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #2c3e50;
            padding-top: 25px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 6px 12px;
        }
    """)
    # 设置组框的尺寸策略
    video_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    
    video_layout = QVBoxLayout(video_group)
    video_layout.setSpacing(12)
    
    folder_choose = QHBoxLayout()
    folder_choose.setSpacing(8)
    video_label = QLabel("视频文件:")
    video_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    video_line_edit = QLineEdit()
    video_line_edit.setText(config.get("video_path", ""))
    if not video_line_edit.text():
        video_line_edit.setPlaceholderText("请选择视频文件")
    video_line_edit.setStyleSheet("""
        QLineEdit { 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            padding: 8px;
        }
    """)
    
    browse_btn = create_button("浏览", styles.COLORS["primary"], "small")
    browse_btn.clicked.connect(partial(select_file_handler, video_line_edit, "video_path"))
    
    folder_choose.addWidget(video_label)
    folder_choose.addWidget(video_line_edit)
    folder_choose.addWidget(browse_btn)
    video_layout.addLayout(folder_choose)
    layout.addWidget(video_group)
    
    # 帧提取参数组
    params_group = QGroupBox("提取参数")
    params_group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #2c3e50;
            padding-top: 20px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
        }
    """)
    # 设置组框的尺寸策略
    params_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    
    params_layout = QVBoxLayout(params_group)
    params_layout.setSpacing(10)
    
    # 帧间隔
    interval_layout = QHBoxLayout()
    interval_layout.setSpacing(8)
    interval_label = QLabel("帧间隔:")
    interval_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    interval_spinbox = QSpinBox()
    interval_spinbox.setMinimum(1)
    interval_spinbox.setMaximum(1000)
    interval_spinbox.setValue(config.get("frame_interval", 1))
    interval_spinbox.setStyleSheet("""
        QSpinBox { 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            padding: 6px;
        }
    """)
    interval_layout.addWidget(interval_label)
    interval_layout.addWidget(interval_spinbox)
    interval_layout.addStretch()
    params_layout.addLayout(interval_layout)
    
    # 最大帧数
    max_frames_layout = QHBoxLayout()
    max_frames_layout.setSpacing(8)
    max_frames_label = QLabel("最大帧数:")
    max_frames_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    max_frames_spinbox = QSpinBox()
    max_frames_spinbox.setMinimum(0)
    max_frames_spinbox.setMaximum(10000)
    max_frames_spinbox.setValue(config.get("max_frames", 0))
    max_frames_spinbox.setSpecialValueText("无限制")
    max_frames_spinbox.setStyleSheet("""
        QSpinBox { 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            padding: 4px;
        }
    """)
    max_frames_layout.addWidget(max_frames_label)
    max_frames_layout.addWidget(max_frames_spinbox)
    max_frames_layout.addStretch()
    params_layout.addLayout(max_frames_layout)
    
    params_layout.addStretch()
    layout.addWidget(params_group)
    
    # 操作按钮
    extract_btn = create_button("提取帧", styles.COLORS["primary"], "large")
    # 设置按钮的尺寸策略
    extract_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    extract_btn.clicked.connect(extract_frames_handler)
    layout.addWidget(extract_btn)
    
    # 帧导航组
    nav_group = QGroupBox("帧导航")
    nav_group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #2c3e50;
            padding-top: 20px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
        }
    """)
    # 设置组框的尺寸策略
    nav_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    
    nav_layout = QVBoxLayout(nav_group)
    nav_layout.setSpacing(10)
    
    # 导航按钮
    nav_buttons_layout = QHBoxLayout()
    nav_buttons_layout.setSpacing(8)
    prev_frame_btn = create_button("上一张", styles.COLORS["primary"], "medium")
    next_frame_btn = create_button("下一张", styles.COLORS["primary"], "medium")
    nav_buttons_layout.addWidget(prev_frame_btn)
    nav_buttons_layout.addWidget(next_frame_btn)
    nav_layout.addLayout(nav_buttons_layout)
    
    # 帧跳转
    goto_layout = QHBoxLayout()
    goto_layout.setSpacing(8)
    goto_label = QLabel("跳转到帧:")
    goto_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    frame_spinbox = QSpinBox()
    frame_spinbox.setMinimum(0)
    frame_spinbox.setMaximum(999999)
    frame_spinbox.setValue(0)
    frame_spinbox.setStyleSheet("""
        QSpinBox { 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            padding: 4px;
        }
    """)
    goto_btn = create_button("跳转", styles.COLORS["primary"], "small")
    goto_layout.addWidget(goto_label)
    goto_layout.addWidget(frame_spinbox)
    goto_layout.addWidget(goto_btn)
    nav_layout.addLayout(goto_layout)
    
    # 帧信息标签
    frame_info_label = QLabel("帧：- / -")
    frame_info_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    nav_layout.addWidget(frame_info_label)
    
    # 进度条
    progress_slider = QSlider(Qt.Horizontal)
    progress_slider.setMinimum(0)
    progress_slider.setMaximum(1000)  # 增加精度，支持更平滑的拖动
    progress_slider.setValue(0)
    progress_slider.setTickPosition(QSlider.NoTicks)  # 移除刻度，让拖动更平滑
    progress_slider.setTracking(True)  # 启用跟踪，提供实时反馈
    progress_slider.setSingleStep(1)  # 设置单步值为1，确保连续拖动
    progress_slider.setStyleSheet("""
        QSlider::groove:horizontal {
            border: 1px solid #999999;
            height: 8px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
            margin: 2px 0;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6c757d, stop:1 #495057);
            border: 1px solid #5c5c5c;
            width: 18px;
            margin: -2px 0;
            border-radius: 3px;
        }
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #495057, stop:1 #343a40);
        }
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6c757d, stop:1 #495057);
            border: 1px solid #5c5c5c;
            height: 8px;
            border-radius: 4px;
        }
    """)
    nav_layout.addWidget(progress_slider)
    
    nav_layout.addStretch()
    layout.addWidget(nav_group)
    
    # 保存当前帧按钮
    save_frame_btn = create_button("保存当前帧", styles.COLORS["primary"], "large")
    layout.addWidget(save_frame_btn)
    
    layout.addStretch()
    
    # 设置面板的尺寸策略
    panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    
    # 返回面板和相关控件
    return panel, video_line_edit, interval_spinbox, max_frames_spinbox, extract_btn, prev_frame_btn, next_frame_btn, frame_spinbox, goto_btn, frame_info_label, save_frame_btn, progress_slider


def create_annotate_panel() -> QWidget:
    """创建标注面板（保留原函数以兼容性）"""
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setSpacing(12)
    
    # 标题
    title_label = QLabel("图像标注")
    title_label.setStyleSheet("""
        QLabel {
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }
    """)
    layout.addWidget(title_label)
    
    # 描述
    desc_label = QLabel("在此面板中可以进行图像标注操作")
    desc_label.setStyleSheet("""
        QLabel {
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #6c757d;
            margin-bottom: 15px;
        }
    """)
    layout.addWidget(desc_label)
    
    
    # 标注工具组
    tools_group = QGroupBox("标注工具")
    tools_group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #2c3e50;
            padding-top: 20px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
        }
    """)
    tools_layout = QVBoxLayout(tools_group)
    
    # 新建标注框按钮
    new_box_btn = create_button("新建标注框", styles.COLORS["primary"], "large", checkable=True)
    new_box_btn.setStyleSheet(styles.get_button_style("large", styles.COLORS["primary"]) + """
        QPushButton:checked {
            background-color: #28a745;
            border: 2px solid #1e7e34;
        }
        QPushButton:checked:hover {
            background-color: #218838;
        }
    """)
    tools_layout.addWidget(new_box_btn)
    
    layout.addWidget(tools_group)
    
    layout.addStretch()
    
    # 设置面板的尺寸策略
    panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    return panel, new_box_btn


def create_video_annotate_panel(config: dict, select_file_handler: callable, 
                                extract_frames_handler: callable) -> Tuple:
    """创建视频处理和图像标注合并面板"""
    # 创建主面板
    main_panel = QWidget()
    main_layout = QVBoxLayout(main_panel)
    main_layout.setSpacing(0)
    main_layout.setContentsMargins(0, 0, 0, 0)
    
    # 创建自定义滚动区域
    scroll_area = CustomScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll_area.setStyleSheet("""
        QScrollArea {
            border-left: 1px solid #e0e0e0;
            background: #fafafa;
        }
        QScrollBar:vertical {
            background: #f0f0f0;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background: #c0c0c0;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #a0a0a0;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
    """)
    
    # 创建内容面板
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setSpacing(15)
    layout.setContentsMargins(15, 15, 15, 15)
    
    # 标题
    title_label = QLabel("视频处理与图像标注")
    title_label.setStyleSheet("""
        QLabel {
            font-size: 20px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }
    """)
    layout.addWidget(title_label)
    
    # 描述
    desc_label = QLabel("在此面板中可以处理视频并进行图像标注")
    desc_label.setStyleSheet("""
        QLabel {
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #6c757d;
            margin-bottom: 15px;
        }
    """)
    layout.addWidget(desc_label)
    
    # 视频文件选择组
    video_group = QGroupBox("视频文件")
    video_group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #2c3e50;
            padding-top: 25px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 6px 12px;
        }
    """)
    video_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    
    video_layout = QVBoxLayout(video_group)
    video_layout.setSpacing(12)
    
    folder_choose = QHBoxLayout()
    folder_choose.setSpacing(8)
    video_label = QLabel("视频文件:")
    video_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    video_line_edit = QLineEdit()
    video_line_edit.setText(config.get("video_path", ""))
    if not video_line_edit.text():
        video_line_edit.setPlaceholderText("请选择视频文件")
    video_line_edit.setStyleSheet("""
        QLineEdit { 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            padding: 8px;
        }
    """)
    
    browse_btn = create_button("浏览", styles.COLORS["primary"], "small")
    browse_btn.clicked.connect(partial(select_file_handler, video_line_edit, "video_path"))
    
    folder_choose.addWidget(video_label)
    folder_choose.addWidget(video_line_edit)
    folder_choose.addWidget(browse_btn)
    video_layout.addLayout(folder_choose)
    layout.addWidget(video_group)
    
    # 帧提取参数组
    params_group = QGroupBox("提取参数")
    params_group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #2c3e50;
            padding-top: 20px;
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
    
    # 帧间隔
    interval_layout = QHBoxLayout()
    interval_layout.setSpacing(8)
    interval_label = QLabel("帧间隔:")
    interval_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    interval_spinbox = QSpinBox()
    interval_spinbox.setMinimum(1)
    interval_spinbox.setMaximum(1000)
    interval_spinbox.setValue(config.get("frame_interval", 1))
    interval_spinbox.setStyleSheet("""
        QSpinBox { 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            padding: 6px;
        }
    """)
    interval_layout.addWidget(interval_label)
    interval_layout.addWidget(interval_spinbox)
    interval_layout.addStretch()
    params_layout.addLayout(interval_layout)
    
    # 最大帧数
    max_frames_layout = QHBoxLayout()
    max_frames_layout.setSpacing(8)
    max_frames_label = QLabel("最大帧数:")
    max_frames_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    max_frames_spinbox = QSpinBox()
    max_frames_spinbox.setMinimum(0)
    max_frames_spinbox.setMaximum(10000)
    max_frames_spinbox.setValue(config.get("max_frames", 0))
    max_frames_spinbox.setSpecialValueText("无限制")
    max_frames_spinbox.setStyleSheet("""
        QSpinBox { 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            padding: 4px;
        }
    """)
    max_frames_layout.addWidget(max_frames_label)
    max_frames_layout.addWidget(max_frames_spinbox)
    max_frames_layout.addStretch()
    params_layout.addLayout(max_frames_layout)
    
    params_layout.addStretch()
    layout.addWidget(params_group)
    
    # 操作按钮
    extract_btn = create_button("提取帧", styles.COLORS["primary"], "large")
    extract_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    extract_btn.clicked.connect(extract_frames_handler)
    layout.addWidget(extract_btn)
    
    # 帧导航组
    nav_group = QGroupBox("帧导航")
    nav_group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #2c3e50;
            padding-top: 20px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
        }
    """)
    nav_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    
    nav_layout = QVBoxLayout(nav_group)
    nav_layout.setSpacing(10)
    
    # 导航按钮
    nav_buttons_layout = QHBoxLayout()
    nav_buttons_layout.setSpacing(8)
    prev_frame_btn = create_button("上一张", styles.COLORS["primary"], "medium")
    next_frame_btn = create_button("下一张", styles.COLORS["primary"], "medium")
    nav_buttons_layout.addWidget(prev_frame_btn)
    nav_buttons_layout.addWidget(next_frame_btn)
    nav_layout.addLayout(nav_buttons_layout)
    
    # 帧跳转
    goto_layout = QHBoxLayout()
    goto_layout.setSpacing(8)
    goto_label = QLabel("跳转到帧:")
    goto_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    frame_spinbox = QSpinBox()
    frame_spinbox.setMinimum(0)
    frame_spinbox.setMaximum(999999)
    frame_spinbox.setValue(0)
    frame_spinbox.setStyleSheet("""
        QSpinBox { 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            padding: 4px;
        }
    """)
    goto_btn = create_button("跳转", styles.COLORS["primary"], "small")
    goto_layout.addWidget(goto_label)
    goto_layout.addWidget(frame_spinbox)
    goto_layout.addWidget(goto_btn)
    nav_layout.addLayout(goto_layout)
    
    # 帧信息标签
    frame_info_label = QLabel("帧：- / -")
    frame_info_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    nav_layout.addWidget(frame_info_label)
    
    # 进度条
    progress_slider = QSlider(Qt.Horizontal)
    progress_slider.setMinimum(0)
    progress_slider.setMaximum(1000)
    progress_slider.setValue(0)
    progress_slider.setTickPosition(QSlider.NoTicks)
    progress_slider.setTracking(True)
    progress_slider.setSingleStep(1)
    progress_slider.setStyleSheet("""
        QSlider::groove:horizontal {
            border: 1px solid #999999;
            height: 8px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
            margin: 2px 0;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6c757d, stop:1 #495057);
            border: 1px solid #5c5c5c;
            width: 18px;
            margin: -2px 0;
            border-radius: 3px;
        }
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #495057, stop:1 #343a40);
        }
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6c757d, stop:1 #495057);
            border: 1px solid #5c5c5c;
            height: 8px;
            border-radius: 4px;
        }
    """)
    nav_layout.addWidget(progress_slider)
    
    nav_layout.addStretch()
    layout.addWidget(nav_group)
    
    # 模型设置组
    model_group = QGroupBox("AI模型设置")
    model_group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #2c3e50;
            padding-top: 20px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
        }
    """)
    model_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    
    model_layout = QVBoxLayout(model_group)
    model_layout.setSpacing(10)
    
    # 模型路径设置
    model_path_layout = QHBoxLayout()
    model_path_layout.setSpacing(8)
    model_path_label = QLabel("模型路径:")
    model_path_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    model_path_line_edit = QLineEdit()
    model_path_line_edit.setText(config.get("model_path", ""))
    if not model_path_line_edit.text():
        model_path_line_edit.setPlaceholderText("请选择YOLO模型文件 (.pt)")
    model_path_line_edit.setStyleSheet("""
        QLineEdit { 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            padding: 6px;
        }
    """)
    model_browse_btn = create_button("浏览", styles.COLORS["primary"], "small")
    model_path_layout.addWidget(model_path_label)
    model_path_layout.addWidget(model_path_line_edit)
    model_path_layout.addWidget(model_browse_btn)
    model_layout.addLayout(model_path_layout)
    
    # 模型状态显示
    model_status_label = QLabel("模型状态: 未加载")
    model_status_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 14px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #6c757d;
            margin-top: 5px;
        }
    """)
    model_layout.addWidget(model_status_label)
    
    # 预测开关
    prediction_layout = QHBoxLayout()
    prediction_layout.setSpacing(8)
    prediction_label = QLabel("启用AI预测:")
    prediction_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    prediction_switch = QPushButton("关闭")
    prediction_switch.setCheckable(True)
    prediction_switch.setStyleSheet("""
        QPushButton {
            background-color: #dc3545;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            font-size: 14px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
        QPushButton:checked {
            background-color: #28a745;
        }
        QPushButton:hover {
            background-color: #c82333;
        }
        QPushButton:checked:hover {
            background-color: #218838;
        }
    """)
    prediction_layout.addWidget(prediction_label)
    prediction_layout.addWidget(prediction_switch)
    prediction_layout.addStretch()
    model_layout.addLayout(prediction_layout)
    
    # 置信度设置
    confidence_layout = QHBoxLayout()
    confidence_layout.setSpacing(8)
    confidence_label = QLabel("置信度阈值:")
    confidence_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    confidence_slider = QSlider(Qt.Horizontal)
    confidence_slider.setMinimum(0)
    confidence_slider.setMaximum(100)
    confidence_slider.setValue(int(config.get("confidence_threshold", 50)))
    confidence_slider.setStyleSheet("""
        QSlider::groove:horizontal {
            border: 1px solid #999999;
            height: 8px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
            margin: 2px 0;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6c757d, stop:1 #495057);
            border: 1px solid #5c5c5c;
            width: 18px;
            margin: -2px 0;
            border-radius: 3px;
        }
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #495057, stop:1 #343a40);
        }
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6c757d, stop:1 #495057);
            border: 1px solid #5c5c5c;
            height: 8px;
            border-radius: 4px;
        }
    """)
    confidence_value_label = QLabel("50%")
    confidence_value_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #2c3e50;
            min-width: 40px;
        }
    """)
    confidence_layout.addWidget(confidence_label)
    confidence_layout.addWidget(confidence_slider)
    confidence_layout.addWidget(confidence_value_label)
    model_layout.addLayout(confidence_layout)
    
    layout.addWidget(model_group)
    
    # 标注工具组
    tools_group = QGroupBox("标注工具")
    tools_group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #2c3e50;
            padding-top: 20px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
        }
    """)
    tools_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    
    tools_layout = QVBoxLayout(tools_group)
    
    # 按钮布局 - 使用水平布局减少垂直空间
    buttons_layout = QHBoxLayout()
    buttons_layout.setSpacing(8)
    
    # 新建标注框按钮
    new_box_btn = create_button("新建标注框", styles.COLORS["primary"], "medium", checkable=True)
    new_box_btn.setStyleSheet(styles.get_button_style("medium", styles.COLORS["primary"]) + """
        QPushButton:checked {
            background-color: #28a745;
            border: 2px solid #1e7e34;
        }
        QPushButton:checked:hover {
            background-color: #218838;
        }
        QPushButton {
            font-size: 16px;
            font-weight: bold;
            min-height: 40px;
        }
    """)
    new_box_btn.setMinimumHeight(40)
    buttons_layout.addWidget(new_box_btn)
    
    # 刷新预测按钮
    refresh_btn = create_button("刷新预测", styles.COLORS["secondary"], "medium")
    refresh_btn.setStyleSheet(styles.get_button_style("medium", styles.COLORS["secondary"]) + """
        QPushButton:hover {
            background-color: #5a6268;
        }
        QPushButton {
            font-size: 16px;
            font-weight: bold;
            min-height: 40px;
        }
    """)
    refresh_btn.setMinimumHeight(40)
    buttons_layout.addWidget(refresh_btn)
    
    # 保存预测结果按钮
    save_prediction_btn = create_button("保存预测结果", styles.COLORS["primary"], "medium")
    save_prediction_btn.setStyleSheet(styles.get_button_style("medium", styles.COLORS["primary"]) + """
        QPushButton {
            font-size: 16px;
            font-weight: bold;
            min-height: 40px;
        }
    """)
    save_prediction_btn.setMinimumHeight(40)
    buttons_layout.addWidget(save_prediction_btn)
    
    # 将按钮布局添加到工具布局
    tools_layout.addLayout(buttons_layout)
    
    # 标注说明
    annotate_desc = QLabel("在图像上绘制标注框，支持拖拽、调整大小、删除等操作。修改模型参数后点击'刷新预测'重新应用。")
    annotate_desc.setStyleSheet("""
        QLabel {
            font-size: 14px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #6c757d;
            margin-top: 8px;
        }
    """)
    annotate_desc.setWordWrap(True)
    tools_layout.addWidget(annotate_desc)
    
    layout.addWidget(tools_group)
    
    layout.addStretch()
    
    # 设置内容面板的尺寸策略
    panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    
    # 将内容面板添加到滚动区域
    scroll_area.setWidget(panel)
    
    # 将滚动区域添加到主面板
    main_layout.addWidget(scroll_area)
    
    # 设置主面板的尺寸策略
    main_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    
    # 返回主面板和相关控件
    return main_panel, video_line_edit, interval_spinbox, max_frames_spinbox, extract_btn, prev_frame_btn, next_frame_btn, frame_spinbox, goto_btn, frame_info_label, save_prediction_btn, progress_slider, new_box_btn, refresh_btn, model_path_line_edit, model_browse_btn, model_status_label, prediction_switch, confidence_slider, confidence_value_label


def create_settings_panel(config: dict) -> Tuple:
    """创建设置面板"""
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setSpacing(12)
    
    # 标题
    title_label = QLabel("设置")
    title_label.setStyleSheet("""
        QLabel {
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }
    """)
    layout.addWidget(title_label)
    
    # 描述
    desc_label = QLabel("在此面板中可以进行程序设置")
    desc_label.setStyleSheet("""
        QLabel {
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #6c757d;
            margin-bottom: 15px;
        }
    """)
    layout.addWidget(desc_label)
    
    # 设置选项
    settings_btn = create_button("保存设置", styles.COLORS["primary"], "large")
    layout.addWidget(settings_btn)
    
    # 输出目录设置
    output_group = QGroupBox("输出设置")
    output_group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #2c3e50;
            padding-top: 20px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
        }
    """)
    output_layout = QVBoxLayout(output_group)
    
    output_label = QLabel("基础输出目录:")
    output_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    output_layout.addWidget(output_label)
    
    output_dir_layout = QHBoxLayout()
    output_dir_layout.setSpacing(6)
    output_dir_line_edit = QLineEdit()
    output_dir_line_edit.setText(config.get("output_dir", "./output"))
    output_dir_line_edit.setStyleSheet("""
        QLineEdit { 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            padding: 6px;
        }
    """)
    output_browse_btn = create_button("浏览", styles.COLORS["primary"], "small")
    output_dir_layout.addWidget(output_dir_line_edit)
    output_dir_layout.addWidget(output_browse_btn)
    output_layout.addLayout(output_dir_layout)
    
    # 当前视频输出目录显示
    current_video_label = QLabel("当前视频输出目录:")
    current_video_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            margin-top: 15px;
        }
    """)
    output_layout.addWidget(current_video_label)
    
    current_video_path_label = QLabel("未选择视频")
    current_video_path_label.setStyleSheet("""
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
    current_video_path_label.setWordWrap(True)
    output_layout.addWidget(current_video_path_label)
    
    layout.addWidget(output_group)
    
    # 模型设置
    model_group = QGroupBox("自动标注模型")
    model_group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #2c3e50;
            padding-top: 20px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
        }
    """)
    model_layout = QVBoxLayout(model_group)
    
    model_label = QLabel("YOLO模型路径:")
    model_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }
    """)
    model_layout.addWidget(model_label)
    
    model_path_layout = QHBoxLayout()
    model_path_layout.setSpacing(6)
    model_path_line_edit = QLineEdit()
    model_path_line_edit.setText(config.get("model_path", ""))
    if not model_path_line_edit.text():
        model_path_line_edit.setPlaceholderText("请选择YOLO模型文件 (.pt)")
    model_path_line_edit.setStyleSheet("""
        QLineEdit { 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            padding: 6px;
        }
    """)
    model_browse_btn = create_button("浏览", styles.COLORS["primary"], "small")
    model_path_layout.addWidget(model_path_line_edit)
    model_path_layout.addWidget(model_browse_btn)
    model_layout.addLayout(model_path_layout)
    
    # 模型状态显示
    model_status_label = QLabel("模型状态: 未加载")
    model_status_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 14px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #6c757d;
            margin-top: 5px;
        }
    """)
    model_layout.addWidget(model_status_label)
    
    # 自动文件夹结构说明
    auto_folder_label = QLabel("自动文件夹结构:")
    auto_folder_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            margin-top: 15px;
        }
    """)
    model_layout.addWidget(auto_folder_label)
    
    folder_structure_label = QLabel("系统会根据视频名称自动创建文件夹结构：\n{基础输出目录}/{视频名称}/\n├── images/  (存放图片文件)\n└── labels/  (存放标注文件)")
    folder_structure_label.setStyleSheet("""
        QLabel { 
            font-weight: normal; 
            font-size: 14px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: #6c757d;
            background-color: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            margin-top: 5px;
        }
    """)
    folder_structure_label.setWordWrap(True)
    model_layout.addWidget(folder_structure_label)
    
    layout.addWidget(model_group)
    
    layout.addStretch()
    
    # 设置面板的尺寸策略
    panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    return panel, output_dir_line_edit, settings_btn, output_browse_btn, model_path_line_edit, model_browse_btn, model_status_label, current_video_path_label