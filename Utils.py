import json
import os

CONFIG_FILE = "config.json"

def load_config():
    """加载配置文件，如果不存在则创建默认配置"""
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "video_path": "",
            "output_dir": "./output",
            "frame_interval": 1,
            "max_frames": None,
            "quality": 95,
            "last_dir": "./"
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        return default_config
    else:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

#def get_config(name):

def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)