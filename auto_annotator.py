"""
自动标注模块
封装YOLO模型加载与自动检测逻辑
"""

import os
import numpy as np
from typing import List, Tuple, Optional


class AutoAnnotator:
    """
    自动标注器类
    使用YOLO模型进行目标检测和自动标注
    """
    
    def __init__(self, model_path: str = ""):
        """
        初始化自动标注器
        
        参数:
            model_path: YOLO模型文件路径
        """
        self.model_path = model_path
        self.model = None
        self.class_names = []
        
        # 如果提供了模型路径，尝试加载模型
        if model_path and os.path.exists(model_path):
            self._load_model()
        else:
            if model_path:
                print(f"警告: 模型文件不存在: {model_path}")
            else:
                print("警告: 未配置模型路径，自动标注功能不可用")
    
    def _load_model(self):
        """
        加载YOLO模型
        """
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            print(f"成功加载YOLO模型: {self.model_path}")
            
            # 获取类别名称
            if hasattr(self.model, 'names'):
                self.class_names = list(self.model.names.values())
            else:
                self.class_names = []
                
        except ImportError:
            print("错误: 未安装ultralytics库，请运行: pip install ultralytics")
            self.model = None
        except Exception as e:
            print(f"错误: 加载YOLO模型失败: {e}")
            self.model = None
    
    def predict(self, frame: np.ndarray, confidence_threshold: float = 0.5) -> List[Tuple[float, float, float, float, str]]:
        """
        对输入帧进行目标检测
        
        参数:
            frame: 输入图像帧 (numpy数组)
            confidence_threshold: 置信度阈值 (0.0-1.0)
            
        返回:
            检测结果列表，格式为 [(x1, y1, x2, y2, label), ...]
            如果模型未加载或检测失败，返回空列表
        """
        if self.model is None:
            return []
        
        if frame is None or frame.size == 0:
            print("警告: 输入帧为空")
            return []
        
        try:
            # 使用YOLO模型进行预测
            results = self.model(frame)
            
            boxes = []
            for result in results:
                # 获取边界框和类别信息
                if result.boxes is not None and len(result.boxes) > 0:
                    for i in range(len(result.boxes)):
                        try:
                            # 获取边界框坐标 (x1, y1, x2, y2)
                            box = result.boxes.xyxy[i].cpu().numpy()
                            x1, y1, x2, y2 = box
                            
                            # 获取类别ID和置信度
                            cls_id = int(result.boxes.cls[i].cpu().numpy())
                            conf = float(result.boxes.conf[i].cpu().numpy())
                            
                            # 只保留置信度高于阈值的检测结果
                            if conf >= confidence_threshold:
                                # 获取类别名称
                                if cls_id < len(self.class_names):
                                    label = self.class_names[cls_id]
                                else:
                                    label = f"class_{cls_id}"
                                
                                # 添加置信度到标签中
                                label_with_conf = f"{label} ({conf:.2f})"
                                
                                boxes.append((float(x1), float(y1), float(x2), float(y2), label_with_conf))
                        except Exception as box_error:
                            print(f"处理检测框时出错: {box_error}")
                            continue
            
            return boxes
            
        except Exception as e:
            print(f"错误: YOLO预测失败: {e}")
            return []
    
    def is_available(self) -> bool:
        """
        检查自动标注功能是否可用
        
        返回:
            True如果模型已加载，False否则
        """
        return self.model is not None
    
    def get_model_info(self) -> dict:
        """
        获取模型信息
        
        返回:
            包含模型信息的字典
        """
        return {
            "model_path": self.model_path,
            "is_loaded": self.model is not None,
            "class_names": self.class_names,
            "num_classes": len(self.class_names)
        }
