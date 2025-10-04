import sys
import Utils
from functools import partial

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, \
    QSizePolicy, QFileDialog, QLineEdit
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        Utils.load_config()

        self.setWindowTitle("InsightLabeler")
        self.setMinimumSize(200, 200)
        self.setStyleSheet("background-color:#FFFFFF;")

        central_widget = QWidget() #主窗口
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()  # 垂直布局

        # ===== 上 1/3：按钮区域 =====
        button_container = QWidget()
        button_container.setStyleSheet("background-color:#f0f0f0;")
        folder_choose = QHBoxLayout(button_container)  # 横向布局（按钮并排）

        VideoText = QLabel("视频文件夹:")

        line_edit = QLineEdit()

        if (line_edit.text() == ""):
            line_edit.setPlaceholderText(f"请选择文件夹路径")

        browse_btn = QPushButton("浏览")
        browse_btn.line_edit = line_edit
        browse_btn.clicked.connect(partial(self.select_folder, line_edit))

        folder_choose.addWidget(VideoText)
        folder_choose.addWidget(line_edit)
        folder_choose.addWidget(browse_btn)

        main_layout.addWidget(button_container, stretch=1)

        #————————图片布局——————
        self.image_label = QLabel()
        self.original_pixmap = QPixmap()
        tmp_pixmap = QPixmap("output/frame_0.jpg")  # 图片路径
        if tmp_pixmap.isNull():
            print("图片加载失败！")
        else:
            self.original_pixmap = tmp_pixmap
            self.image_label.setPixmap(self.original_pixmap)
        main_layout.addWidget(self.image_label, stretch=7)
        central_widget.setLayout(main_layout)
        self.showMaximized()  # 设置窗口最大化

    def create_button(self, text, x, y, w, h, callback):
        self.button = QPushButton(text, self)
        self.button.setGeometry(x, y, w, h)
        self.button.clicked.connect(callback)

    def resizeEvent(self, event):  # 窗口缩放自动调整图片大小
        if hasattr(self, "original_pixmap") and not self.original_pixmap.isNull():
            self.image_label.setPixmap(
                self.original_pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
        super().resizeEvent(event)  # 保留父类默认行为

    def select_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", "./")
        if folder:
            line_edit.setText(folder)
            self.config["last_dir"] = folder
            Utils.save_config(self.config)

if __name__ == '__main__':
    app = QApplication(sys.argv)  # 创建Qt应用程序实例
    window = MainWindow()
    sys.exit(app.exec())  # PySide6 用 exec()
