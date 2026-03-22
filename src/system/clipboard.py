"""
剪贴板管理模块
提供剪贴板操作功能
"""

from typing import Optional
from PyQt6.QtCore import QObject, QMimeData, QUrl
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import QApplication


class ClipboardManager(QObject):
    """剪贴板管理器"""
    
    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)
        self.app = app
        self.clipboard = app.clipboard()
    
    def copy_image(self, pixmap: QPixmap) -> bool:
        """
        复制图片到剪贴板
        
        Args:
            pixmap: 要复制的图片
            
        Returns:
            是否成功
        """
        try:
            self.clipboard.setPixmap(pixmap)
            return True
        except Exception as e:
            print(f"Failed to copy image to clipboard: {e}")
            return False
    
    def copy_image_from_file(self, filepath: str) -> bool:
        """
        从文件复制图片到剪贴板
        
        Args:
            filepath: 图片文件路径
            
        Returns:
            是否成功
        """
        try:
            pixmap = QPixmap(filepath)
            if pixmap.isNull():
                return False
            return self.copy_image(pixmap)
        except Exception as e:
            print(f"Failed to copy image from file: {e}")
            return False
    
    def copy_text(self, text: str) -> bool:
        """
        复制文本到剪贴板
        
        Args:
            text: 要复制的文本
            
        Returns:
            是否成功
        """
        try:
            self.clipboard.setText(text)
            return True
        except Exception as e:
            print(f"Failed to copy text to clipboard: {e}")
            return False
    
    def get_image(self) -> Optional[QPixmap]:
        """
        从剪贴板获取图片
        
        Returns:
            图片对象，如果没有则返回None
        """
        mime_data = self.clipboard.mimeData()
        if mime_data.hasImage():
            image = self.clipboard.image()
            if not image.isNull():
                return QPixmap.fromImage(image)
        return None
    
    def get_text(self) -> Optional[str]:
        """
        从剪贴板获取文本
        
        Returns:
            文本内容，如果没有则返回None
        """
        mime_data = self.clipboard.mimeData()
        if mime_data.hasText():
            return self.clipboard.text()
        return None
    
    def has_image(self) -> bool:
        """
        检查剪贴板是否有图片
        
        Returns:
            是否有图片
        """
        return self.clipboard.mimeData().hasImage()
    
    def has_text(self) -> bool:
        """
        检查剪贴板是否有文本
        
        Returns:
            是否有文本
        """
        return self.clipboard.mimeData().hasText()
    
    def clear(self):
        """清空剪贴板"""
        self.clipboard.clear()
