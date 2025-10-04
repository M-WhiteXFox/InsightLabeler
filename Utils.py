"""
工具模块
提供通用的工具函数
"""

import json
import os
from typing import Dict, Any, Optional

# 配置文件路径
CONFIG_FILE = "config.json"

# 默认配置
DEFAULT_CONFIG = {
    "video_path": "",
    "output_dir": "./output",
    "frame_interval": 1,
    "max_frames": None,
    "quality": 95,
    "last_dir": "./"
}


def load_config() -> Dict[str, Any]:
    """
    加载配置文件，如果不存在则创建默认配置
    
    返回:
        配置字典
    """
    if not os.path.exists(CONFIG_FILE):
        # 创建默认配置
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    else:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # 验证并补充缺失的配置项
                validated_config = validate_config(config)
                # 如果配置有变化，保存更新后的配置
                if validated_config != config:
                    save_config(validated_config)
                return validated_config
        except (json.JSONDecodeError, IOError) as e:
            print(f"配置文件读取错误: {e}，使用默认配置")
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证配置项完整性，补充缺失的配置项
    
    参数:
        config: 配置字典
    返回:
        验证后的配置字典
    """
    validated_config = DEFAULT_CONFIG.copy()
    validated_config.update(config)
    return validated_config


def save_config(config: Dict[str, Any]) -> None:
    """
    保存配置文件
    
    参数:
        config: 配置字典
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"配置文件保存错误: {e}")


def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    安全地获取配置值
    
    参数:
        config: 配置字典
        key: 配置键
        default: 默认值
    返回:
        配置值或默认值
    """
    return config.get(key, default)