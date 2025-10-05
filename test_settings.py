"""
测试设置面板功能
"""

import sys
from PyQt5.QtWidgets import QApplication
from LabelerPyQt5 import MainWindow

def test_settings_panel():
    """测试设置面板"""
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # 检查设置面板是否正确创建
    print("设置面板创建成功")
    
    # 检查模型相关控件是否存在
    if hasattr(window, 'model_path_line_edit'):
        print("模型路径输入框存在")
    else:
        print("错误: 模型路径输入框不存在")
        
    if hasattr(window, 'model_browse_btn'):
        print("模型浏览按钮存在")
    else:
        print("错误: 模型浏览按钮不存在")
        
    if hasattr(window, 'model_status_label'):
        print("模型状态标签存在")
    else:
        print("错误: 模型状态标签不存在")
    
    # 检查自动标注器是否正确初始化
    if hasattr(window, 'auto_annotator'):
        print("自动标注器已初始化")
        print(f"模型可用性: {window.auto_annotator.is_available()}")
    else:
        print("错误: 自动标注器未初始化")
    
    print("设置面板功能测试完成！")
    
    # 不显示窗口，只测试初始化
    window.close()
    app.quit()

if __name__ == "__main__":
    test_settings_panel()
