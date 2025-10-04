"""
主程序入口文件
负责初始化应用程序并启动主窗口
"""

import sys
from PyQt5.QtWidgets import QApplication
from LabelerPyQt5 import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())