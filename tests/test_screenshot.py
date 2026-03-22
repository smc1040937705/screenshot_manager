"""
截图功能测试
"""

import unittest
import sys
import os
import tempfile

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap

from src.core.screenshot import ScreenshotCapture, ScreenshotMode, ScreenshotResult


class TestScreenshot(unittest.TestCase):
    """测试截图功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """每个测试方法初始化"""
        self.capture = ScreenshotCapture(self.app)
    
    def test_screenshot_result_save(self):
        """测试截图结果保存"""
        # 创建一个测试图片
        pixmap = QPixmap(100, 100)
        pixmap.fill()
        
        result = ScreenshotResult(
            pixmap=pixmap,
            mode=ScreenshotMode.FULLSCREEN
        )
        
        # 测试保存
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
        
        try:
            success = result.save(temp_path)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(temp_path))
            
            # 验证保存的图片可以加载
            loaded = QPixmap(temp_path)
            self.assertFalse(loaded.isNull())
            self.assertEqual(loaded.width(), 100)
            self.assertEqual(loaded.height(), 100)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_screenshot_result_to_clipboard(self):
        """测试复制到剪贴板"""
        pixmap = QPixmap(100, 100)
        pixmap.fill()
        
        result = ScreenshotResult(
            pixmap=pixmap,
            mode=ScreenshotMode.FULLSCREEN
        )
        
        # 复制到剪贴板
        result.to_clipboard(self.app)
        
        # 验证剪贴板内容
        clipboard = self.app.clipboard()
        self.assertTrue(clipboard.mimeData().hasImage())
    
    def test_capture_fullscreen(self):
        """测试全屏截图"""
        result = self.capture.capture_fullscreen()
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ScreenshotResult)
        self.assertEqual(result.mode, ScreenshotMode.FULLSCREEN)
        self.assertFalse(result.pixmap.isNull())
        self.assertGreater(result.pixmap.width(), 0)
        self.assertGreater(result.pixmap.height(), 0)
    
    def test_screenshot_modes(self):
        """测试截图模式枚举"""
        self.assertEqual(ScreenshotMode.FULLSCREEN.name, "FULLSCREEN")
        self.assertEqual(ScreenshotMode.WINDOW.name, "WINDOW")
        self.assertEqual(ScreenshotMode.REGION.name, "REGION")


if __name__ == '__main__':
    unittest.main()
