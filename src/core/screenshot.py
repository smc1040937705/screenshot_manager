"""
截图核心功能模块
提供全屏截图、窗口截图、区域截图功能
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Callable, List
import tempfile
import os

from PyQt6.QtCore import Qt, QRect, QPoint, QTimer
from PyQt6.QtGui import QPixmap, QScreen, QImage, QPainter, QColor, QPen, QCursor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, 
    QRubberBand, QPushButton, QHBoxLayout
)


class ScreenshotMode(Enum):
    """截图模式"""
    FULLSCREEN = auto()  # 全屏截图
    WINDOW = auto()      # 窗口截图
    REGION = auto()      # 区域截图


@dataclass
class ScreenshotResult:
    """截图结果"""
    pixmap: QPixmap
    mode: ScreenshotMode
    region: Optional[QRect] = None  # 截图区域（区域截图时有效）
    window_id: Optional[int] = None  # 窗口ID（窗口截图时有效）
    
    def save(self, filepath: str, quality: int = -1) -> bool:
        """保存截图到文件"""
        return self.pixmap.save(filepath, quality=quality)
    
    def to_clipboard(self, app: QApplication) -> None:
        """复制到剪贴板"""
        clipboard = app.clipboard()
        clipboard.setPixmap(self.pixmap)


class RegionSelector(QWidget):
    """区域选择器 - 用于区域截图"""
    
    selection_completed = Callable[[QRect], None]
    selection_cancelled = Callable[[], None]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        self.rubber_band: Optional[QRubberBand] = None
        self.origin: Optional[QPoint] = None
        self.selected_region: Optional[QRect] = None
        self.on_completed: Optional[Callable[[QRect], None]] = None
        self.on_cancelled: Optional[Callable[[], None]] = None
        
        # 设置全屏覆盖
        self._setup_fullscreen()
        
    def _setup_fullscreen(self):
        """设置全屏覆盖所有显示器"""
        screens = QApplication.screens()
        total_geometry = QRect()
        for screen in screens:
            total_geometry = total_geometry.united(screen.geometry())
        self.setGeometry(total_geometry)
        
        # 创建半透明遮罩
        self.overlay_label = QLabel(self)
        self.overlay_label.setGeometry(self.rect())
        self.overlay_label.setStyleSheet("background-color: rgba(0, 0, 0, 100);")
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
            if self.rubber_band is None:
                self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
            self.rubber_band.setGeometry(QRect(self.origin, self.origin))
            self.rubber_band.show()
        elif event.button() == Qt.MouseButton.RightButton:
            self._cancel_selection()
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.rubber_band and self.origin:
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())
            
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton and self.rubber_band:
            self.selected_region = self.rubber_band.geometry()
            self.rubber_band.hide()
            self._complete_selection()
            
    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key.Key_Escape:
            self._cancel_selection()
            
    def _complete_selection(self):
        """完成选择"""
        if self.selected_region and self.on_completed:
            self.on_completed(self.selected_region)
        self.close()
        
    def _cancel_selection(self):
        """取消选择"""
        if self.on_cancelled:
            self.on_cancelled()
        self.close()


class ScreenshotCapture:
    """截图捕获器"""
    
    def __init__(self, app: QApplication):
        self.app = app
        self._region_selector: Optional[RegionSelector] = None
        
    def capture_fullscreen(self, screen: Optional[QScreen] = None) -> ScreenshotResult:
        """
        全屏截图
        
        Args:
            screen: 指定屏幕，None则使用主屏幕
            
        Returns:
            ScreenshotResult: 截图结果
        """
        if screen is None:
            screen = self.app.primaryScreen()
            
        pixmap = screen.grabWindow(0)
        return ScreenshotResult(
            pixmap=pixmap,
            mode=ScreenshotMode.FULLSCREEN
        )
    
    def capture_window(self, window_id: int) -> ScreenshotResult:
        """
        窗口截图
        
        Args:
            window_id: 窗口句柄ID
            
        Returns:
            ScreenshotResult: 截图结果
        """
        screen = self.app.primaryScreen()
        pixmap = screen.grabWindow(window_id)
        return ScreenshotResult(
            pixmap=pixmap,
            mode=ScreenshotMode.WINDOW,
            window_id=window_id
        )
    
    def capture_region(
        self, 
        on_completed: Callable[[ScreenshotResult], None],
        on_cancelled: Optional[Callable[[], None]] = None
    ) -> None:
        """
        区域截图 - 异步操作，通过回调返回结果
        
        Args:
            on_completed: 完成回调
            on_cancelled: 取消回调
        """
        def _on_region_selected(region: QRect):
            # 获取包含该区域的屏幕
            screen = self.app.primaryScreen()
            for s in self.app.screens():
                if s.geometry().contains(region):
                    screen = s
                    break
                    
            # 截取指定区域
            pixmap = screen.grabWindow(0, region.x(), region.y(), 
                                       region.width(), region.height())
            result = ScreenshotResult(
                pixmap=pixmap,
                mode=ScreenshotMode.REGION,
                region=region
            )
            on_completed(result)
            self._region_selector = None
            
        def _on_region_cancelled():
            if on_cancelled:
                on_cancelled()
            self._region_selector = None
            
        self._region_selector = RegionSelector()
        self._region_selector.on_completed = _on_region_selected
        self._region_selector.on_cancelled = _on_region_cancelled
        self._region_selector.show()
        
    def capture_active_window(self) -> Optional[ScreenshotResult]:
        """
        截取当前活动窗口
        
        Returns:
            ScreenshotResult: 截图结果，失败返回None
        """
        # 获取当前活动窗口ID
        active_window = self.app.activeWindow()
        if active_window:
            win_id = int(active_window.winId())
            return self.capture_window(win_id)
        return None


class ScreenshotPreview(QWidget):
    """截图预览组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: Optional[QPixmap] = None
        self._scale_factor = 1.0
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #2d2d2d; border: 1px solid #555;")
        layout.addWidget(self.image_label)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.zoom_in_btn = QPushButton("放大", self)
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        toolbar.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = QPushButton("缩小", self)
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        toolbar.addWidget(self.zoom_out_btn)
        
        self.fit_btn = QPushButton("适应窗口", self)
        self.fit_btn.clicked.connect(self._fit_to_window)
        toolbar.addWidget(self.fit_btn)
        
        self.actual_btn = QPushButton("实际大小", self)
        self.actual_btn.clicked.connect(self._actual_size)
        toolbar.addWidget(self.actual_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
    def set_pixmap(self, pixmap: QPixmap):
        """设置预览图片"""
        self._pixmap = pixmap
        self._update_display()
        
    def _update_display(self):
        """更新显示"""
        if self._pixmap:
            scaled = self._pixmap.scaled(
                int(self._pixmap.width() * self._scale_factor),
                int(self._pixmap.height() * self._scale_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
            
    def _zoom_in(self):
        """放大"""
        self._scale_factor = min(self._scale_factor * 1.25, 5.0)
        self._update_display()
        
    def _zoom_out(self):
        """缩小"""
        self._scale_factor = max(self._scale_factor / 1.25, 0.1)
        self._update_display()
        
    def _fit_to_window(self):
        """适应窗口"""
        if self._pixmap and self.image_label.width() > 0:
            self._scale_factor = min(
                self.image_label.width() / self._pixmap.width(),
                self.image_label.height() / self._pixmap.height()
            ) * 0.95
            self._update_display()
            
    def _actual_size(self):
        """实际大小"""
        self._scale_factor = 1.0
        self._update_display()
