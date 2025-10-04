"""
UI组件模块
负责创建和管理用户界面组件
"""

import sys
from typing import Tuple, Any
from functools import partial

from PyQt5.QtWidgets import QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox, QFrame, QSpinBox, QLineEdit, QStackedWidget, QSizePolicy, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import styles


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
    
    nav_layout.addStretch()
    layout.addWidget(nav_group)
    
    layout.addStretch()
    
    # 设置面板的尺寸策略
    panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    
    # 返回面板和相关控件
    return panel, video_line_edit, interval_spinbox, max_frames_spinbox, extract_btn, prev_frame_btn, next_frame_btn, frame_spinbox, goto_btn


def create_annotate_panel() -> QWidget:
    """创建标注面板"""
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
    
    # 功能按钮
    annotate_btn = create_button("开始标注", styles.COLORS["primary"], "large")
    layout.addWidget(annotate_btn)
    
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
    
    rect_btn = create_button("矩形工具", styles.COLORS["primary"], "medium")
    circle_btn = create_button("圆形工具", styles.COLORS["primary"], "medium")
    polygon_btn = create_button("多边形工具", styles.COLORS["primary"], "medium")
    
    tools_layout.addWidget(rect_btn)
    tools_layout.addWidget(circle_btn)
    tools_layout.addWidget(polygon_btn)
    layout.addWidget(tools_group)
    
    layout.addStretch()
    
    # 设置面板的尺寸策略
    panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    return panel


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
    
    output_label = QLabel("输出目录:")
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
    
    layout.addWidget(output_group)
    
    layout.addStretch()
    
    # 设置面板的尺寸策略
    panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    return panel, output_dir_line_edit, settings_btn, output_browse_btn