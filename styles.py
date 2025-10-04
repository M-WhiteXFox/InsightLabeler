"""
样式表模块
负责管理应用程序的统一样式
"""

from typing import Dict


# 定义颜色常量
COLORS = {
    "primary": "#6c757d",
    "hover": "#5a6268",
    "pressed": "#545b62",
    "selected": "#495057",
    "background": "#f0f0f0",
    "text": "#333",
    "secondary_text": "#6c757d",
    "border": "#ddd",
    "light_background": "#f8f9fa",
    "title": "#2c3e50"
}


def get_main_style() -> str:
    """获取主窗口样式表"""
    return f"""
        QMainWindow {{
            background-color: {COLORS["background"]};
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }}
        QPushButton {{
            background-color: {COLORS["primary"]};
            border: none;
            color: white;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            margin: 4px 2px;
            border-radius: 8px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["pressed"]};
        }}
        QPushButton:checked {{
            background-color: {COLORS["selected"]};
        }}
        QLineEdit {{
            padding: 8px;
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }}
        QLineEdit:focus {{
            border: 2px solid {COLORS["primary"]};
        }}
        QLabel {{
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            color: {COLORS["text"]};
        }}
        QSpinBox {{
            padding: 6px;
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            font-size: 16px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }}
        QGroupBox {{
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            margin-top: 1ex;
            font-weight: bold;
            padding: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 10px;
            background-color: {COLORS["background"]};
            color: {COLORS["text"]};
            font-size: 18px;
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
        }}
    """


def get_button_style(size: str = "medium", color: str = COLORS["primary"]) -> str:
    """获取按钮样式"""
    # 根据大小设置不同的样式
    if size == "small":
        padding = "8px 16px"
        font_size = "16px"
        min_width = "80px"
    elif size == "large":
        padding = "14px 28px"
        font_size = "16px"
        min_width = "140px"
    else:  # medium
        padding = "12px 24px"
        font_size = "16px"
        min_width = "100px"
    
    return f"""
        QPushButton {{
            background-color: {color};
            border: none;
            color: white;
            padding: {padding};
            text-align: center;
            text-decoration: none;
            font-size: {font_size};
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            font-weight: normal;
            margin: 4px 2px;
            border-radius: 8px;
            min-width: {min_width};
        }}
        QPushButton:hover {{
            background-color: {COLORS["hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["pressed"]};
        }}
    """


def get_top_button_style(selected: bool = False) -> str:
    """获取顶部按钮样式"""
    if selected:
        return f"""
            QPushButton {{
                background-color: {COLORS["selected"]};
                border: 2px solid {COLORS["primary"]};
                color: white;
                padding: 14px 28px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                font-weight: normal;
                margin: 4px 2px;
                border-radius: 8px;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["hover"]};
            }}
            QPushButton:pressed {{
                background-color: {COLORS["pressed"]};
            }}
        """
    else:
        return f"""
            QPushButton {{
                background-color: {COLORS["primary"]};
                border: none;
                color: white;
                padding: 14px 28px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                font-weight: normal;
                margin: 4px 2px;
                border-radius: 8px;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["hover"]};
            }}
            QPushButton:pressed {{
                background-color: {COLORS["pressed"]};
            }}
        """