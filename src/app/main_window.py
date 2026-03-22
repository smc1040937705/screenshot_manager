"""
主窗口模块
提供分屏界面：左侧历史列表、右侧预览/编辑
"""

import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from PyQt6.QtCore import Qt, QSettings, QSize, QPoint, pyqtSignal
from PyQt6.QtGui import QPixmap, QKeySequence, QShortcut, QAction
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFileDialog, QMessageBox, QMenuBar,
    QMenu, QToolBar, QStatusBar, QApplication,
    QInputDialog, QLineEdit
)

from src.components.history_list import HistoryListWidget
from src.components.image_editor import ImageEditorWidget
from src.core.screenshot import ScreenshotCapture, ScreenshotMode
from src.core.annotation import apply_annotations_to_pixmap
from src.storage.database import StorageManager, ScreenshotMetadata
from src.system.tray import TrayManager
from src.system.clipboard import ClipboardManager
from src.system.export import ExportManager


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        
        # 初始化管理器
        self._init_managers()
        
        # 设置窗口
        self.setWindowTitle("截图标注与历史管理器")
        self.setMinimumSize(1200, 800)
        
        # 设置UI
        self._setup_ui()
        self._setup_menu()
        self._setup_shortcuts()
        self._setup_statusbar()
        
        # 加载设置
        self._load_settings()
        
        # 加载历史记录
        self._load_history()
        
    def _init_managers(self):
        """初始化管理器"""
        # 存储管理器
        storage_path = Path.home() / ".screenshot_manager"
        self.storage = StorageManager(str(storage_path))
        
        # 截图捕获器
        self.screenshot_capture = ScreenshotCapture(self.app)
        
        # 剪贴板管理器
        self.clipboard = ClipboardManager(self.app)
        
        # 导出管理器
        self.export_manager = ExportManager()
        self.export_manager.export_finished.connect(self._on_export_finished)
        
        # 托盘管理器
        self.tray_manager = TrayManager(self.app)
        self.tray_manager.screenshot_requested.connect(self._on_screenshot_fullscreen)
        self.tray_manager.show_window_requested.connect(self.show)
        self.tray_manager.exit_requested.connect(self._on_exit)
        self.tray_manager.show()
        
        # 设置
        self.settings = QSettings("ScreenshotManager", "MainWindow")
        
        # 当前选中的截图
        self._current_screenshot: Optional[ScreenshotMetadata] = None
        
    def _setup_ui(self):
        """设置UI"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 分割器
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：历史列表
        self.history_list = HistoryListWidget()
        self.history_list.item_selected.connect(self._on_history_item_selected)
        self.history_list.item_double_clicked.connect(self._on_history_item_double_clicked)
        self.history_list.item_favorite_toggled.connect(self._on_favorite_toggled)
        self.history_list.item_deleted.connect(self._on_delete_screenshot)
        self.history_list.setMinimumWidth(250)
        self.history_list.setMaximumWidth(400)
        self.splitter.addWidget(self.history_list)
        
        # 右侧：图片编辑器
        self.image_editor = ImageEditorWidget()
        self.image_editor.save_requested.connect(self._on_save_current)
        self.image_editor.copy_requested.connect(self._on_copy_current)
        self.splitter.addWidget(self.image_editor)
        
        # 设置分割器比例
        self.splitter.setSizes([300, 900])
        
        main_layout.addWidget(self.splitter)
        
    def _setup_menu(self):
        """设置菜单"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        # 截图子菜单
        screenshot_menu = file_menu.addMenu("截图")
        
        fullscreen_action = QAction("全屏截图", self)
        fullscreen_action.setShortcut("F1")
        fullscreen_action.triggered.connect(self._on_screenshot_fullscreen)
        screenshot_menu.addAction(fullscreen_action)
        
        region_action = QAction("区域截图", self)
        region_action.setShortcut("F2")
        region_action.triggered.connect(self._on_screenshot_region)
        screenshot_menu.addAction(region_action)
        
        file_menu.addSeparator()
        
        # 保存
        save_action = QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save_current)
        file_menu.addAction(save_action)
        
        # 另存为
        save_as_action = QAction("另存为...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._on_save_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # 导出
        export_menu = file_menu.addMenu("导出")
        
        export_png_action = QAction("导出为 PNG", self)
        export_png_action.triggered.connect(self._on_export_png)
        export_menu.addAction(export_png_action)
        
        export_pdf_action = QAction("导出为 PDF", self)
        export_pdf_action.triggered.connect(self._on_export_pdf)
        export_menu.addAction(export_pdf_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self._on_exit)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        copy_action = QAction("复制到剪贴板", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self._on_copy_current)
        edit_menu.addAction(copy_action)
        
        edit_menu.addSeparator()
        
        # 编辑元数据
        edit_meta_action = QAction("编辑信息...", self)
        edit_meta_action.triggered.connect(self._on_edit_metadata)
        edit_menu.addAction(edit_meta_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        refresh_action = QAction("刷新", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._load_history)
        view_menu.addAction(refresh_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        
    def _setup_shortcuts(self):
        """设置快捷键"""
        # 删除
        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self._on_delete_current)
        
        # 收藏
        favorite_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        favorite_shortcut.activated.connect(self._on_toggle_favorite_current)
        
    def _setup_statusbar(self):
        """设置状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪")
        
    def _load_settings(self):
        """加载设置"""
        # 窗口位置和大小
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        else:
            self.resize(1400, 900)
            self.move(100, 100)
            
        # 分割器状态
        if self.settings.contains("splitter"):
            self.splitter.restoreState(self.settings.value("splitter"))
            
    def _save_settings(self):
        """保存设置"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter", self.splitter.saveState())
        
    def _load_history(self):
        """加载历史记录"""
        screenshots = self.storage.db.get_all_screenshots()
        self.history_list.set_screenshots(screenshots)
        self.statusbar.showMessage(f"已加载 {len(screenshots)} 张截图")
        
    def _on_screenshot_fullscreen(self):
        """全屏截图"""
        # 隐藏窗口
        self.hide()
        
        # 延迟执行截图
        def do_capture():
            result = self.screenshot_capture.capture_fullscreen()
            self._on_screenshot_captured(result)
            self.show()
            
        import threading
        timer = threading.Timer(0.5, do_capture)
        timer.start()
        
    def _on_screenshot_region(self):
        """区域截图"""
        # 隐藏窗口
        self.hide()
        
        def on_completed(result):
            self._on_screenshot_captured(result)
            self.show()
            
        def on_cancelled():
            self.show()
            
        self.screenshot_capture.capture_region(on_completed, on_cancelled)
        
    def _on_screenshot_captured(self, result):
        """截图完成回调"""
        if not result or result.pixmap.isNull():
            return
            
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        
        # 保存图片
        from PyQt6.QtCore import QBuffer, QIODevice
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        result.pixmap.save(buffer, "PNG")
        image_data = buffer.data().data()
        
        # 创建元数据
        metadata = ScreenshotMetadata(
            title=f"截图 {timestamp}",
            width=result.pixmap.width(),
            height=result.pixmap.height()
        )
        
        # 保存到存储
        metadata = self.storage.save_screenshot(image_data, filename, metadata)
        
        # 添加到列表
        self.history_list.add_screenshot(metadata)
        
        # 显示通知
        self.tray_manager.show_message("截图完成", f"已保存: {metadata.title}")
        
        # 选中并显示
        self.history_list.select_screenshot(metadata.id)
        self._on_history_item_selected(metadata)
        
    def _on_history_item_selected(self, metadata: ScreenshotMetadata):
        """历史项被选中"""
        self._current_screenshot = metadata
        
        # 加载图片
        if metadata.file_path and os.path.exists(metadata.file_path):
            pixmap = QPixmap(metadata.file_path)
            self.image_editor.set_image(pixmap)
            
            # 加载标注
            if metadata.annotation_data:
                self.image_editor.set_annotations(metadata.annotation_data)
                
        self.statusbar.showMessage(f"选中: {metadata.title}")
        
    def _on_history_item_double_clicked(self, metadata: ScreenshotMetadata):
        """历史项被双击"""
        self._on_history_item_selected(metadata)
        
    def _on_favorite_toggled(self, screenshot_id: int, is_favorite: bool):
        """收藏状态切换"""
        self.storage.db.toggle_favorite(screenshot_id)
        self._load_history()
        
    def _on_delete_screenshot(self, screenshot_id: int):
        """删除截图"""
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这张截图吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.storage.delete_screenshot(screenshot_id):
                self.history_list.remove_screenshot(screenshot_id)
                self.image_editor.set_image(QPixmap())  # 清空编辑器
                self._current_screenshot = None
                self.statusbar.showMessage("已删除")
            else:
                QMessageBox.warning(self, "错误", "删除失败")
                
    def _on_delete_current(self):
        """删除当前选中的截图"""
        if self._current_screenshot:
            self._on_delete_screenshot(self._current_screenshot.id)
            
    def _on_toggle_favorite_current(self):
        """切换当前截图的收藏状态"""
        if self._current_screenshot:
            self._on_favorite_toggled(
                self._current_screenshot.id, 
                not self._current_screenshot.is_favorite
            )
            
    def _on_save_current(self):
        """保存当前截图"""
        if not self._current_screenshot:
            return
            
        # 获取带标注的图片
        pixmap = self.image_editor.get_image()
        if pixmap and not pixmap.isNull():
            # 保存到原文件
            pixmap.save(self._current_screenshot.file_path, "PNG")
            
            # 保存标注数据
            annotation_data = self.image_editor.get_annotations()
            self.storage.db.update_annotation_data(
                self._current_screenshot.id, annotation_data)
            
            self.statusbar.showMessage("已保存")
            self.tray_manager.show_message("保存成功", "截图已保存")
            
    def _on_save_as(self):
        """另存为"""
        if not self._current_screenshot:
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, "另存为", self._current_screenshot.filename,
            "PNG Images (*.png);;JPEG Images (*.jpg *.jpeg);;All Files (*.*)"
        )
        
        if filepath:
            pixmap = self.image_editor.get_image()
            if pixmap and not pixmap.isNull():
                pixmap.save(filepath)
                self.statusbar.showMessage(f"已保存到: {filepath}")
                
    def _on_copy_current(self):
        """复制当前截图到剪贴板"""
        pixmap = self.image_editor.get_image()
        if pixmap and not pixmap.isNull():
            self.clipboard.copy_image(pixmap)
            self.statusbar.showMessage("已复制到剪贴板")
            self.tray_manager.show_message("复制成功", "截图已复制到剪贴板")
            
    def _on_export_png(self):
        """导出为PNG"""
        if not self._current_screenshot:
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出PNG", f"{self._current_screenshot.title}.png",
            "PNG Images (*.png)"
        )
        
        if filepath:
            pixmap = self.image_editor.get_image()
            if pixmap and not pixmap.isNull():
                pixmap.save(filepath, "PNG")
                self.statusbar.showMessage(f"已导出: {filepath}")
                
    def _on_export_pdf(self):
        """导出为PDF"""
        if not self._current_screenshot:
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出PDF", f"{self._current_screenshot.title}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if filepath:
            self.export_manager.export_to_pdf(
                [self._current_screenshot.file_path], filepath)
            
    def _on_export_finished(self, success: bool, message: str):
        """导出完成"""
        if success:
            self.statusbar.showMessage(message)
        else:
            QMessageBox.warning(self, "导出失败", message)
            
    def _on_edit_metadata(self):
        """编辑元数据"""
        if not self._current_screenshot:
            return
            
        # 编辑标题
        title, ok = QInputDialog.getText(
            self, "编辑标题", "标题:",
            QLineEdit.EchoMode.Normal,
            self._current_screenshot.title
        )
        
        if ok:
            self._current_screenshot.title = title
            self.storage.db.update_screenshot(self._current_screenshot)
            self._load_history()
            
    def _on_about(self):
        """关于对话框"""
        QMessageBox.about(
            self, "关于",
            "<h2>截图标注与历史管理器</h2>"
            "<p>版本: 1.0.0</p>"
            "<p>基于 Python + PyQt6 构建</p>"
            "<p>功能:</p>"
            "<ul>"
            "<li>全屏/区域截图</li>"
            "<li>标注工具: 矩形、箭头、文字、马赛克</li>"
            "<li>历史管理、收藏、搜索</li>"
            "<li>导出为 PNG/PDF</li>"
            "</ul>"
        )
        
    def _on_exit(self):
        """退出应用"""
        self._save_settings()
        self.app.quit()
        
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        # 确保窗口被激活
        self.raise_()
        self.activateWindow()
        
    def closeEvent(self, event):
        """关闭事件"""
        self._save_settings()
        # 最小化到托盘而不是退出
        if self.tray_manager.tray_icon and self.tray_manager.tray_icon.isVisible():
            self.hide()
            self.tray_manager.show_message(
                "程序已最小化",
                "截图管理器仍在后台运行，点击托盘图标可恢复窗口"
            )
            event.ignore()
        else:
            event.accept()
