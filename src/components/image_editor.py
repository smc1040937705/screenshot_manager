"""
图片编辑器组件
提供标注编辑功能
"""

from typing import Optional, Callable, List
from enum import Enum, auto

from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QImage, QMouseEvent, QKeyEvent, QWheelEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QColorDialog, QSpinBox, QLineEdit,
    QDialog, QDialogButtonBox, QFormLayout, QGroupBox,
    QButtonGroup, QRadioButton, QSlider
)

from src.core.annotation import (
    AnnotationManager, AnnotationType, RectangleAnnotation,
    ArrowAnnotation, TextAnnotation, MosaicAnnotation,
    apply_annotations_to_pixmap
)


class EditMode(Enum):
    """编辑模式"""
    VIEW = auto()       # 查看模式
    RECTANGLE = auto()  # 矩形标注
    ARROW = auto()      # 箭头标注
    TEXT = auto()       # 文字标注
    MOSAIC = auto()     # 马赛克标注


class ImageCanvas(QWidget):
    """图片画布 - 显示和编辑图片"""
    
    annotation_added = pyqtSignal()  # 标注添加信号
    annotation_modified = pyqtSignal()  # 标注修改信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: Optional[QPixmap] = None
        self._original_pixmap: Optional[QPixmap] = None
        self._annotation_manager = AnnotationManager()
        self._edit_mode = EditMode.VIEW
        self._scale_factor = 1.0
        
        # 绘制状态
        self._is_drawing = False
        self._draw_start: Optional[QPoint] = None
        self._draw_end: Optional[QPoint] = None
        self._temp_annotation: Optional[object] = None
        
        # 设置
        self.setMinimumSize(400, 300)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
    def set_pixmap(self, pixmap: QPixmap):
        """设置图片"""
        self._original_pixmap = pixmap
        self._pixmap = pixmap.copy()
        self._annotation_manager.clear()
        self._update_display()
        self.update()
        
    def get_pixmap(self) -> Optional[QPixmap]:
        """获取当前图片（含标注）"""
        if self._original_pixmap:
            return apply_annotations_to_pixmap(self._original_pixmap, 
                                              self._annotation_manager.annotations)
        return None
    
    def set_edit_mode(self, mode: EditMode):
        """设置编辑模式"""
        self._edit_mode = mode
        
        # 更新光标
        if mode == EditMode.VIEW:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)
            
    def set_annotation_color(self, color: str):
        """设置标注颜色"""
        self._annotation_manager.current_color = color
        
    def set_line_width(self, width: int):
        """设置线宽"""
        self._annotation_manager.current_line_width = width
        
    def set_font_size(self, size: int):
        """设置字体大小"""
        self._annotation_manager._current_font_size = size
        
    def set_mosaic_size(self, size: int):
        """设置马赛克大小"""
        self._annotation_manager._current_mosaic_size = size
        
    def undo(self):
        """撤销"""
        if self._annotation_manager.undo():
            self._update_display()
            self.annotation_modified.emit()
            
    def clear_annotations(self):
        """清空所有标注"""
        self._annotation_manager.clear()
        self._update_display()
        self.annotation_modified.emit()
        
    def get_annotations_json(self) -> str:
        """获取标注JSON"""
        return self._annotation_manager.serialize()
    
    def set_annotations_json(self, json_str: str):
        """从JSON加载标注"""
        self._annotation_manager.deserialize(json_str)
        self._update_display()
        
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景
        painter.fillRect(self.rect(), QColor("#2d2d2d"))
        
        if self._pixmap:
            # 计算居中位置
            x = (self.width() - self._pixmap.width()) // 2
            y = (self.height() - self._pixmap.height()) // 2
            
            # 绘制图片
            painter.drawPixmap(x, y, self._pixmap)
            
            # 绘制临时标注
            if self._temp_annotation:
                painter.translate(x, y)
                if isinstance(self._temp_annotation, MosaicAnnotation):
                    self._temp_annotation.draw(painter, self._original_pixmap.toImage())
                else:
                    self._temp_annotation.draw(painter)
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下"""
        if self._edit_mode == EditMode.VIEW or not self._original_pixmap:
            return
            
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_drawing = True
            self._draw_start = self._map_to_image(event.pos())
            self._draw_end = self._draw_start
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动"""
        if not self._is_drawing or not self._draw_start:
            return
            
        self._draw_end = self._map_to_image(event.pos())
        self._update_temp_annotation()
        self.update()
        
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放"""
        if event.button() == Qt.MouseButton.LeftButton and self._is_drawing:
            self._is_drawing = False
            self._draw_end = self._map_to_image(event.pos())
            
            # 添加标注
            if self._temp_annotation:
                self._annotation_manager.add_annotation(self._temp_annotation)
                self._temp_annotation = None
                self._update_display()
                self.annotation_added.emit()
                
    def _map_to_image(self, pos: QPoint) -> QPoint:
        """将窗口坐标映射到图片坐标"""
        if not self._pixmap:
            return pos
            
        x = (self.width() - self._pixmap.width()) // 2
        y = (self.height() - self._pixmap.height()) // 2
        
        return QPoint(pos.x() - x, pos.y() - y)
    
    def _update_temp_annotation(self):
        """更新临时标注"""
        if not self._draw_start or not self._draw_end:
            return
            
        if self._edit_mode == EditMode.RECTANGLE:
            rect = QRect(self._draw_start, self._draw_end).normalized()
            self._temp_annotation = self._annotation_manager.create_rectangle(rect)
            
        elif self._edit_mode == EditMode.ARROW:
            self._temp_annotation = self._annotation_manager.create_arrow(
                self._draw_start, self._draw_end)
            
        elif self._edit_mode == EditMode.MOSAIC:
            rect = QRect(self._draw_start, self._draw_end).normalized()
            self._temp_annotation = self._annotation_manager.create_mosaic(rect)
            
    def _update_display(self):
        """更新显示"""
        if not self._original_pixmap:
            return
            
        # 应用标注到图片
        self._pixmap = apply_annotations_to_pixmap(
            self._original_pixmap, 
            self._annotation_manager.annotations
        )
        
    def show_text_dialog(self, pos: QPoint):
        """显示文字输入对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加文字")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout(dialog)
        
        text_edit = QLineEdit()
        layout.addRow("文字内容:", text_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted and text_edit.text():
            text_annotation = self._annotation_manager.create_text(
                text_edit.text(), pos)
            self._annotation_manager.add_annotation(text_annotation)
            self._update_display()
            self.annotation_added.emit()


class ImageEditorWidget(QWidget):
    """图片编辑器组件"""
    
    save_requested = pyqtSignal()  # 保存请求
    copy_requested = pyqtSignal()  # 复制请求
    export_requested = pyqtSignal(str)  # 导出请求（格式）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 工具栏
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #f5f5f5; border-bottom: 1px solid #ddd;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 编辑模式选择
        mode_group = QGroupBox("标注工具")
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.setSpacing(5)
        
        self.mode_buttons = QButtonGroup(self)
        
        self.view_btn = QRadioButton("查看")
        self.view_btn.setChecked(True)
        self.mode_buttons.addButton(self.view_btn, EditMode.VIEW.value)
        mode_layout.addWidget(self.view_btn)
        
        self.rect_btn = QRadioButton("矩形")
        self.mode_buttons.addButton(self.rect_btn, EditMode.RECTANGLE.value)
        mode_layout.addWidget(self.rect_btn)
        
        self.arrow_btn = QRadioButton("箭头")
        self.mode_buttons.addButton(self.arrow_btn, EditMode.ARROW.value)
        mode_layout.addWidget(self.arrow_btn)
        
        self.text_btn = QRadioButton("文字")
        self.mode_buttons.addButton(self.text_btn, EditMode.TEXT.value)
        mode_layout.addWidget(self.text_btn)
        
        self.mosaic_btn = QRadioButton("马赛克")
        self.mode_buttons.addButton(self.mosaic_btn, EditMode.MOSAIC.value)
        mode_layout.addWidget(self.mosaic_btn)
        
        self.mode_buttons.idClicked.connect(self._on_mode_changed)
        toolbar_layout.addWidget(mode_group)
        
        toolbar_layout.addSpacing(20)
        
        # 颜色选择
        color_group = QGroupBox("颜色")
        color_layout = QHBoxLayout(color_group)
        
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(30, 30)
        self.color_btn.setStyleSheet("background-color: #FF0000; border: 1px solid #999;")
        self.color_btn.clicked.connect(self._on_color_clicked)
        color_layout.addWidget(self.color_btn)
        
        toolbar_layout.addWidget(color_group)
        
        # 线宽选择
        width_group = QGroupBox("线宽")
        width_layout = QHBoxLayout(width_group)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 20)
        self.width_spin.setValue(2)
        self.width_spin.valueChanged.connect(self._on_width_changed)
        width_layout.addWidget(self.width_spin)
        
        toolbar_layout.addWidget(width_group)
        
        toolbar_layout.addStretch()
        
        # 撤销和清空
        self.undo_btn = QPushButton("撤销")
        self.undo_btn.clicked.connect(self._on_undo)
        toolbar_layout.addWidget(self.undo_btn)
        
        self.clear_btn = QPushButton("清空标注")
        self.clear_btn.clicked.connect(self._on_clear)
        toolbar_layout.addWidget(self.clear_btn)
        
        toolbar_layout.addSpacing(20)
        
        # 操作按钮
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_requested.emit)
        toolbar_layout.addWidget(self.save_btn)
        
        self.copy_btn = QPushButton("复制")
        self.copy_btn.clicked.connect(self.copy_requested.emit)
        toolbar_layout.addWidget(self.copy_btn)
        
        layout.addWidget(toolbar)
        
        # 画布
        self.canvas = ImageCanvas()
        self.canvas.annotation_added.connect(self._on_annotation_changed)
        self.canvas.annotation_modified.connect(self._on_annotation_changed)
        layout.addWidget(self.canvas)
        
        # 底部状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self._current_color = "#FF0000"
        
    def set_image(self, pixmap: QPixmap):
        """设置图片"""
        self.canvas.set_pixmap(pixmap)
        self._update_status()
        
    def get_image(self) -> Optional[QPixmap]:
        """获取当前图片"""
        return self.canvas.get_pixmap()
    
    def get_annotations(self) -> str:
        """获取标注数据"""
        return self.canvas.get_annotations_json()
    
    def set_annotations(self, json_str: str):
        """设置标注数据"""
        self.canvas.set_annotations_json(json_str)
        
    def _on_mode_changed(self, mode_id: int):
        """编辑模式改变"""
        mode = EditMode(mode_id)
        self.canvas.set_edit_mode(mode)
        
        if mode == EditMode.TEXT:
            # 文字模式需要特殊处理
            self.canvas.show_text_dialog(QPoint(50, 50))
            self.view_btn.setChecked(True)
            self.canvas.set_edit_mode(EditMode.VIEW)
            
    def _on_color_clicked(self):
        """颜色按钮点击"""
        color = QColorDialog.getColor(QColor(self._current_color), self)
        if color.isValid():
            self._current_color = color.name()
            self.color_btn.setStyleSheet(
                f"background-color: {self._current_color}; border: 1px solid #999;")
            self.canvas.set_annotation_color(self._current_color)
            
    def _on_width_changed(self, width: int):
        """线宽改变"""
        self.canvas.set_line_width(width)
        
    def _on_undo(self):
        """撤销"""
        self.canvas.undo()
        self._update_status()
        
    def _on_clear(self):
        """清空"""
        self.canvas.clear_annotations()
        self._update_status()
        
    def _on_annotation_changed(self):
        """标注变化"""
        self._update_status()
        
    def _update_status(self):
        """更新状态栏"""
        count = len(self.canvas._annotation_manager.annotations)
        self.status_label.setText(f"标注数量: {count}")
