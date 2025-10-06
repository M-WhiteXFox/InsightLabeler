"""
模型训练管理面板模块
负责提供模型训练相关的用户界面和功能
"""

import os
import sys
import subprocess
import threading
import time
import re
from typing import Optional, Callable
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QLineEdit, QTextEdit, QGroupBox, QFileDialog, QMessageBox,
                             QProgressBar, QScrollArea, QFrame, QSizePolicy, QSpinBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

import styles
import Utils
from training_config import TrainingConfig


class TrainingWorker(QThread):
    """训练工作线程"""
    log_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    training_finished = pyqtSignal(bool, str)
    
    def __init__(self, training_data_path: str, base_model_path: str, epochs: int = 100):
        super().__init__()
        self.training_data_path = training_data_path
        self.base_model_path = base_model_path
        self.epochs = epochs
        self.is_running = True
        self.training_config = TrainingConfig()
        self.process = None
        self.session_id = int(time.time())  # 用于区分训练会话
        
    def run(self):
        """执行训练任务"""
        try:
            self.log_updated.emit("开始模型训练...")
            self.log_updated.emit(f"训练数据路径: {self.training_data_path}")
            self.log_updated.emit(f"基准模型路径: {self.base_model_path}")
            self.log_updated.emit(f"训练轮数: {self.epochs}")
            
            # 验证训练数据
            is_valid, message = self.training_config.validate_training_data(self.training_data_path)
            if not is_valid:
                self.training_finished.emit(False, message)
                return
            
            self.log_updated.emit("训练数据验证通过")
            
            # 检查基准模型
            if not os.path.exists(self.base_model_path) and not self.base_model_path.endswith('.pt'):
                self.training_finished.emit(False, "基准模型文件不存在")
                return
            
            # 创建训练会话
            session_dir, dataset_yaml_path = self.training_config.create_training_session(
                self.training_data_path, self.base_model_path
            )
            
            self.log_updated.emit(f"训练会话目录: {session_dir}")
            self.log_updated.emit("训练配置已生成")
            
            # 执行YOLO训练（在新CMD窗口中）
            self.execute_yolo_training(dataset_yaml_path, session_dir)
            
            # 由于在新CMD窗口中运行，我们无法直接监控进程状态
            # 所以立即标记为训练已启动
            if self.is_running:
                self.training_finished.emit(True, f"训练已在CMD窗口中启动，结果将保存在: {session_dir}")
            else:
                self.training_finished.emit(False, "训练启动失败")
                
        except Exception as e:
            self.training_finished.emit(False, f"训练过程中发生错误: {str(e)}")
    
    def execute_yolo_training(self, dataset_yaml_path: str, session_dir: str):
        """执行YOLO训练 - 在新CMD窗口中运行"""
        try:
            # 创建训练参数配置文件
            args_yaml_path = self.training_config.create_training_args(
                session_dir, dataset_yaml_path, self.base_model_path, self.epochs
            )
            
            # 获取Python解释器路径
            python_exe = sys.executable
            
            # 构建YOLO训练命令
            yolo_cmd = f'"{python_exe}" -m ultralytics yolo train args={args_yaml_path}'
            
            self.log_updated.emit(f"训练命令: {yolo_cmd}")
            
            # Windows环境下使用start cmd /k打开新窗口
            if sys.platform.startswith('win'):
                cmd = f'start cmd /k "{yolo_cmd}"'
                self.log_updated.emit("已在新 CMD 窗口中启动模型训练。")
                self.log_updated.emit(f"训练配置文件: {args_yaml_path}")
                self.log_updated.emit("请在CMD窗口中查看训练进度和日志。")
                
                # 启动新CMD窗口
                self.process = subprocess.Popen(cmd, shell=True)
                
                # 等待一下确保窗口启动
                import time
                time.sleep(2)
                
                # 由于在新窗口中运行，我们无法直接监控进程状态
                # 但可以设置一个标志表示训练已启动
                self.log_updated.emit(f"[会话{self.session_id}] 训练已在CMD窗口中启动")
                
            else:
                # 非Windows环境，直接执行命令
                self.log_updated.emit("在终端中启动模型训练...")
                self.log_updated.emit(f"训练配置文件: {args_yaml_path}")
                
                # 直接执行命令
                self.process = subprocess.Popen(yolo_cmd, shell=True)
                
                # 等待进程完成
                if self.is_running:
                    return_code = self.process.wait()
                    if return_code == 0:
                        self.log_updated.emit(f"[会话{self.session_id}] 训练成功完成")
                    else:
                        self.log_updated.emit(f"[会话{self.session_id}] 训练进程异常退出，返回码: {return_code}")
                else:
                    # 终止训练进程
                    if self.process:
                        self.process.terminate()
                        self.process.wait()
                        self.log_updated.emit(f"[会话{self.session_id}] 训练进程已终止")
                    
        except Exception as e:
            self.log_updated.emit(f"[会话{self.session_id}] 执行训练时发生错误: {str(e)}")
            raise
    
    def parse_training_progress(self, line: str):
        """解析训练进度"""
        try:
            # 匹配epoch信息
            epoch_match = re.search(r'Epoch\s+(\d+)/(\d+)', line)
            if epoch_match:
                current_epoch = int(epoch_match.group(1))
                total_epochs = int(epoch_match.group(2))
                progress = int((current_epoch / total_epochs) * 100)
                self.progress_updated.emit(progress)
                return
            
            # 匹配损失信息
            loss_match = re.search(r'loss:\s+([\d.]+)', line)
            if loss_match:
                loss_value = float(loss_match.group(1))
                self.log_updated.emit(f"当前损失: {loss_value:.4f}")
                
        except Exception as e:
            # 解析失败不影响训练
            pass
    
    def stop_training(self):
        """停止训练"""
        self.is_running = False
        if self.process:
            try:
                # 尝试终止进程
                self.process.terminate()
                self.process.wait()
                self.log_updated.emit(f"[会话{self.session_id}] 训练进程已终止")
            except Exception as e:
                self.log_updated.emit(f"[会话{self.session_id}] 停止训练时发生错误: {str(e)}")
                # 如果无法终止进程，提示用户手动关闭CMD窗口
                self.log_updated.emit("如果训练仍在运行，请手动关闭CMD窗口")


