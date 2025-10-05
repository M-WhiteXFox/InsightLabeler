from PyQt5.QtWidgets import QLabel, QMenu, QAction
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QWheelEvent, QKeyEvent
from PyQt5.QtCore import Qt, QRectF, QPointF


class AnnotateCanvas(QLabel):
    def __init__(self):
        super().__init__()
        # 标注框相关属性
        self.boxes = []  # [(x1, y1, x2, y2, label)]
        self.current_box = None  # (x1, y1, x2, y2, label)
        self.selected_box = None
        
        # 图像相关属性
        self.base_pixmap = None  # 原图
        self.auto_fit = True     # 是否在首次设置/窗口变化时自适应
        
        # 缩放和平移相关属性
        self.zoom_level = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # 状态控制变量
        self.edit_enabled = False  # 是否允许编辑
        self.draw_mode = False     # 是否处于新建框模式
        
        # 拖拽相关属性
        self.is_panning = False
        self.last_mouse_pos = None
        
        # 鼠标相关属性
        self.start_pos = None
        self.setMouseTracking(True)  # 启用鼠标跟踪
        self.setCursor(Qt.ArrowCursor)  # 默认光标
        
        # 调整大小相关属性
        self.resize_handle = None  # 当前调整的边角
        self.resize_start_pos = None
        self.resize_start_box = None
        
    def set_image(self, pixmap):
        """设置底图，开启 auto_fit=True 并调用 fit_to_window()"""
        self.base_pixmap = pixmap
        self.auto_fit = True
        self.fit_to_window()
        self.clear_boxes()
        self.update()
        
    def fit_to_window(self):
        """让图片以 95% 的比例适配当前控件尺寸"""
        if self.base_pixmap is None or self.base_pixmap.isNull():
            return
            
        # 获取控件尺寸
        widget_width = self.width()
        widget_height = self.height()
        
        if widget_width <= 0 or widget_height <= 0:
            return
            
        # 计算图像尺寸
        pixmap_width = self.base_pixmap.width()
        pixmap_height = self.base_pixmap.height()
        
        if pixmap_width <= 0 or pixmap_height <= 0:
            return
            
        # 计算缩放比例，以95%的比例适配窗口
        scale_x = (widget_width * 0.95) / pixmap_width
        scale_y = (widget_height * 0.95) / pixmap_height
        self.zoom_level = min(scale_x, scale_y)
        
        # 居中显示
        scaled_width = pixmap_width * self.zoom_level
        scaled_height = pixmap_height * self.zoom_level
        self.offset_x = (widget_width - scaled_width) / 2
        self.offset_y = (widget_height - scaled_height) / 2
        
        self.update()
        
    def reset_view(self):
        """重置到自适应视图"""
        self.auto_fit = True
        self.fit_to_window()
        
    def set_edit_enabled(self, enabled: bool):
        """设置编辑状态"""
        self.edit_enabled = enabled
        # 根据编辑状态设置鼠标光标
        if enabled:
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            
    def set_draw_mode(self, enabled: bool):
        """设置绘制模式"""
        self.draw_mode = enabled
        if enabled:
            self.setCursor(Qt.CrossCursor)
        else:
            # 如果不是绘制模式但编辑已启用，显示抓手光标
            if self.edit_enabled:
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        
    def load_boxes(self, box_list):
        """从外部加载标注框列表"""
        self.boxes = box_list.copy()
        self.selected_box = None
        self.current_box = None
        self.update()
        
    def get_boxes(self):
        """获取当前所有标注框"""
        return self.boxes.copy()
        
    def clear_boxes(self):
        """清空所有标注框"""
        self.boxes = []
        self.selected_box = None
        self.current_box = None
        self.update()
        
    def delete_selected_box(self):
        """删除选中的标注框"""
        if self.selected_box is not None and 0 <= self.selected_box < len(self.boxes):
            del self.boxes[self.selected_box]
            self.selected_box = None
            self.update()
            
    def delete_box_at_position(self, pos):
        """删除指定位置的标注框"""
        box_index = self.get_box_at_position(pos)
        if box_index is not None:
            del self.boxes[box_index]
            if self.selected_box == box_index:
                self.selected_box = None
            elif self.selected_box is not None and self.selected_box > box_index:
                self.selected_box -= 1
            self.update()
            return True
        return False
        
    def paintEvent(self, event):
        """绘制事件：绘制图片和所有标注框"""
        # 不调用父类的绘制方法，避免QLabel先画一次缩放后的pixmap造成重复/错位
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 应用缩放和平移变换
        painter.translate(self.offset_x, self.offset_y)
        painter.scale(self.zoom_level, self.zoom_level)
        
        # 绘制底图
        if self.base_pixmap is not None and not self.base_pixmap.isNull():
            painter.drawPixmap(0, 0, self.base_pixmap)
        
        # 绘制已存在的框
        pen = QPen(QColor(255, 0, 0), 2 / self.zoom_level)  # 红色边框，保持视觉上的一致性
        brush = QBrush(QColor(255, 0, 0, 50))  # 半透明红色填充
        painter.setPen(pen)
        painter.setBrush(brush)
        
        for i, box in enumerate(self.boxes):
            x1, y1, x2, y2, label = box
            # 确保坐标顺序正确
            left, right = min(x1, x2), max(x1, x2)
            top, bottom = min(y1, y2), max(y1, y2)
            
            rect = QRectF(left, top, right - left, bottom - top)
            painter.drawRect(rect)
            
            # 绘制标签
            if label:
                painter.drawText(int(left + 3), int(top - 5), label)
                
        # 绘制选中的框（青色）
        if self.selected_box is not None and self.selected_box < len(self.boxes):
            pen = QPen(QColor(0, 255, 255), 2 / self.zoom_level)  # 青色边框
            brush = QBrush(QColor(0, 255, 255, 50))  # 半透明青色填充
            painter.setPen(pen)
            painter.setBrush(brush)
            
            box = self.boxes[self.selected_box]
            x1, y1, x2, y2, label = box
            left, right = min(x1, x2), max(x1, x2)
            top, bottom = min(y1, y2), max(y1, y2)
            
            rect = QRectF(left, top, right - left, bottom - top)
            painter.drawRect(rect)
            
            # 绘制调整句柄
            if self.edit_enabled and not self.draw_mode:
                self.draw_resize_handles(painter, left, top, right, bottom)
            
        # 绘制正在绘制的框（半透明）
        if self.current_box is not None:
            pen = QPen(QColor(255, 0, 0), 2 / self.zoom_level)
            brush = QBrush(QColor(255, 0, 0, 100))  # 更透明的填充
            painter.setPen(pen)
            painter.setBrush(brush)
            
            x1, y1, x2, y2, label = self.current_box
            left, right = min(x1, x2), max(x1, x2)
            top, bottom = min(y1, y2), max(y1, y2)
            
            rect = QRectF(left, top, right - left, bottom - top)
            painter.drawRect(rect)
            
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 如果 auto_fit 为 True，则调用 fit_to_window()
        if self.auto_fit:
            self.fit_to_window()
            
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        # 默认查看模式：左键拖拽=平移；滚轮=缩放；不进入画框
        if not self.edit_enabled:
            if event.button() == Qt.LeftButton:
                # 左键拖拽平移
                self.is_panning = True
                self.last_mouse_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
            elif event.button() == Qt.RightButton:
                # 右键点击缩小
                self.zoom_at_point(event.pos(), 1/1.2)
            return
            
        # 编辑模式
        if event.button() == Qt.LeftButton:
            if self.draw_mode:
                # 绘制模式：开始绘制新框
                pos = self.mapToImagePos(event.pos())
                self.start_pos = pos
                self.selected_box = None
                self.current_box = (pos.x(), pos.y(), pos.x(), pos.y(), "")
            else:
                # 非绘制模式：选择框或拖拽
                clicked_box_index = self.get_box_at_position(self.mapToImagePos(event.pos()))
                if clicked_box_index is not None:
                    # 点击了现有框，选择该框
                    self.selected_box = clicked_box_index
                    self.start_pos = self.mapToImagePos(event.pos())
                    
                    # 检查是否点击了调整句柄
                    pos = self.mapToImagePos(event.pos())
                    self.resize_handle = self.get_resize_handle(pos, clicked_box_index)
                    if self.resize_handle:
                        self.resize_start_pos = pos
                        self.resize_start_box = list(self.boxes[clicked_box_index])
                else:
                    # 没有点击现有框，开启拖拽模式
                    self.is_panning = True
                    self.last_mouse_pos = event.pos()
                    self.setCursor(Qt.ClosedHandCursor)
                    
        # 右键菜单
        elif event.button() == Qt.RightButton:
            if self.edit_enabled:
                self.show_context_menu(event.pos())
                
        self.update()
        
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        # 处理拖拽
        if self.is_panning and event.buttons() & Qt.LeftButton:
            dx = event.pos().x() - self.last_mouse_pos.x()
            dy = event.pos().y() - self.last_mouse_pos.y()
            self.offset_x += dx
            self.offset_y += dy
            self.last_mouse_pos = event.pos()
            # 一旦拖拽，关闭自动适配
            self.auto_fit = False
            self.update()
            return
            
        # 仅在允许编辑时有效
        if not self.edit_enabled:
            return
            
        pos = self.mapToImagePos(event.pos())
        
        # 仅当draw_mode为True时才能绘制
        if event.buttons() & Qt.LeftButton and self.start_pos is not None:
            if self.draw_mode and self.current_box is not None:
                # 更新正在绘制的框
                x1, y1, _, _, label = self.current_box
                self.current_box = (x1, y1, pos.x(), pos.y(), label)
                self.update()
            elif not self.draw_mode and self.selected_box is not None:
                if self.resize_handle is not None:
                    # 调整大小
                    self.resize_box(pos)
                else:
                    # 拖动选中的框
                    if self.selected_box < len(self.boxes):
                        dx = pos.x() - self.start_pos.x()
                        dy = pos.y() - self.start_pos.y()
                        x1, y1, x2, y2, label = self.boxes[self.selected_box]
                        self.boxes[self.selected_box] = (x1 + dx, y1 + dy, x2 + dx, y2 + dy, label)
                        self.start_pos = pos
                        self.update()
        else:
            # 更新鼠标光标
            if self.edit_enabled and not self.draw_mode and self.selected_box is not None:
                handle = self.get_resize_handle(pos, self.selected_box)
                if handle:
                    self.setCursor(self.get_resize_cursor(handle))
                else:
                    self.setCursor(Qt.SizeAllCursor)
                
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        # 处理拖拽结束
        if self.is_panning and event.button() == Qt.LeftButton:
            self.is_panning = False
            # 恢复光标
            if self.edit_enabled:
                self.setCursor(Qt.OpenHandCursor if not self.draw_mode else Qt.CrossCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            # 一旦拖拽，关闭自动适配
            self.auto_fit = False
            return
            
        # 仅在允许编辑时有效
        if not self.edit_enabled:
            return
            
        if event.button() == Qt.LeftButton:
            if self.draw_mode and self.current_box is not None:
                # 完成绘制框
                x1, y1, x2, y2, label = self.current_box
                # 确保框有最小尺寸
                if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
                    self.boxes.append((x1, y1, x2, y2, label))
                    self.selected_box = len(self.boxes) - 1
                self.current_box = None
                self.update()
            else:
                # 清理调整大小状态
                self.resize_handle = None
                self.resize_start_pos = None
                self.resize_start_box = None
                
    def wheelEvent(self, event: QWheelEvent):
        """滚轮事件：实现缩放功能"""
        # 获取鼠标位置
        mouse_pos = event.pos()
        # 将鼠标位置转换为图像坐标
        image_pos = self.mapToImagePos(mouse_pos)
        
        # 计算缩放因子
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 1/1.1
        new_zoom = self.zoom_level * zoom_factor
        
        # 限制缩放范围
        if 0.1 <= new_zoom <= 10.0:
            self.zoom_level = new_zoom
            # 调整偏移量以实现以鼠标为中心的缩放
            self.offset_x = mouse_pos.x() - image_pos.x() * self.zoom_level
            self.offset_y = mouse_pos.y() - image_pos.y() * self.zoom_level
            
            # 边界检查：确保图像不会完全移出视野
            self._constrain_view()
            
            # 一旦缩放，关闭自动适配
            self.auto_fit = False
            self.update()
            
    def mapToImagePos(self, widget_pos):
        """将窗口坐标转换为图像坐标"""
        image_x = (widget_pos.x() - self.offset_x) / self.zoom_level
        image_y = (widget_pos.y() - self.offset_y) / self.zoom_level
        return QPointF(image_x, image_y)
        
    def get_box_at_position(self, pos):
        """获取指定位置的框索引"""
        for i, box in enumerate(self.boxes):
            x1, y1, x2, y2, label = box
            left, right = min(x1, x2), max(x1, x2)
            top, bottom = min(y1, y2), max(y1, y2)
            
            # 增加一点容差以便于点击
            if left - 5 <= pos.x() <= right + 5 and top - 5 <= pos.y() <= bottom + 5:
                return i
        return None
        
    def get_resize_handle(self, pos, box_index):
        """获取调整大小的句柄"""
        if box_index is None or box_index >= len(self.boxes):
            return None
            
        box = self.boxes[box_index]
        x1, y1, x2, y2, label = box
        left, right = min(x1, x2), max(x1, x2)
        top, bottom = min(y1, y2), max(y1, y2)
        
        handle_size = 8 / self.zoom_level  # 调整句柄大小
        
        # 检查各个角
        if abs(pos.x() - left) <= handle_size and abs(pos.y() - top) <= handle_size:
            return 'top-left'
        elif abs(pos.x() - right) <= handle_size and abs(pos.y() - top) <= handle_size:
            return 'top-right'
        elif abs(pos.x() - left) <= handle_size and abs(pos.y() - bottom) <= handle_size:
            return 'bottom-left'
        elif abs(pos.x() - right) <= handle_size and abs(pos.y() - bottom) <= handle_size:
            return 'bottom-right'
        elif abs(pos.x() - (left + right) / 2) <= handle_size and abs(pos.y() - top) <= handle_size:
            return 'top'
        elif abs(pos.x() - (left + right) / 2) <= handle_size and abs(pos.y() - bottom) <= handle_size:
            return 'bottom'
        elif abs(pos.x() - left) <= handle_size and abs(pos.y() - (top + bottom) / 2) <= handle_size:
            return 'left'
        elif abs(pos.x() - right) <= handle_size and abs(pos.y() - (top + bottom) / 2) <= handle_size:
            return 'right'
        
        return None
        
    def zoom_at_point(self, point, factor):
        """在指定点进行缩放"""
        # 将鼠标位置转换为图像坐标
        image_pos = self.mapToImagePos(point)
        
        new_zoom = self.zoom_level * factor
        
        # 限制缩放范围
        if 0.1 <= new_zoom <= 10.0:
            self.zoom_level = new_zoom
            # 调整偏移量以实现以鼠标为中心的缩放
            self.offset_x = point.x() - image_pos.x() * self.zoom_level
            self.offset_y = point.y() - image_pos.y() * self.zoom_level
            
            # 边界检查：确保图像不会完全移出视野
            self._constrain_view()
            
            # 一旦缩放，关闭自动适配
            self.auto_fit = False
            self.update()
            
    def _constrain_view(self):
        """约束视图，确保图像不会完全移出视野"""
        if self.base_pixmap is None or self.base_pixmap.isNull():
            return
            
        widget_width = self.width()
        widget_height = self.height()
        pixmap_width = self.base_pixmap.width()
        pixmap_height = self.base_pixmap.height()
        
        # 计算缩放后的图像尺寸
        scaled_width = pixmap_width * self.zoom_level
        scaled_height = pixmap_height * self.zoom_level
        
        # 约束偏移量，确保图像至少有一部分可见
        # 当图像小于窗口时，居中显示
        if scaled_width <= widget_width:
            self.offset_x = (widget_width - scaled_width) / 2
        else:
            # 当图像大于窗口时，确保图像不会完全移出视野
            min_offset_x = widget_width - scaled_width
            max_offset_x = 0
            self.offset_x = max(min(self.offset_x, max_offset_x), min_offset_x)
            
        if scaled_height <= widget_height:
            self.offset_y = (widget_height - scaled_height) / 2
        else:
            # 当图像大于窗口时，确保图像不会完全移出视野
            min_offset_y = widget_height - scaled_height
            max_offset_y = 0
            self.offset_y = max(min(self.offset_y, max_offset_y), min_offset_y)
            
    def keyPressEvent(self, event: QKeyEvent):
        """键盘事件处理"""
        if not self.edit_enabled:
            return
            
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            # 删除选中的标注框
            self.delete_selected_box()
        elif event.key() == Qt.Key_Escape:
            # 取消当前操作
            self.draw_mode = False
            self.current_box = None
            self.selected_box = None
            self.update()
            
    def resize_box(self, pos):
        """调整标注框大小"""
        if (self.resize_handle is None or self.resize_start_pos is None or 
            self.resize_start_box is None or self.selected_box is None):
            return
            
        if self.selected_box >= len(self.boxes):
            return
            
        dx = pos.x() - self.resize_start_pos.x()
        dy = pos.y() - self.resize_start_pos.y()
        
        x1, y1, x2, y2, label = self.resize_start_box
        
        # 根据句柄类型调整坐标
        if 'left' in self.resize_handle:
            x1 += dx
        if 'right' in self.resize_handle:
            x2 += dx
        if 'top' in self.resize_handle:
            y1 += dy
        if 'bottom' in self.resize_handle:
            y2 += dy
            
        # 确保最小尺寸
        if abs(x2 - x1) < 10:
            if 'left' in self.resize_handle:
                x1 = x2 - 10
            else:
                x2 = x1 + 10
        if abs(y2 - y1) < 10:
            if 'top' in self.resize_handle:
                y1 = y2 - 10
            else:
                y2 = y1 + 10
                
        self.boxes[self.selected_box] = (x1, y1, x2, y2, label)
        self.update()
        
    def get_resize_cursor(self, handle):
        """获取调整大小的光标"""
        cursor_map = {
            'top-left': Qt.SizeFDiagCursor,
            'top-right': Qt.SizeBDiagCursor,
            'bottom-left': Qt.SizeBDiagCursor,
            'bottom-right': Qt.SizeFDiagCursor,
            'top': Qt.SizeVerCursor,
            'bottom': Qt.SizeVerCursor,
            'left': Qt.SizeHorCursor,
            'right': Qt.SizeHorCursor
        }
        return cursor_map.get(handle, Qt.ArrowCursor)
        
    def show_context_menu(self, pos):
        """显示右键上下文菜单"""
        menu = QMenu(self)
        
        # 删除选项
        delete_action = QAction("删除标注框", self)
        delete_action.triggered.connect(self.delete_selected_box)
        menu.addAction(delete_action)
        
        # 清空所有选项
        clear_action = QAction("清空所有标注框", self)
        clear_action.triggered.connect(self.clear_boxes)
        menu.addAction(clear_action)
        
        # 显示菜单
        menu.exec_(self.mapToGlobal(pos))
        
    def draw_resize_handles(self, painter, left, top, right, bottom):
        """绘制调整大小的句柄"""
        handle_size = 8 / self.zoom_level
        pen = QPen(QColor(0, 0, 0), 1 / self.zoom_level)
        brush = QBrush(QColor(255, 255, 255))
        painter.setPen(pen)
        painter.setBrush(brush)
        
        # 绘制四个角的句柄
        handles = [
            (left - handle_size/2, top - handle_size/2, handle_size, handle_size),  # 左上
            (right - handle_size/2, top - handle_size/2, handle_size, handle_size),  # 右上
            (left - handle_size/2, bottom - handle_size/2, handle_size, handle_size),  # 左下
            (right - handle_size/2, bottom - handle_size/2, handle_size, handle_size),  # 右下
        ]
        
        for handle_rect in handles:
            painter.drawRect(QRectF(*handle_rect))