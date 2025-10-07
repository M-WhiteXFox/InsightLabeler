import os
import math
import random
import shutil
import ujson
from multiprocessing.pool import ThreadPool

# 全局标签列表（后续由 label_path 加载）
NAMES = []


class Labelme2Yolo:
    """Labelme 数据集转换为 YOLO 格式的类，支持多线程"""

    def __init__(self, labelme_dir, save_dir, val_size, thread_num):
        self.labelme_dir = labelme_dir
        self.save_dir = save_dir if save_dir != 'default' else os.path.join(
            os.path.split(labelme_dir.rstrip('/'))[0], 'YOLODataset')
        self.labels = NAMES
        self.thread_num = thread_num
        self.train_list, self.val_list = [], []

        self.make_train_val_dir()
        self.split_train_val(val_size)
        self.convert()
        self.save_yaml()

    def make_train_val_dir(self):
        """创建 train/val 目录结构"""
        if os.path.exists(self.save_dir):
            shutil.rmtree(self.save_dir)

        self.train_dir_path = os.path.join(self.save_dir, 'train')
        self.val_dir_path = os.path.join(self.save_dir, 'val')

        for path in [
            os.path.join(self.train_dir_path, 'images'),
            os.path.join(self.train_dir_path, 'labels'),
            os.path.join(self.val_dir_path, 'images'),
            os.path.join(self.val_dir_path, 'labels')
        ]:
            os.makedirs(path, exist_ok=True)

    def split_train_val(self, val_size):
        """划分训练集与验证集"""
        all_name = [f.split('.')[0] for f in os.listdir(self.labelme_dir) if f.endswith('.json')]
        random.shuffle(all_name)
        val_num = int(len(all_name) * val_size)
        self.val_list = all_name[:val_num]
        self.train_list = all_name[val_num:]

    def convert_json_to_yolo(self, json_path, yolo_path):
        """将单个 Labelme JSON 转换为 YOLO txt"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = ujson.load(f)
            img_h, img_w = json_data['imageHeight'], json_data['imageWidth']

            yolo_obj_list = []
            for shape in json_data['shapes']:
                if shape['shape_type'] == 'circle':
                    yolo_obj = self.circle_to_box(shape, img_h, img_w)
                else:
                    yolo_obj = self.other_to_box(shape, img_h, img_w)
                yolo_obj_list.append(' '.join(map(str, yolo_obj)))

            with open(yolo_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(yolo_obj_list))

            # 拷贝对应图像
            src_img = json_path.replace('.json', '.jpg')
            opt_img = yolo_path.replace('.txt', '.jpg').replace('labels', 'images')
            self._copy_image(src_img, opt_img)

            print(f"[OK] 转换完成：{os.path.basename(json_path)}")

        except Exception as e:
            print(f"[ERROR] 转换失败 {json_path}: {e}")

    def _copy_image(self, src_img, opt_img):
        """尝试不同扩展名的图像复制"""
        if os.path.exists(src_img):
            shutil.copyfile(src_img, opt_img)
            return
        for ext in ['.JPG', '.jpeg', '.png', '.JPEG', '.PNG']:
            candidate = src_img[:-4] + ext
            if os.path.exists(candidate):
                shutil.copyfile(candidate, opt_img)
                return
        print(f"[WARN] 找不到图像: {src_img}")

    def circle_to_box(self, shape, img_h, img_w):
        """圆形标注转为 YOLO 格式"""
        obj_center_x, obj_center_y = shape['points'][0]
        radius = math.sqrt((obj_center_x - shape['points'][1][0]) ** 2 +
                           (obj_center_y - shape['points'][1][1]) ** 2)
        obj_w = obj_h = 2 * radius
        label_id = self.labels.index(shape['label'])
        return [
            label_id,
            round(obj_center_x / img_w, 6),
            round(obj_center_y / img_h, 6),
            round(obj_w / img_w, 6),
            round(obj_h / img_h, 6)
        ]

    def other_to_box(self, shape, img_h, img_w):
        """矩形/多边形标注转为 YOLO 格式"""
        x_lists = [p[0] for p in shape['points']]
        y_lists = [p[1] for p in shape['points']]
        x_min, y_min = min(x_lists), min(y_lists)
        box_w = max(x_lists) - x_min
        box_h = max(y_lists) - y_min
        label_id = self.labels.index(shape['label'])
        return [
            label_id,
            round((x_min + box_w / 2) / img_w, 6),
            round((y_min + box_h / 2) / img_h, 6),
            round(box_w / img_w, 6),
            round(box_h / img_h, 6)
        ]

    def convert(self):
        """执行多线程转换"""
        pool = ThreadPool(self.thread_num)
        for name in self.train_list:
            json_path = os.path.join(self.labelme_dir, f"{name}.json")
            yolo_path = os.path.join(self.train_dir_path, 'labels', f"{name}.txt")
            pool.apply_async(self.convert_json_to_yolo, args=(json_path, yolo_path))
        for name in self.val_list:
            json_path = os.path.join(self.labelme_dir, f"{name}.json")
            yolo_path = os.path.join(self.val_dir_path, 'labels', f"{name}.txt")
            pool.apply_async(self.convert_json_to_yolo, args=(json_path, yolo_path))
        pool.close()
        pool.join()

    def save_yaml(self):
        """保存 dataset.yaml 文件"""
        yaml_path = os.path.join(self.save_dir, 'dataset.yaml')
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(f"train: {os.path.join(self.save_dir, 'train')}\n")
            f.write(f"val: {os.path.join(self.save_dir, 'val')}\n\n")
            f.write(f"nc: {len(self.labels)}\n")
            f.write(f"names: {ujson.dumps(self.labels, ensure_ascii=False)}\n")
        print(f"[INFO] dataset.yaml 已生成：{yaml_path}")


def convert_labelme_to_yolo(labelme_dir, save_dir, label_path, val_size=0.2, thread_num=8):
    """
    对外封装的主函数
    :param labelme_dir: Labelme 数据集路径
    :param save_dir: YOLO 数据集保存路径
    :param label_path: 标签文件路径（内容为 Python list 格式）
    :param val_size: 验证集比例 (默认 0.2)
    :param thread_num: 线程数 (默认 8)
    """
    global NAMES
    with open(label_path, 'r', encoding='utf-8') as f:
        NAMES = eval(f.read().strip())

    print(f"[INFO] 标签加载成功: {NAMES}")
    print(f"[INFO] 开始转换 Labelme 数据集: {labelme_dir}")
    Labelme2Yolo(labelme_dir, save_dir, val_size, thread_num)
    print("[DONE] 数据集转换完成 ✅")
    return True;