class TrainingPanel(QWidget):
    """模型训练管理面板"""
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.training_worker: Optional[TrainingWorker] = None
        self.training_data_path = ""
        self.base_model_path = ""
        self.epochs = 100
        self.is_training = False  # 训练状态标志
        
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        title_label = QLabel("模型训练管理")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 描述
        desc_label = QLabel("在此面板中可以管理模型训练任务，包括选择训练数据、基准模型和监控训练进度")
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                color: #6c757d;
                margin-bottom: 20px;
            }
        """)
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
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
        """)
        
        # 创建内容面板
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # 训练数据选择组
        self.create_training_data_group(content_layout)
        
        # 基准模型选择组
        self.create_base_model_group(content_layout)
        
        # 训练控制组
        self.create_training_control_group(content_layout)
        
        # 训练日志组
        self.create_training_log_group(content_layout)
        
        # 设置内容面板的尺寸策略
        content_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # 将内容面板添加到滚动区域
        scroll_area.setWidget(content_widget)
        
        # 将滚动区域添加到主布局
        main_layout.addWidget(scroll_area)
        
        # 设置主面板的尺寸策略
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    
    def create_training_data_group(self, parent_layout: QVBoxLayout):
        """创建训练数据选择组"""
        group = QGroupBox("训练数据选择")
        group.setStyleSheet("""
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
        group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # 路径选择
        path_layout = QHBoxLayout()
        path_layout.setSpacing(8)
        
        path_label = QLabel("训练数据文件夹:")
        path_label.setStyleSheet("""
            QLabel { 
                font-weight: normal; 
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        
        self.training_data_line_edit = QLineEdit()
        self.training_data_line_edit.setPlaceholderText("请选择包含训练数据的文件夹")
        self.training_data_line_edit.setStyleSheet("""
            QLineEdit { 
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                padding: 8px;
            }
        """)
        
        self.training_data_browse_btn = QPushButton("浏览")
        self.training_data_browse_btn.setStyleSheet(styles.get_button_style("small", styles.COLORS["primary"]))
        self.training_data_browse_btn.clicked.connect(self.select_training_data_folder)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.training_data_line_edit)
        path_layout.addWidget(self.training_data_browse_btn)
        layout.addLayout(path_layout)
        
        # 路径显示
        self.training_data_display_label = QLabel("未选择训练数据文件夹")
        self.training_data_display_label.setStyleSheet("""
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
        self.training_data_display_label.setWordWrap(True)
        layout.addWidget(self.training_data_display_label)
        
        parent_layout.addWidget(group)
    
    def create_base_model_group(self, parent_layout: QVBoxLayout):
        """创建基准模型选择组"""
        group = QGroupBox("基准模型选择")
        group.setStyleSheet("""
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
        group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.setSpacing(8)
        
        model_label = QLabel("基准模型文件:")
        model_label.setStyleSheet("""
            QLabel { 
                font-weight: normal; 
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        
        self.base_model_line_edit = QLineEdit()
        self.base_model_line_edit.setPlaceholderText("请选择基准模型文件 (.pt)")
        self.base_model_line_edit.setStyleSheet("""
            QLineEdit { 
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                padding: 8px;
            }
        """)
        
        self.base_model_browse_btn = QPushButton("浏览")
        self.base_model_browse_btn.setStyleSheet(styles.get_button_style("small", styles.COLORS["primary"]))
        self.base_model_browse_btn.clicked.connect(self.select_base_model_file)
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.base_model_line_edit)
        model_layout.addWidget(self.base_model_browse_btn)
        layout.addLayout(model_layout)
        
        # 模型信息显示
        self.base_model_display_label = QLabel("未选择基准模型文件")
        self.base_model_display_label.setStyleSheet("""
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
        self.base_model_display_label.setWordWrap(True)
        layout.addWidget(self.base_model_display_label)
        
        parent_layout.addWidget(group)
    
    def create_training_control_group(self, parent_layout: QVBoxLayout):
        """创建训练控制组"""
        group = QGroupBox("训练控制")
        group.setStyleSheet("""
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
        group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # 训练参数设置
        params_layout = QHBoxLayout()
        params_layout.setSpacing(10)
        
        epochs_label = QLabel("训练轮数:")
        epochs_label.setStyleSheet("""
            QLabel { 
                font-weight: normal; 
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        
        self.epochs_spinbox = QSpinBox()
        self.epochs_spinbox.setMinimum(1)
        self.epochs_spinbox.setMaximum(1000)
        self.epochs_spinbox.setValue(100)
        self.epochs_spinbox.setStyleSheet("""
            QSpinBox { 
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                padding: 6px;
            }
        """)
        
        params_layout.addWidget(epochs_label)
        params_layout.addWidget(self.epochs_spinbox)
        params_layout.addStretch()
        layout.addLayout(params_layout)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        
        self.start_training_btn = QPushButton("开始训练")
        self.start_training_btn.setStyleSheet(styles.get_button_style("large", "#28a745"))
        self.start_training_btn.clicked.connect(self.start_training)
        
        self.stop_training_btn = QPushButton("停止训练")
        self.stop_training_btn.setStyleSheet(styles.get_button_style("large", "#dc3545"))
        self.stop_training_btn.clicked.connect(self.stop_training)
        self.stop_training_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_training_btn)
        control_layout.addWidget(self.stop_training_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 进度条
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(5)
        
        progress_label = QLabel("训练进度:")
        progress_label.setStyleSheet("""
            QLabel { 
                font-weight: normal; 
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                font-size: 14px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)
        
        # 状态显示
        self.status_label = QLabel("状态: 就绪")
        self.status_label.setStyleSheet("""
            QLabel { 
                font-weight: normal; 
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                color: #28a745;
                margin-top: 5px;
            }
        """)
        layout.addWidget(self.status_label)
        
        parent_layout.addWidget(group)
    
    def create_training_log_group(self, parent_layout: QVBoxLayout):
        """创建训练日志组"""
        group = QGroupBox("训练日志")
        group.setStyleSheet("""
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
        group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # 日志显示区域
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMinimumHeight(200)
        self.log_text_edit.setStyleSheet("""
            QTextEdit {
                font-family: "Consolas", "Courier New", monospace;
                font-size: 12px;
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        # 清空日志按钮
        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.setStyleSheet(styles.get_button_style("small", styles.COLORS["secondary"]))
        clear_log_btn.clicked.connect(self.clear_log)
        
        log_control_layout = QHBoxLayout()
        log_control_layout.addWidget(clear_log_btn)
        log_control_layout.addStretch()
        
        layout.addWidget(self.log_text_edit)
        layout.addLayout(log_control_layout)
        
        parent_layout.addWidget(group)
    
    def select_training_data_folder(self):
        """选择训练数据文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择训练数据文件夹", "./"
        )
        
        if folder_path:
            self.training_data_path = folder_path
            self.training_data_line_edit.setText(folder_path)
            self.training_data_display_label.setText(f"已选择: {folder_path}")
            self.training_data_display_label.setStyleSheet("""
                QLabel { 
                    font-weight: normal; 
                    font-size: 14px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                    color: #28a745;
                    background-color: #e8f5e8;
                    border: 1px solid #28a745;
                    border-radius: 4px;
                    padding: 8px;
                    margin-top: 5px;
                }
            """)
            self.log_message(f"选择训练数据文件夹: {folder_path}")
    
    def select_base_model_file(self):
        """选择基准模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择基准模型文件", "./", "PyTorch模型文件 (*.pt);;所有文件 (*)"
        )
        
        if file_path:
            self.base_model_path = file_path
            self.base_model_line_edit.setText(file_path)
            model_name = os.path.basename(file_path)
            self.base_model_display_label.setText(f"已选择: {model_name}")
            self.base_model_display_label.setStyleSheet("""
                QLabel { 
                    font-weight: normal; 
                    font-size: 14px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                    color: #28a745;
                    background-color: #e8f5e8;
                    border: 1px solid #28a745;
                    border-radius: 4px;
                    padding: 8px;
                    margin-top: 5px;
                }
            """)
            self.log_message(f"选择基准模型文件: {file_path}")
    
    def start_training(self):
        """开始训练"""
        # 检查是否已有训练线程在运行
        if self.is_training:
            QMessageBox.warning(self, "警告", "已有训练任务在运行，请等待完成或先停止当前训练")
            return
        
        # 验证输入
        if not self.training_data_path:
            QMessageBox.warning(self, "警告", "请先选择训练数据文件夹")
            return
        
        if not self.base_model_path:
            QMessageBox.warning(self, "警告", "请先选择基准模型文件")
            return
        
        # 获取训练轮数
        self.epochs = self.epochs_spinbox.value()
        
        # 添加训练会话分隔线
        self.log_message("=" * 60)
        self.log_message(f"开始新的训练会话 - 时间: {self.get_current_time()}")
        self.log_message("=" * 60)
        
        # 创建训练工作线程
        self.training_worker = TrainingWorker(
            self.training_data_path,
            self.base_model_path,
            self.epochs
        )
        
        # 连接信号
        self.training_worker.log_updated.connect(self.log_message)
        self.training_worker.progress_updated.connect(self.update_progress)
        self.training_worker.training_finished.connect(self.on_training_finished)
        
        # 更新UI状态
        self.start_training_btn.setEnabled(False)
        self.stop_training_btn.setEnabled(True)
        self.is_training = True
        self.status_label.setText("状态: 训练中...")
        self.status_label.setStyleSheet("""
            QLabel { 
                font-weight: normal; 
                font-size: 16px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                color: #ffc107;
                margin-top: 5px;
            }
        """)
        
        # 开始训练
        self.training_worker.start()
        self.log_message("开始模型训练...")
    
    def stop_training(self):
        """停止训练"""
        if self.training_worker and self.training_worker.isRunning():
            self.training_worker.stop_training()
            self.training_worker.wait()
            self.log_message("训练已停止")
    
    def on_training_finished(self, success: bool, message: str):
        """训练完成回调"""
        # 重置训练状态
        self.is_training = False
        self.start_training_btn.setEnabled(True)
        self.stop_training_btn.setEnabled(False)
        
        # 清空进度条
        self.progress_bar.setValue(0)
        
        if success:
            self.status_label.setText("状态: 训练已启动")
            self.status_label.setStyleSheet("""
                QLabel { 
                    font-weight: normal; 
                    font-size: 16px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                    color: #28a745;
                    margin-top: 5px;
                }
            """)
            QMessageBox.information(self, "成功", message)
        else:
            self.status_label.setText("状态: 就绪")
            self.status_label.setStyleSheet("""
                QLabel { 
                    font-weight: normal; 
                    font-size: 16px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                    color: #dc3545;
                    margin-top: 5px;
                }
            """)
            QMessageBox.warning(self, "错误", message)
        
        # 添加训练会话标记
        self.log_message("=" * 60)
        if success:
            self.log_message(f"训练会话已启动 - 时间: {self.get_current_time()}")
        else:
            self.log_message(f"训练会话启动失败 - 时间: {self.get_current_time()}")
        self.log_message("=" * 60)
        self.log_message(message)
        
        # 强制刷新日志框并滚动到底部
        self.log_text_edit.verticalScrollBar().setValue(
            self.log_text_edit.verticalScrollBar().maximum()
        )
    
    def update_progress(self, value: int):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def log_message(self, message: str):
        """添加日志消息"""
        # 添加时间戳和颜色标记
        timestamp = self.get_current_time()
        formatted_message = f"[{timestamp}] {message}"
        
        # 根据消息类型添加不同的标记
        if "开始新的训练会话" in message:
            formatted_message = f"🚀 {formatted_message}"
        elif "训练已在CMD窗口中启动" in message or "训练已启动" in message:
            formatted_message = f"✅ {formatted_message}"
        elif "训练进程异常退出" in message or "错误" in message or "启动失败" in message:
            formatted_message = f"❌ {formatted_message}"
        elif "训练进程已终止" in message:
            formatted_message = f"⏹️ {formatted_message}"
        elif "Epoch" in message:
            formatted_message = f"📊 {formatted_message}"
        elif "CMD窗口" in message:
            formatted_message = f"🖥️ {formatted_message}"
        
        self.log_text_edit.append(formatted_message)
        
        # 自动滚动到底部
        self.log_text_edit.verticalScrollBar().setValue(
            self.log_text_edit.verticalScrollBar().maximum()
        )
    
    def clear_log(self):
        """清空日志"""
        self.log_text_edit.clear()
    
    def get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def load_config(self):
        """加载配置"""
        # 从配置中加载默认路径
        default_model_path = self.config.get("model_path", "")
        if default_model_path and os.path.exists(default_model_path):
            self.base_model_path = default_model_path
            self.base_model_line_edit.setText(default_model_path)
            model_name = os.path.basename(default_model_path)
            self.base_model_display_label.setText(f"已选择: {model_name}")
            self.base_model_display_label.setStyleSheet("""
                QLabel { 
                    font-weight: normal; 
                    font-size: 14px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                    color: #28a745;
                    background-color: #e8f5e8;
                    border: 1px solid #28a745;
                    border-radius: 4px;
                    padding: 8px;
                    margin-top: 5px;
                }
            """)
