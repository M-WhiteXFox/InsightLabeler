"""
训练配置管理模块
负责创建和管理YOLO训练配置
"""

import os
import yaml
import shutil
from datetime import datetime
from typing import Tuple, Dict, Any


class TrainingConfig:
    """训练配置管理类"""
    
    def __init__(self):
        self.base_config = {
            'task': 'detect',
            'mode': 'train',
            'epochs': 100,
            'time': None,
            'patience': 100,
            'batch': 16,
            'imgsz': 640,
            'save': True,
            'save_period': -1,
            'cache': False,
            'device': '0',
            'workers': 8,
            'exist_ok': False,
            'pretrained': True,
            'optimizer': 'auto',
            'verbose': True,
            'seed': 0,
            'deterministic': True,
            'single_cls': False,
            'rect': False,
            'cos_lr': False,
            'close_mosaic': 10,
            'resume': False,
            'amp': True,
            'fraction': 1.0,
            'profile': False,
            'freeze': None,
            'multi_scale': False,
            'overlap_mask': True,
            'mask_ratio': 4,
            'dropout': 0.0,
            'val': True,
            'split': 'val',
            'save_json': False,
            'conf': None,
            'iou': 0.7,
            'max_det': 300,
            'half': False,
            'dnn': False,
            'plots': True,
            'source': None,
            'vid_stride': 1,
            'stream_buffer': False,
            'visualize': False,
            'augment': False,
            'agnostic_nms': False,
            'classes': None,
            'retina_masks': False,
            'embed': None,
            'show': False,
            'save_frames': False,
            'save_txt': False,
            'save_conf': False,
            'save_crop': False,
            'show_labels': True,
            'show_conf': True,
            'show_boxes': True,
            'line_width': None,
            'format': 'torchscript',
            'keras': False,
            'optimize': False,
            'int8': False,
            'dynamic': False,
            'simplify': True,
            'opset': None,
            'workspace': None,
            'nms': False,
            'lr0': 0.01,
            'lrf': 0.01,
            'momentum': 0.937,
            'weight_decay': 0.0005,
            'warmup_epochs': 3.0,
            'warmup_momentum': 0.8,
            'warmup_bias_lr': 0.1,
            'box': 7.5,
            'cls': 0.5,
            'dfl': 1.5,
            'pose': 12.0,
            'kobj': 1.0,
            'nbs': 64,
            'hsv_h': 0.015,
            'hsv_s': 0.7,
            'hsv_v': 0.4,
            'degrees': 0.0,
            'translate': 0.1,
            'scale': 0.5,
            'shear': 0.0,
            'perspective': 0.0,
            'flipud': 0.0,
            'fliplr': 0.5,
            'bgr': 0.0,
            'mosaic': 1.0,
            'mixup': 0.0,
            'cutmix': 0.0,
            'copy_paste': 0.0,
            'copy_paste_mode': 'flip',
            'auto_augment': 'randaugment',
            'erasing': 0.4,
            'cfg': None,
            'tracker': 'botsort.yaml'
        }
    
    def validate_training_data(self, data_path: str) -> Tuple[bool, str]:
        """验证训练数据格式"""
        try:
            if not os.path.exists(data_path):
                return False, "训练数据路径不存在"
            
            # 检查YOLO官方数据格式结构
            train_images_dir = os.path.join(data_path, "train", "images")
            train_labels_dir = os.path.join(data_path, "train", "labels")
            val_images_dir = os.path.join(data_path, "val", "images")
            val_labels_dir = os.path.join(data_path, "val", "labels")
            
            # 检查简单格式（images和labels文件夹）
            simple_images_dir = os.path.join(data_path, "images")
            simple_labels_dir = os.path.join(data_path, "labels")
            
            is_official_format = (os.path.exists(train_images_dir) and 
                                os.path.exists(train_labels_dir))
            is_simple_format = (os.path.exists(simple_images_dir) and 
                              os.path.exists(simple_labels_dir))
            
            if is_official_format:
                # YOLO官方格式
                return self._validate_official_format(data_path, train_images_dir, train_labels_dir, 
                                                    val_images_dir, val_labels_dir)
            elif is_simple_format:
                # 简单格式
                return self._validate_simple_format(data_path, simple_images_dir, simple_labels_dir)
            else:
                return False, "训练数据格式不正确，需要包含images和labels文件夹，或train/images、train/labels等YOLO官方格式"
            
        except Exception as e:
            return False, f"验证训练数据时发生错误: {str(e)}"
    
    def _validate_official_format(self, data_path: str, train_images_dir: str, train_labels_dir: str,
                                 val_images_dir: str, val_labels_dir: str) -> Tuple[bool, str]:
        """验证YOLO官方格式数据"""
        try:
            # 检查训练集
            train_image_files = [f for f in os.listdir(train_images_dir) 
                               if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
            if not train_image_files:
                return False, "train/images文件夹中没有找到图片文件"
            
            train_label_files = [f for f in os.listdir(train_labels_dir) 
                               if f.lower().endswith('.txt')]
            if not train_label_files:
                return False, "train/labels文件夹中没有找到标注文件"
            
            # 检查验证集（可选）
            if os.path.exists(val_images_dir) and os.path.exists(val_labels_dir):
                val_image_files = [f for f in os.listdir(val_images_dir) 
                                 if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
                val_label_files = [f for f in os.listdir(val_labels_dir) 
                                 if f.lower().endswith('.txt')]
                
                if not val_image_files:
                    return False, "val/images文件夹中没有找到图片文件"
                if not val_label_files:
                    return False, "val/labels文件夹中没有找到标注文件"
            
            return True, "YOLO官方格式训练数据验证通过"
            
        except Exception as e:
            return False, f"验证YOLO官方格式数据时发生错误: {str(e)}"
    
    def _validate_simple_format(self, data_path: str, images_dir: str, labels_dir: str) -> Tuple[bool, str]:
        """验证简单格式数据"""
        try:
            # 检查是否有图片文件
            image_files = [f for f in os.listdir(images_dir) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
            if not image_files:
                return False, "images文件夹中没有找到图片文件"
            
            # 检查是否有标注文件
            label_files = [f for f in os.listdir(labels_dir) 
                          if f.lower().endswith('.txt')]
            if not label_files:
                return False, "labels文件夹中没有找到标注文件"
            
            return True, "简单格式训练数据验证通过"
            
        except Exception as e:
            return False, f"验证简单格式数据时发生错误: {str(e)}"
    
    def create_dataset_yaml(self, data_path: str, output_path: str) -> str:
        """创建数据集配置文件"""
        try:
            # 检查数据格式并获取类别数量
            train_images_dir = os.path.join(data_path, "train", "images")
            simple_images_dir = os.path.join(data_path, "images")
            
            if os.path.exists(train_images_dir):
                # YOLO官方格式
                labels_dir = os.path.join(data_path, "train", "labels")
                val_labels_dir = os.path.join(data_path, "val", "labels")
            else:
                # 简单格式
                labels_dir = os.path.join(data_path, "labels")
                val_labels_dir = None
            
            class_ids = set()
            
            # 从训练集标签获取类别
            if os.path.exists(labels_dir):
                for label_file in os.listdir(labels_dir):
                    if label_file.endswith('.txt'):
                        label_path = os.path.join(labels_dir, label_file)
                        try:
                            with open(label_path, 'r') as f:
                                for line in f:
                                    if line.strip():
                                        class_id = int(line.strip().split()[0])
                                        class_ids.add(class_id)
                        except:
                            continue
            
            # 从验证集标签获取类别（如果存在）
            if val_labels_dir and os.path.exists(val_labels_dir):
                for label_file in os.listdir(val_labels_dir):
                    if label_file.endswith('.txt'):
                        label_path = os.path.join(val_labels_dir, label_file)
                        try:
                            with open(label_path, 'r') as f:
                                for line in f:
                                    if line.strip():
                                        class_id = int(line.strip().split()[0])
                                        class_ids.add(class_id)
                        except:
                            continue
            
            # 创建类别列表
            num_classes = max(class_ids) + 1 if class_ids else 1
            names = [f"class_{i}" for i in range(num_classes)]
            
            # 创建数据集配置
            if os.path.exists(train_images_dir):
                # YOLO官方格式
                dataset_config = {
                    'path': os.path.abspath(data_path),
                    'train': 'train/images',
                    'val': 'val/images' if os.path.exists(os.path.join(data_path, "val", "images")) else 'train/images',
                    'test': 'test/images' if os.path.exists(os.path.join(data_path, "test", "images")) else 'train/images',
                    'nc': num_classes,
                    'names': names
                }
            else:
                # 简单格式
                dataset_config = {
                    'path': os.path.abspath(data_path),
                    'train': 'images',
                    'val': 'images',
                    'test': 'images',
                    'nc': num_classes,
                    'names': names
                }
            
            # 保存配置文件
            yaml_path = os.path.join(output_path, 'dataset.yaml')
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(dataset_config, f, default_flow_style=False, allow_unicode=True)
            
            return yaml_path
            
        except Exception as e:
            raise Exception(f"创建数据集配置文件时发生错误: {str(e)}")
    
    def create_training_session(self, data_path: str, base_model_path: str) -> Tuple[str, str]:
        """创建训练会话目录"""
        try:
            # 创建基于时间戳的会话目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_name = f"train_{timestamp}"
            session_dir = os.path.join("model", session_name)
            
            # 创建目录
            os.makedirs(session_dir, exist_ok=True)
            
            # 创建数据集配置文件
            dataset_yaml_path = self.create_dataset_yaml(data_path, session_dir)
            
            return session_dir, dataset_yaml_path
            
        except Exception as e:
            raise Exception(f"创建训练会话时发生错误: {str(e)}")
    
    def create_training_args(self, session_dir: str, dataset_yaml_path: str, 
                           base_model_path: str, epochs: int = 100) -> str:
        """创建训练参数配置文件"""
        try:
            # 复制基础配置
            config = self.base_config.copy()
            
            # 设置训练参数
            config['model'] = base_model_path
            config['data'] = dataset_yaml_path
            config['epochs'] = epochs
            config['project'] = os.path.dirname(os.path.abspath(session_dir))  # 输出主目录
            config['name'] = os.path.basename(session_dir)  # 训练子目录名

            # 保存配置文件
            args_yaml_path = os.path.join(session_dir, 'args.yaml')
            with open(args_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            return args_yaml_path
            
        except Exception as e:
            raise Exception(f"创建训练参数配置时发生错误: {str(e)}")
    
    def get_available_models(self) -> list:
        """获取可用的预训练模型列表"""
        return [
            "yolo11n.pt",  # 最轻量
            "yolo11s.pt",  # 小型
            "yolo11m.pt",  # 中型
            "yolo11l.pt",  # 大型
            "yolo11x.pt",  # 超大型
        ]
