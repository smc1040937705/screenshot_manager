"""
导出功能模块
提供PNG、PDF等导出功能
"""

import os
from typing import List, Optional, Callable
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMarginsF, Qt
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPdfWriter, QPageSize


class ExportWorker(QThread):
    """导出工作线程"""
    
    progress_updated = pyqtSignal(int)  # 进度更新
    export_completed = pyqtSignal(bool, str)  # 导出完成（成功/失败，消息）
    
    def __init__(self, export_type: str, source_paths: List[str], 
                 output_path: str, parent=None):
        super().__init__(parent)
        self.export_type = export_type
        self.source_paths = source_paths
        self.output_path = output_path
    
    def run(self):
        """执行导出"""
        try:
            if self.export_type == "pdf":
                self._export_to_pdf()
            elif self.export_type == "png":
                self._export_to_png()
            else:
                self.export_completed.emit(False, f"不支持的导出类型: {self.export_type}")
        except Exception as e:
            self.export_completed.emit(False, f"导出失败: {str(e)}")
    
    def _export_to_pdf(self):
        """导出为PDF"""
        if not self.source_paths:
            self.export_completed.emit(False, "没有要导出的图片")
            return
        
        # 创建PDF写入器
        writer = QPdfWriter(self.output_path)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setResolution(150)
        writer.setPageMargins(QMarginsF(0, 0, 0, 0))
        
        painter = QPainter(writer)
        total = len(self.source_paths)
        
        for i, image_path in enumerate(self.source_paths):
            if i > 0:
                writer.newPage()
            
            # 加载图片
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                continue
            
            # 计算缩放比例以适应页面
            page_rect = writer.pageLayout().paintRectPixels(writer.resolution())
            scaled_pixmap = pixmap.scaled(
                page_rect.width(),
                page_rect.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # 居中绘制
            x = (page_rect.width() - scaled_pixmap.width()) // 2
            y = (page_rect.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
            
            # 更新进度
            progress = int((i + 1) / total * 100)
            self.progress_updated.emit(progress)
        
        painter.end()
        self.export_completed.emit(True, f"PDF已保存到: {self.output_path}")
    
    def _export_to_png(self):
        """导出为PNG（批量保存）"""
        if len(self.source_paths) == 1:
            # 单文件导出
            pixmap = QPixmap(self.source_paths[0])
            if pixmap.save(self.output_path, "PNG"):
                self.export_completed.emit(True, f"图片已保存到: {self.output_path}")
            else:
                self.export_completed.emit(False, "保存图片失败")
        else:
            # 批量导出到目录
            output_dir = Path(self.output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            total = len(self.source_paths)
            for i, image_path in enumerate(self.source_paths):
                pixmap = QPixmap(image_path)
                if pixmap.isNull():
                    continue
                
                # 生成文件名
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1}.png"
                output_file = output_dir / filename
                
                pixmap.save(str(output_file), "PNG")
                
                # 更新进度
                progress = int((i + 1) / total * 100)
                self.progress_updated.emit(progress)
            
            self.export_completed.emit(True, f"{total}张图片已导出到: {output_dir}")


class ExportManager(QObject):
    """导出管理器"""
    
    export_started = pyqtSignal()
    export_progress = pyqtSignal(int)
    export_finished = pyqtSignal(bool, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_worker: Optional[ExportWorker] = None
    
    def export_to_pdf(self, image_paths: List[str], output_path: str) -> bool:
        """
        导出为PDF
        
        Args:
            image_paths: 图片路径列表
            output_path: 输出PDF路径
            
        Returns:
            是否成功启动导出
        """
        if self._current_worker and self._current_worker.isRunning():
            return False
        
        self._current_worker = ExportWorker("pdf", image_paths, output_path, self)
        self._current_worker.progress_updated.connect(self.export_progress)
        self._current_worker.export_completed.connect(self._on_export_completed)
        
        self.export_started.emit()
        self._current_worker.start()
        return True
    
    def export_to_png(self, image_paths: List[str], output_path: str) -> bool:
        """
        导出为PNG
        
        Args:
            image_paths: 图片路径列表
            output_path: 输出路径（单文件或目录）
            
        Returns:
            是否成功启动导出
        """
        if self._current_worker and self._current_worker.isRunning():
            return False
        
        self._current_worker = ExportWorker("png", image_paths, output_path, self)
        self._current_worker.progress_updated.connect(self.export_progress)
        self._current_worker.export_completed.connect(self._on_export_completed)
        
        self.export_started.emit()
        self._current_worker.start()
        return True
    
    def save_pixmap(self, pixmap: QPixmap, filepath: str, 
                   format: str = "PNG") -> bool:
        """
        保存图片
        
        Args:
            pixmap: 图片对象
            filepath: 保存路径
            format: 图片格式
            
        Returns:
            是否成功
        """
        try:
            # 确保目录存在
            directory = os.path.dirname(filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)
            
            return pixmap.save(filepath, format)
        except Exception as e:
            print(f"Failed to save pixmap: {e}")
            return False
    
    def _on_export_completed(self, success: bool, message: str):
        """导出完成回调"""
        self.export_finished.emit(success, message)
        self._current_worker = None
    
    def cancel_export(self):
        """取消导出"""
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.terminate()
            self._current_worker.wait()
            self._current_worker = None


# 导入Qt
from PyQt6.QtCore import Qt
