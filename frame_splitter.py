"""
视频帧处理模块
负责视频帧的提取、读取、管理与导航功能
"""

import cv2
import os
import argparse
import json
from pathlib import Path
import glob
from typing import Dict, List, Optional, Callable, Any


# ==============================
# 提取视频帧并保存为图片文件
# ==============================
def extract_frames(config: Optional[Dict[str, Any]] = None,
                   progress_callback: Optional[Callable[[int, int], None]] = None,
                   verbose: bool = True, **kwargs) -> bool:
    """
    从视频中提取帧并保存为图片文件
    """
    try:
        # 合并配置
        if config is None:
            config = {}

        # 参数优先级: kwargs > config > 默认值
        video_path = kwargs.get('video_path', config.get('video_path', ''))
        output_dir = kwargs.get('output_dir', config.get('output_dir', './frames'))
        frame_interval = kwargs.get('frame_interval', config.get('frame_interval', 1))
        max_frames = kwargs.get('max_frames', config.get('max_frames', None))
        quality = kwargs.get('quality', config.get('quality', 95))

        if not video_path:
            if verbose:
                print("错误: 未指定视频文件路径")
            return False

        if not os.path.exists(video_path):
            if verbose:
                print(f"错误: 视频文件不存在: {video_path}")
            return False

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            if verbose:
                print(f"错误: 无法打开视频文件 {video_path}")
            return False

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps else 0

            if verbose:
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

                if frame_count % frame_interval == 0:
                    filename = f"frame_{saved_count:06d}.jpg"
                    filepath = os.path.join(output_dir, filename)
                    
                    # 检查图像是否有效
                    if frame is not None and frame.size > 0:
                        success = cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
                        if success:
                            saved_count += 1
                        else:
                            if verbose:
                                print(f"警告: 无法保存帧 {filename}")

                    if progress_callback:
                        progress_callback(frame_count, total_frames)

                    if saved_count % 10 == 0 and verbose:
                        print(f"已保存: {filename} (进度: {frame_count}/{total_frames} 帧)")

                    if max_frames and saved_count >= max_frames:
                        break
                frame_count += 1

            if verbose:
                print(f"\n完成! 共提取 {saved_count} 帧")
                print(f"输出目录: {output_dir}")
            return True
        finally:
            try:
                cap.release()
            except Exception as e:
                if verbose:
                    print(f"释放视频捕获对象时出错: {e}")
    except Exception as e:
        if verbose:
            print(f"帧提取过程中发生错误: {e}")
        return False


# ==============================
# 从视频直接读取指定帧（不保存）
# ==============================
def read_frame_by_index(video_path: str, frame_index: int) -> Optional[Any]:
    """
    直接从视频文件中读取指定帧并返回图像矩阵（不保存）

    参数:
        video_path: 视频文件路径
        frame_index: 目标帧索引（0 开始）
    返回:
        ndarray (BGR图像) 或 None
    """
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        return None

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("错误: 无法打开视频文件")
        return None

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        index = max(0, min(frame_index, total_frames - 1))
        cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ret, frame = cap.read()

        if not ret or frame is None:
            print("警告: 无法读取指定帧")
            return None
        return frame
    finally:
        try:
            cap.release()
        except Exception as e:
            print(f"释放视频捕获对象时出错: {e}")


# ==============================
# 获取输出文件夹中的帧列表
# ==============================
def get_frame_files(output_dir: str) -> List[str]:
    if os.path.exists(output_dir):
        return sorted(glob.glob(os.path.join(output_dir, "frame_*.jpg")))
    return []


def load_frame(frame_files: List[str], frame_index: int) -> Optional[str]:
    if 0 <= frame_index < len(frame_files):
        return frame_files[frame_index]
    return None


def get_previous_frame_index(current_index: int) -> int:
    return max(0, current_index - 1)


def get_next_frame_index(current_index: int, max_index: int) -> int:
    return min(max_index, current_index + 1)


def goto_frame_index(target_index: int, max_index: int) -> int:
    return max(0, min(max_index, target_index))


# ==============================
# 创建示例配置文件
# ==============================
def create_sample_config() -> None:
    sample_config = {
        "video_path": "",
        "output_dir": "./output",
        "frame_interval": 1,
        "max_frames": None,
        "quality": 95
    }

    with open("config_sample.json", 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=4, ensure_ascii=False)
    print("示例配置文件已创建: config_sample.json")


# ==============================
# 命令行入口
# ==============================
def main() -> None:
    parser = argparse.ArgumentParser(description="视频帧处理工具")
    parser.add_argument("--video_path", help="输入视频文件路径")
    parser.add_argument("--output", "-o", help="输出目录")
    parser.add_argument("--interval", "-i", type=int, help="帧间隔")
    parser.add_argument("--max_frames", "-m", type=int, help="最大帧数")
    parser.add_argument("--quality", "-q", type=int, help="图像质量 (1-100)")
    parser.add_argument("--create_sample", action="store_true", help="创建示例配置文件")

    args = parser.parse_args()

    if args.create_sample:
        create_sample_config()
        return

    import Utils
    config = Utils.load_config()

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

    extract_frames(config, **kwargs)