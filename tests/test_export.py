"""
导出功能测试
"""

import unittest
import sys
import os
import tempfile
import shutil

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap

from src.system.export import ExportManager


class TestExport(unittest.TestCase):
    """测试导出功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """每个测试方法初始化"""
        self.temp_dir = tempfile.mkdtemp()
        self.export_manager = ExportManager()
    
    def tearDown(self):
        """每个测试方法清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_pixmap(self):
        """测试保存图片"""
        # 创建测试图片
        pixmap = QPixmap(100, 100)
        pixmap.fill()
        
        # 保存
        output_path = os.path.join(self.temp_dir, "test.png")
        success = self.export_manager.save_pixmap(pixmap, output_path, "PNG")
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        # 验证可以加载
        loaded = QPixmap(output_path)
        self.assertFalse(loaded.isNull())
        self.assertEqual(loaded.width(), 100)
        self.assertEqual(loaded.height(), 100)
    
    def test_save_pixmap_creates_directory(self):
        """测试保存图片时自动创建目录"""
        pixmap = QPixmap(50, 50)
        pixmap.fill()
        
        # 保存到不存在的子目录
        output_path = os.path.join(self.temp_dir, "subdir1", "subdir2", "test.png")
        success = self.export_manager.save_pixmap(pixmap, output_path, "PNG")
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))


class TestExportManagerSignals(unittest.TestCase):
    """测试导出管理器信号"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """每个测试方法初始化"""
        self.temp_dir = tempfile.mkdtemp()
        self.export_manager = ExportManager()
        self.signals_received = []
    
    def tearDown(self):
        """每个测试方法清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_export_signals(self):
        """测试导出信号"""
        # 创建测试图片
        pixmap = QPixmap(100, 100)
        pixmap.fill()
        
        image_path = os.path.join(self.temp_dir, "test.png")
        pixmap.save(image_path, "PNG")
        
        # 连接信号
        def on_started():
            self.signals_received.append("started")
        
        def on_progress(value):
            self.signals_received.append(("progress", value))
        
        def on_finished(success, message):
            self.signals_received.append(("finished", success, message))
        
        self.export_manager.export_started.connect(on_started)
        self.export_manager.export_progress.connect(on_progress)
        self.export_manager.export_finished.connect(on_finished)
        
        # 导出
        output_path = os.path.join(self.temp_dir, "output.png")
        self.export_manager.export_to_png([image_path], output_path)
        
        # 等待导出完成
        import time
        time.sleep(0.5)
        
        # 验证信号
        self.assertIn("started", self.signals_received)
        finished_signals = [s for s in self.signals_received if s[0] == "finished"]
        self.assertEqual(len(finished_signals), 1)
        self.assertTrue(finished_signals[0][1])  # success = True


if __name__ == '__main__':
    unittest.main()
