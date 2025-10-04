import cv2
import os
import argparse
import json
from pathlib import Path
import Utils
import glob


def extract_frames(config=None, **kwargs):
    """
    从视频中提取帧

    参数:
        config: 配置字典
        **kwargs: 覆盖配置的参数
    """
    # 合并配置和参数
    if config is None:
        config = {}

    # 参数优先级: kwargs > config > 默认值
    video_path = kwargs.get('video_path', config.get('video_path', ''))
    output_dir = kwargs.get('output_dir', config.get('output_dir', './frames'))
    frame_interval = kwargs.get('frame_interval', config.get('frame_interval', 1))
    max_frames = kwargs.get('max_frames', config.get('max_frames', None))
    quality = kwargs.get('quality', config.get('quality', 95))

    # 验证必要参数
    if not video_path:
        print("错误: 未指定视频文件路径")
        return False

    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        return False

    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 打开视频文件
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"错误: 无法打开视频文件 {video_path}")
        return False

    # 获取视频信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    print(f"视频信息:")
    print(f"  - 路径: {video_path}")
    print(f"  - 帧率: {fps:.2f} FPS")
    print(f"  - 总帧数: {total_frames}")
    print(f"  - 时长: {duration:.2f} 秒")
    print(f"提取参数:")
    print(f"  - 输出目录: {output_dir}")
    print(f"  - 帧间隔: {frame_interval}")
    print(f"  - 最大帧数: {max_frames if max_frames else '无限制'}")
    print(f"  - 图像质量: {quality}")

    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        # 按间隔提取帧
        if frame_count % frame_interval == 0:
            # 生成文件名
            filename = f"frame_{saved_count:06d}.jpg"
            filepath = os.path.join(output_dir, filename)

            # 保存帧
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            saved_count += 1

            if saved_count % 10 == 0:  # 每10帧打印一次进度
                print(f"已保存: {filename} (进度: {frame_count}/{total_frames} 帧)")

            # 检查是否达到最大帧数限制
            if max_frames and saved_count >= max_frames:
                break

        frame_count += 1

    # 释放资源
    cap.release()

    print(f"\n完成! 共提取 {saved_count} 帧")
    print(f"输出目录: {output_dir}")
    return True


def extract_frames_with_custom_interval(video_path, output_dir, interval, max_frames=None, quality=95):
    """
    使用自定义间隔提取视频帧
    
    参数:
        video_path: 视频文件路径
        output_dir: 输出目录
        interval: 帧间隔
        max_frames: 最大帧数
        quality: 图像质量 (1-100)
    """
    config = {
        "video_path": video_path,
        "output_dir": output_dir,
        "frame_interval": interval,
        "max_frames": max_frames,
        "quality": quality
    }
    
    return extract_frames(config)


def get_frame_files(output_dir):
    """
    获取帧文件列表
    
    参数:
        output_dir: 帧文件所在目录
    返回:
        帧文件路径列表
    """
    if os.path.exists(output_dir):
        return sorted(glob.glob(os.path.join(output_dir, "frame_*.jpg")))
    return []


def load_frame(frame_files, frame_index):
    """
    加载指定索引的帧
    
    参数:
        frame_files: 帧文件列表
        frame_index: 帧索引
    返回:
        帧文件路径或None（如果索引无效）
    """
    if 0 <= frame_index < len(frame_files):
        return frame_files[frame_index]
    return None


def get_previous_frame_index(current_index):
    """
    获取上一帧索引
    
    参数:
        current_index: 当前帧索引
    返回:
        上一帧索引
    """
    return max(0, current_index - 1)


def get_next_frame_index(current_index, max_index):
    """
    获取下一帧索引
    
    参数:
        current_index: 当前帧索引
        max_index: 最大帧索引
    返回:
        下一帧索引
    """
    return min(max_index, current_index + 1)


def goto_frame_index(target_index, max_index):
    """
    跳转到指定帧索引
    
    参数:
        target_index: 目标帧索引
        max_index: 最大帧索引
    返回:
        有效帧索引
    """
    return max(0, min(max_index, target_index))


def create_sample_config():
    """示例配置文件"""
    sample_config = "config.json"

    with open("config_sample.json", 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=4, ensure_ascii=False)

    print("配置文件: config.json")


def main():
    parser = argparse.ArgumentParser(description="视频帧切割工具 ")
    parser.add_argument("--config", default="config.json", help="配置文件路径 (默认: config.json)")
    parser.add_argument("--video_path", help="输入视频文件路径 (覆盖配置文件)")
    parser.add_argument("--output", "-o", help="输出目录 (覆盖配置文件)")
    parser.add_argument("--interval", "-i", type=int, help="帧间隔 (覆盖配置文件)")
    parser.add_argument("--max_frames", "-m", type=int, help="最大提取帧数 (覆盖配置文件)")
    parser.add_argument("--quality", "-q", type=int, help="图像质量 (1-100) (覆盖配置文件)")
    parser.add_argument("--create_sample", action="store_true", help="创建示例配置文件")

    args = parser.parse_args()

    # 创建示例配置文件
    if args.create_sample:
        create_sample_config()
        return

    # 加载配置
    config = Utils.load_config()

    # 准备参数
    kwargs = {}
    if args.video_path:
        kwargs['video_path'] = args.video_path
    if args.output:
        kwargs['output_dir'] = args.output
    if args.interval:
        kwargs['frame_interval'] = args.interval
    if args.max_frames:
        kwargs['max_frames'] = args.max_frames
    if args.quality:
        kwargs['quality'] = args.quality

    # 使用帧间隔提取
    extract_frames(config, **kwargs)