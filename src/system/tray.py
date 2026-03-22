"""
系统托盘模块
提供托盘图标和快捷菜单功能
"""

from typing import Callable, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication


class TrayManager(QObject):
    """托盘管理器"""
    
    # 信号定义
    screenshot_requested = pyqtSignal()  # 请求截图
    show_window_requested = pyqtSignal()  # 请求显示主窗口
    exit_requested = pyqtSignal()  # 请求退出
    
    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)
        self.app = app
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self.menu: Optional[QMenu] = None
        
        self._setup_tray()
        
    def _setup_tray(self):
        """设置托盘图标"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self._create_default_icon())
        self.tray_icon.setToolTip("截图标注与历史管理器")
        
        # 创建右键菜单
        self.menu = QMenu()
        
        # 截图菜单项
        screenshot_action = QAction("立即截图", self)
        screenshot_action.triggered.connect(self._on_screenshot)
        self.menu.addAction(screenshot_action)
        
        self.menu.addSeparator()
        
        # 打开主窗口菜单项
        show_action = QAction("打开主窗口", self)
        show_action.triggered.connect(self._on_show_window)
        self.menu.addAction(show_action)
        
        self.menu.addSeparator()
        
        # 退出菜单项
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self._on_exit)
        self.menu.addAction(exit_action)
        
        # 设置菜单
        self.tray_icon.setContextMenu(self.menu)
        
        # 连接激活信号
        self.tray_icon.activated.connect(self._on_activated)
        
    def _create_default_icon(self) -> QIcon:
        """创建默认图标"""
        # 创建一个简单的图标
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("#4CAF50"))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "S")
        painter.end()
        
        return QIcon(pixmap)
    
    def set_icon(self, icon: QIcon):
        """设置托盘图标"""
        if self.tray_icon:
            self.tray_icon.setIcon(icon)
    
    def show(self):
        """显示托盘图标"""
        if self.tray_icon:
            self.tray_icon.show()
    
    def hide(self):
        """隐藏托盘图标"""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def show_message(self, title: str, message: str, 
                    icon=QSystemTrayIcon.MessageIcon.Information,
                    duration: int = 3000):
        """
        显示气泡通知
        
        Args:
            title: 标题
            message: 消息内容
            icon: 图标类型
            duration: 显示时长（毫秒）
        """
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, icon, duration)
    
    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """托盘图标被激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_show_window()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._on_show_window()
    
    def _on_screenshot(self):
        """截图菜单项被点击"""
        self.screenshot_requested.emit()
    
    def _on_show_window(self):
        """显示窗口菜单项被点击"""
        self.show_window_requested.emit()
    
    def _on_exit(self):
        """退出菜单项被点击"""
        self.exit_requested.emit()


# 导入Qt
from PyQt6.QtCore import Qt
