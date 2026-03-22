"""
标注功能测试
"""

import unittest
import sys
import os
import json

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QPainter, QImage
from PyQt6.QtCore import QRect, QPoint

from src.core.annotation import (
    AnnotationManager, AnnotationType,
    RectangleAnnotation, ArrowAnnotation, TextAnnotation, MosaicAnnotation,
    apply_annotations_to_pixmap
)


class TestAnnotation(unittest.TestCase):
    """测试标注功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """每个测试方法初始化"""
        self.manager = AnnotationManager()
    
    def test_annotation_types(self):
        """测试标注类型枚举"""
        self.assertEqual(AnnotationType.RECTANGLE.name, "RECTANGLE")
        self.assertEqual(AnnotationType.ARROW.name, "ARROW")
        self.assertEqual(AnnotationType.TEXT.name, "TEXT")
        self.assertEqual(AnnotationType.MOSAIC.name, "MOSAIC")
    
    def test_create_rectangle(self):
        """测试创建矩形标注"""
        rect = QRect(10, 20, 100, 200)
        annotation = self.manager.create_rectangle(rect)
        
        self.assertIsInstance(annotation, RectangleAnnotation)
        self.assertEqual(annotation.rect, rect)
        self.assertEqual(annotation.annotation_type, AnnotationType.RECTANGLE)
    
    def test_create_arrow(self):
        """测试创建箭头标注"""
        start = QPoint(0, 0)
        end = QPoint(100, 100)
        annotation = self.manager.create_arrow(start, end)
        
        self.assertIsInstance(annotation, ArrowAnnotation)
        self.assertEqual(annotation.start, start)
        self.assertEqual(annotation.end, end)
        self.assertEqual(annotation.annotation_type, AnnotationType.ARROW)
    
    def test_create_text(self):
        """测试创建文字标注"""
        text = "测试文字"
        pos = QPoint(50, 50)
        annotation = self.manager.create_text(text, pos)
        
        self.assertIsInstance(annotation, TextAnnotation)
        self.assertEqual(annotation.text, text)
        self.assertEqual(annotation.pos, pos)
        self.assertEqual(annotation.annotation_type, AnnotationType.TEXT)
    
    def test_create_mosaic(self):
        """测试创建马赛克标注"""
        rect = QRect(0, 0, 50, 50)
        annotation = self.manager.create_mosaic(rect)
        
        self.assertIsInstance(annotation, MosaicAnnotation)
        self.assertEqual(annotation.rect, rect)
        self.assertEqual(annotation.annotation_type, AnnotationType.MOSAIC)
    
    def test_add_and_get_annotations(self):
        """测试添加和获取标注"""
        rect = QRect(0, 0, 100, 100)
        annotation = self.manager.create_rectangle(rect)
        
        self.manager.add_annotation(annotation)
        
        self.assertEqual(len(self.manager.annotations), 1)
        self.assertEqual(self.manager.annotations[0], annotation)
    
    def test_undo(self):
        """测试撤销功能"""
        # 添加两个标注
        rect1 = QRect(0, 0, 100, 100)
        rect2 = QRect(50, 50, 100, 100)
        
        self.manager.add_annotation(self.manager.create_rectangle(rect1))
        self.manager.add_annotation(self.manager.create_rectangle(rect2))
        
        self.assertEqual(len(self.manager.annotations), 2)
        
        # 撤销
        result = self.manager.undo()
        self.assertTrue(result)
        self.assertEqual(len(self.manager.annotations), 1)
        
        # 再撤销
        result = self.manager.undo()
        self.assertTrue(result)
        self.assertEqual(len(self.manager.annotations), 0)
        
        # 没有可撤销的了
        result = self.manager.undo()
        self.assertFalse(result)
    
    def test_clear(self):
        """测试清空标注"""
        self.manager.add_annotation(self.manager.create_rectangle(QRect(0, 0, 100, 100)))
        self.manager.add_annotation(self.manager.create_arrow(QPoint(0, 0), QPoint(100, 100)))
        
        self.assertEqual(len(self.manager.annotations), 2)
        
        self.manager.clear()
        
        self.assertEqual(len(self.manager.annotations), 0)
    
    def test_serialization(self):
        """测试序列化和反序列化"""
        # 添加各种标注
        self.manager.add_annotation(self.manager.create_rectangle(QRect(10, 20, 100, 200)))
        self.manager.add_annotation(self.manager.create_arrow(QPoint(0, 0), QPoint(100, 100)))
        self.manager.add_annotation(self.manager.create_text("测试", QPoint(50, 50)))
        
        # 序列化
        json_str = self.manager.serialize()
        
        # 验证是有效的JSON
        data = json.loads(json_str)
        self.assertEqual(len(data), 3)
        
        # 创建新的管理器并反序列化
        new_manager = AnnotationManager()
        new_manager.deserialize(json_str)
        
        self.assertEqual(len(new_manager.annotations), 3)
        
        # 验证类型
        self.assertIsInstance(new_manager.annotations[0], RectangleAnnotation)
        self.assertIsInstance(new_manager.annotations[1], ArrowAnnotation)
        self.assertIsInstance(new_manager.annotations[2], TextAnnotation)
    
    def test_rectangle_serialization(self):
        """测试矩形标注的序列化"""
        rect = QRect(10, 20, 100, 200)
        annotation = RectangleAnnotation(
            annotation_type=AnnotationType.RECTANGLE,
            rect=rect,
            color="#FF0000",
            line_width=3,
            fill=True,
            fill_color="#00FF00",
            fill_alpha=100
        )
        
        # 序列化
        data = annotation.to_dict()
        
        # 验证字段
        self.assertEqual(data["type"], "RECTANGLE")
        self.assertEqual(data["rect"], [10, 20, 100, 200])
        self.assertEqual(data["color"], "#FF0000")
        self.assertEqual(data["line_width"], 3)
        self.assertEqual(data["fill"], True)
        self.assertEqual(data["fill_color"], "#00FF00")
        self.assertEqual(data["fill_alpha"], 100)
        
        # 反序列化
        restored = RectangleAnnotation.from_dict(data)
        self.assertEqual(restored.rect, rect)
        self.assertEqual(restored.color, "#FF0000")
        self.assertEqual(restored.line_width, 3)
    
    def test_arrow_serialization(self):
        """测试箭头标注的序列化"""
        annotation = ArrowAnnotation(
            annotation_type=AnnotationType.ARROW,
            start=QPoint(0, 0),
            end=QPoint(100, 100),
            color="#0000FF",
            line_width=2,
            arrow_size=20
        )
        
        # 序列化
        data = annotation.to_dict()
        
        # 验证字段
        self.assertEqual(data["type"], "ARROW")
        self.assertEqual(data["start"], [0, 0])
        self.assertEqual(data["end"], [100, 100])
        self.assertEqual(data["arrow_size"], 20)
        
        # 反序列化
        restored = ArrowAnnotation.from_dict(data)
        self.assertEqual(restored.start, QPoint(0, 0))
        self.assertEqual(restored.end, QPoint(100, 100))
        self.assertEqual(restored.arrow_size, 20)
    
    def test_text_serialization(self):
        """测试文字标注的序列化"""
        annotation = TextAnnotation(
            annotation_type=AnnotationType.TEXT,
            text="Hello World",
            pos=QPoint(50, 50),
            color="#000000",
            font_size=16,
            font_family="Arial",
            background=True,
            bg_color="#FFFF00",
            bg_alpha=200
        )
        
        # 序列化
        data = annotation.to_dict()
        
        # 验证字段
        self.assertEqual(data["type"], "TEXT")
        self.assertEqual(data["text"], "Hello World")
        self.assertEqual(data["pos"], [50, 50])
        self.assertEqual(data["font_size"], 16)
        self.assertEqual(data["font_family"], "Arial")
        self.assertEqual(data["background"], True)
        
        # 反序列化
        restored = TextAnnotation.from_dict(data)
        self.assertEqual(restored.text, "Hello World")
        self.assertEqual(restored.pos, QPoint(50, 50))
        self.assertEqual(restored.font_size, 16)
    
    def test_apply_annotations_to_pixmap(self):
        """测试将标注应用到图片"""
        # 创建测试图片
        pixmap = QPixmap(200, 200)
        pixmap.fill()
        
        # 添加标注
        self.manager.add_annotation(self.manager.create_rectangle(QRect(10, 10, 50, 50)))
        
        # 应用标注
        result = apply_annotations_to_pixmap(pixmap, self.manager.annotations)
        
        self.assertIsNotNone(result)
        self.assertFalse(result.isNull())
        self.assertEqual(result.width(), 200)
        self.assertEqual(result.height(), 200)


if __name__ == '__main__':
    unittest.main()
