"""
标注工具模块
提供矩形、箭头、文字、马赛克等标注功能
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import json
import math

from PyQt6.QtCore import Qt, QRect, QPoint, QPointF, QSize
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QFontMetrics,
    QBrush, QPainterPath, QImage, QPixmap
)


class AnnotationType(Enum):
    """标注类型"""
    RECTANGLE = auto()   # 矩形
    ARROW = auto()       # 箭头
    TEXT = auto()        # 文字
    MOSAIC = auto()      # 马赛克
    

@dataclass
class AnnotationData:
    """标注数据基类"""
    annotation_type: AnnotationType
    color: str = "#FF0000"  # 默认红色
    line_width: int = 2
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "type": self.annotation_type.name,
            "color": self.color,
            "line_width": self.line_width
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnnotationData":
        """从字典反序列化"""
        annotation_type = AnnotationType[data["type"]]
        
        if annotation_type == AnnotationType.RECTANGLE:
            return RectangleAnnotation.from_dict(data)
        elif annotation_type == AnnotationType.ARROW:
            return ArrowAnnotation.from_dict(data)
        elif annotation_type == AnnotationType.TEXT:
            return TextAnnotation.from_dict(data)
        elif annotation_type == AnnotationType.MOSAIC:
            return MosaicAnnotation.from_dict(data)
        
        raise ValueError(f"Unknown annotation type: {annotation_type}")


@dataclass
class RectangleAnnotation(AnnotationData):
    """矩形标注"""
    rect: QRect = field(default_factory=lambda: QRect(0, 0, 100, 100))
    fill: bool = False
    fill_color: str = "#FF0000"
    fill_alpha: int = 50  # 0-255
    
    def __post_init__(self):
        self.annotation_type = AnnotationType.RECTANGLE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "rect": [self.rect.x(), self.rect.y(), 
                    self.rect.width(), self.rect.height()],
            "fill": self.fill,
            "fill_color": self.fill_color,
            "fill_alpha": self.fill_alpha
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RectangleAnnotation":
        rect_data = data["rect"]
        return cls(
            annotation_type=AnnotationType.RECTANGLE,
            rect=QRect(rect_data[0], rect_data[1], rect_data[2], rect_data[3]),
            color=data["color"],
            line_width=data["line_width"],
            fill=data.get("fill", False),
            fill_color=data.get("fill_color", "#FF0000"),
            fill_alpha=data.get("fill_alpha", 50)
        )
    
    def draw(self, painter: QPainter):
        """绘制矩形"""
        pen = QPen(QColor(self.color))
        pen.setWidth(self.line_width)
        painter.setPen(pen)
        
        if self.fill:
            fill_color = QColor(self.fill_color)
            fill_color.setAlpha(self.fill_alpha)
            painter.setBrush(QBrush(fill_color))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        
        painter.drawRect(self.rect)


@dataclass
class ArrowAnnotation(AnnotationData):
    """箭头标注"""
    start: QPoint = field(default_factory=lambda: QPoint(0, 0))
    end: QPoint = field(default_factory=lambda: QPoint(100, 100))
    arrow_size: int = 15
    
    def __post_init__(self):
        self.annotation_type = AnnotationType.ARROW
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "start": [self.start.x(), self.start.y()],
            "end": [self.end.x(), self.end.y()],
            "arrow_size": self.arrow_size
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArrowAnnotation":
        start_data = data["start"]
        end_data = data["end"]
        return cls(
            annotation_type=AnnotationType.ARROW,
            start=QPoint(start_data[0], start_data[1]),
            end=QPoint(end_data[0], end_data[1]),
            color=data["color"],
            line_width=data["line_width"],
            arrow_size=data.get("arrow_size", 15)
        )
    
    def draw(self, painter: QPainter):
        """绘制箭头"""
        pen = QPen(QColor(self.color))
        pen.setWidth(self.line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QColor(self.color))
        
        # 绘制主线
        painter.drawLine(self.start, self.end)
        
        # 计算箭头角度
        angle = math.atan2(self.end.y() - self.start.y(), 
                          self.end.x() - self.start.x())
        
        # 绘制箭头头部
        arrow_angle = math.pi / 6  # 30度
        
        p1 = QPointF(
            self.end.x() - self.arrow_size * math.cos(angle - arrow_angle),
            self.end.y() - self.arrow_size * math.sin(angle - arrow_angle)
        )
        p2 = QPointF(
            self.end.x() - self.arrow_size * math.cos(angle + arrow_angle),
            self.end.y() - self.arrow_size * math.sin(angle + arrow_angle)
        )
        
        path = QPainterPath()
        path.moveTo(QPointF(self.end))
        path.lineTo(p1)
        path.lineTo(p2)
        path.closeSubpath()
        painter.drawPath(path)


@dataclass
class TextAnnotation(AnnotationData):
    """文字标注"""
    text: str = ""
    pos: QPoint = field(default_factory=lambda: QPoint(0, 0))
    font_size: int = 14
    font_family: str = "Microsoft YaHei"
    background: bool = True
    bg_color: str = "#FFFF00"
    bg_alpha: int = 180
    
    def __post_init__(self):
        self.annotation_type = AnnotationType.TEXT
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "text": self.text,
            "pos": [self.pos.x(), self.pos.y()],
            "font_size": self.font_size,
            "font_family": self.font_family,
            "background": self.background,
            "bg_color": self.bg_color,
            "bg_alpha": self.bg_alpha
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextAnnotation":
        pos_data = data["pos"]
        return cls(
            annotation_type=AnnotationType.TEXT,
            text=data["text"],
            pos=QPoint(pos_data[0], pos_data[1]),
            color=data["color"],
            line_width=data["line_width"],
            font_size=data.get("font_size", 14),
            font_family=data.get("font_family", "Microsoft YaHei"),
            background=data.get("background", True),
            bg_color=data.get("bg_color", "#FFFF00"),
            bg_alpha=data.get("bg_alpha", 180)
        )
    
    def draw(self, painter: QPainter):
        """绘制文字"""
        font = QFont(self.font_family, self.font_size)
        painter.setFont(font)
        
        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(self.text)
        text_rect.moveTo(self.pos)
        
        # 绘制背景
        if self.background:
            bg_rect = text_rect.adjusted(-4, -2, 4, 2)
            bg_color = QColor(self.bg_color)
            bg_color.setAlpha(self.bg_alpha)
            painter.fillRect(bg_rect, bg_color)
        
        # 绘制文字
        painter.setPen(QColor(self.color))
        painter.drawText(self.pos.x(), 
                        self.pos.y() + metrics.ascent(), 
                        self.text)


@dataclass
class MosaicAnnotation(AnnotationData):
    """马赛克标注"""
    rect: QRect = field(default_factory=lambda: QRect(0, 0, 100, 100))
    block_size: int = 10  # 马赛克块大小
    
    def __post_init__(self):
        self.annotation_type = AnnotationType.MOSAIC
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "rect": [self.rect.x(), self.rect.y(), 
                    self.rect.width(), self.rect.height()],
            "block_size": self.block_size
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MosaicAnnotation":
        rect_data = data["rect"]
        return cls(
            annotation_type=AnnotationType.MOSAIC,
            rect=QRect(rect_data[0], rect_data[1], rect_data[2], rect_data[3]),
            color=data["color"],
            line_width=data["line_width"],
            block_size=data.get("block_size", 10)
        )
    
    def draw(self, painter: QPainter, source_image: Optional[QImage] = None):
        """
        绘制马赛克效果
        
        Args:
            painter: QPainter对象
            source_image: 源图像（用于获取马赛克区域的颜色）
        """
        if source_image is None:
            return
        
        # 获取马赛克区域
        x, y = self.rect.x(), self.rect.y()
        w, h = self.rect.width(), self.rect.height()
        
        # 确保在图像范围内
        img_w, img_h = source_image.width(), source_image.height()
        x = max(0, min(x, img_w - 1))
        y = max(0, min(y, img_h - 1))
        w = min(w, img_w - x)
        h = min(h, img_h - y)
        
        # 绘制马赛克块
        for row in range(y, y + h, self.block_size):
            for col in range(x, x + w, self.block_size):
                # 计算块的实际大小
                block_w = min(self.block_size, x + w - col)
                block_h = min(self.block_size, y + h - row)
                
                # 获取块中心的颜色
                center_x = col + block_w // 2
                center_y = row + block_h // 2
                color = QColor(source_image.pixel(center_x, center_y))
                
                # 绘制块
                painter.fillRect(col, row, block_w, block_h, color)


class AnnotationManager:
    """标注管理器"""
    
    def __init__(self):
        self.annotations: List[AnnotationData] = []
        self._current_tool: AnnotationType = AnnotationType.RECTANGLE
        self._current_color: str = "#FF0000"
        self._current_line_width: int = 2
        self._current_font_size: int = 14
        self._current_mosaic_size: int = 10
        
    @property
    def current_tool(self) -> AnnotationType:
        return self._current_tool
    
    @current_tool.setter
    def current_tool(self, tool: AnnotationType):
        self._current_tool = tool
        
    @property
    def current_color(self) -> str:
        return self._current_color
    
    @current_color.setter
    def current_color(self, color: str):
        self._current_color = color
        
    @property
    def current_line_width(self) -> int:
        return self._current_line_width
    
    @current_line_width.setter
    def current_line_width(self, width: int):
        self._current_line_width = width
        
    def add_annotation(self, annotation: AnnotationData):
        """添加标注"""
        self.annotations.append(annotation)
        
    def remove_annotation(self, annotation: AnnotationData):
        """移除标注"""
        if annotation in self.annotations:
            self.annotations.remove(annotation)
            
    def clear(self):
        """清空所有标注"""
        self.annotations.clear()
        
    def undo(self) -> bool:
        """撤销最后一个标注"""
        if self.annotations:
            self.annotations.pop()
            return True
        return False
    
    def draw_all(self, painter: QPainter, source_image: Optional[QImage] = None):
        """
        绘制所有标注
        
        Args:
            painter: QPainter对象
            source_image: 源图像（马赛克需要）
        """
        for annotation in self.annotations:
            if isinstance(annotation, MosaicAnnotation):
                annotation.draw(painter, source_image)
            else:
                annotation.draw(painter)
    
    def create_rectangle(self, rect: QRect, fill: bool = False) -> RectangleAnnotation:
        """创建矩形标注"""
        return RectangleAnnotation(
            annotation_type=AnnotationType.RECTANGLE,
            rect=rect,
            color=self._current_color,
            line_width=self._current_line_width,
            fill=fill
        )
    
    def create_arrow(self, start: QPoint, end: QPoint) -> ArrowAnnotation:
        """创建箭头标注"""
        return ArrowAnnotation(
            annotation_type=AnnotationType.ARROW,
            start=start,
            end=end,
            color=self._current_color,
            line_width=self._current_line_width
        )
    
    def create_text(self, text: str, pos: QPoint) -> TextAnnotation:
        """创建文字标注"""
        return TextAnnotation(
            annotation_type=AnnotationType.TEXT,
            text=text,
            pos=pos,
            color=self._current_color,
            font_size=self._current_font_size
        )
    
    def create_mosaic(self, rect: QRect) -> MosaicAnnotation:
        """创建马赛克标注"""
        return MosaicAnnotation(
            annotation_type=AnnotationType.MOSAIC,
            rect=rect,
            block_size=self._current_mosaic_size
        )
    
    def serialize(self) -> str:
        """序列化所有标注为JSON字符串"""
        data = [ann.to_dict() for ann in self.annotations]
        return json.dumps(data, ensure_ascii=False)
    
    def deserialize(self, json_str: str):
        """从JSON字符串反序列化标注"""
        self.annotations.clear()
        data = json.loads(json_str)
        for item in data:
            try:
                annotation = AnnotationData.from_dict(item)
                self.annotations.append(annotation)
            except (KeyError, ValueError) as e:
                print(f"Failed to deserialize annotation: {e}")
                continue
    
    def get_annotation_at(self, pos: QPoint, tolerance: int = 5) -> Optional[AnnotationData]:
        """
        获取指定位置的标注
        
        Args:
            pos: 位置
            tolerance: 容差
            
        Returns:
            找到的标注，没找到返回None
        """
        for annotation in reversed(self.annotations):
            if self._is_point_on_annotation(annotation, pos, tolerance):
                return annotation
        return None
    
    def _is_point_on_annotation(self, annotation: AnnotationData, 
                                 pos: QPoint, tolerance: int) -> bool:
        """检查点是否在标注上"""
        if isinstance(annotation, RectangleAnnotation):
            rect = annotation.rect.adjusted(-tolerance, -tolerance, 
                                           tolerance, tolerance)
            return rect.contains(pos)
        elif isinstance(annotation, ArrowAnnotation):
            # 检查点是否在线段附近
            return self._point_to_line_distance(pos, annotation.start, 
                                               annotation.end) <= tolerance
        elif isinstance(annotation, TextAnnotation):
            # 简化为检查点是否在文字矩形内
            metrics = QFontMetrics(QFont(annotation.font_family, annotation.font_size))
            rect = metrics.boundingRect(annotation.text)
            rect.moveTo(annotation.pos)
            return rect.contains(pos)
        elif isinstance(annotation, MosaicAnnotation):
            return annotation.rect.contains(pos)
        return False
    
    def _point_to_line_distance(self, point: QPoint, line_start: QPoint, 
                                line_end: QPoint) -> float:
        """计算点到线段的距离"""
        x0, y0 = point.x(), point.y()
        x1, y1 = line_start.x(), line_start.y()
        x2, y2 = line_end.x(), line_end.y()
        
        # 线段长度的平方
        line_len_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        
        if line_len_sq == 0:
            # 线段退化为点
            return math.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)
        
        # 计算投影参数 t
        t = max(0, min(1, ((x0 - x1) * (x2 - x1) + (y0 - y1) * (y2 - y1)) / line_len_sq))
        
        # 投影点
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        # 返回距离
        return math.sqrt((x0 - proj_x) ** 2 + (y0 - proj_y) ** 2)


def apply_annotations_to_pixmap(pixmap: QPixmap, 
                                annotations: List[AnnotationData]) -> QPixmap:
    """
    将标注应用到图片上
    
    Args:
        pixmap: 原始图片
        annotations: 标注列表
        
    Returns:
        应用标注后的新图片
    """
    # 创建副本
    result = pixmap.copy()
    
    # 转换为QImage用于马赛克
    image = result.toImage()
    
    # 创建绘制器
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # 绘制所有标注
    for annotation in annotations:
        if isinstance(annotation, MosaicAnnotation):
            annotation.draw(painter, image)
        else:
            annotation.draw(painter)
    
    painter.end()
    return result
