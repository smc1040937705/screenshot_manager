"""
历史列表组件
显示截图历史列表，支持搜索、收藏、删除等功能
"""

from typing import List, Optional, Callable
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon, QColor, QFont, QFontMetrics
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QLineEdit, QMenu, QAbstractItemView,
    QFrame, QStyledItemDelegate, QStyleOptionViewItem, QStyle
)

from src.storage.database import ScreenshotMetadata


class ScreenshotItemDelegate(QStyledItemDelegate):
    """截图列表项委托 - 自定义绘制"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnail_size = QSize(80, 60)
        self.padding = 10
        
    def paint(self, painter, option, index):
        """绘制列表项"""
        metadata = index.data(Qt.ItemDataRole.UserRole)
        if not metadata:
            super().paint(painter, option, index)
            return
        
        painter.save()
        
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#0078D4"))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor("#3d3d3d"))
        else:
            painter.fillRect(option.rect, QColor("#2d2d2d"))
        
        thumb_rect = option.rect.adjusted(self.padding, self.padding, 
                                          -option.rect.width() + self.thumbnail_size.width() + self.padding * 2, 
                                          -self.padding)
        painter.setPen(QColor("#555555"))
        painter.drawRect(thumb_rect)
        
        title_rect = option.rect.adjusted(self.thumbnail_size.width() + self.padding * 3, 
                                          self.padding + 5,
                                          -self.padding, 
                                          0)
        painter.setPen(QColor("white" if option.state & QStyle.StateFlag.State_Selected else "#ddd"))
        font = QFont("Microsoft YaHei", 10, QFont.Weight.Bold)
        painter.setFont(font)
        title = metadata.title if metadata.title else metadata.filename
        painter.drawText(title_rect, Qt.TextFlag.TextSingleLine, title)
        
        date_rect = option.rect.adjusted(self.thumbnail_size.width() + self.padding * 3, 
                                         self.padding + 30,
                                         -self.padding, 
                                         0)
        painter.setPen(QColor("white" if option.state & QStyle.StateFlag.State_Selected else "#999"))
        font = QFont("Microsoft YaHei", 8)
        painter.setFont(font)
        if metadata.created_at:
            date_str = metadata.created_at.strftime("%Y-%m-%d %H:%M")
        else:
            date_str = "未知时间"
        painter.drawText(date_rect, Qt.TextFlag.TextSingleLine, date_str)
        
        if metadata.is_favorite:
            star_rect = option.rect.adjusted(option.rect.width() - 30, 
                                            self.padding + 5,
                                            -self.padding, 
                                            0)
            painter.setPen(QColor("#FFD700"))
            font = QFont("Arial", 12)
            painter.setFont(font)
            painter.drawText(star_rect, "★")
        
        painter.restore()
    
    def sizeHint(self, option, index):
        """返回项的大小"""
        return QSize(option.rect.width(), 80)


class HistoryListWidget(QWidget):
    """历史列表组件"""
    
    # 信号定义
    item_selected = pyqtSignal(ScreenshotMetadata)  # 选中项
    item_double_clicked = pyqtSignal(ScreenshotMetadata)  # 双击项
    item_favorite_toggled = pyqtSignal(int, bool)  # 收藏切换（ID，新状态）
    item_deleted = pyqtSignal(int)  # 删除项（ID）
    search_text_changed = pyqtSignal(str)  # 搜索文本变化
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._screenshots: List[ScreenshotMetadata] = []
        self._current_filter: str = ""
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        search_frame = QFrame()
        search_frame.setStyleSheet("background-color: #3d3d3d; border-bottom: 1px solid #555;")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(10, 10, 10, 10)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索标题、标签、备注...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                background: #4d4d4d;
                color: #ddd;
            }
            QLineEdit::placeholder {
                color: #888;
            }
        """)
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_edit)
        
        self.clear_btn = QPushButton("×")
        self.clear_btn.setFixedSize(24, 24)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #888;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #ddd;
            }
        """)
        self.clear_btn.clicked.connect(self._clear_search)
        self.clear_btn.hide()
        search_layout.addWidget(self.clear_btn)
        
        layout.addWidget(search_frame)
        
        self.list_widget = QListWidget()
        self.list_widget.setItemDelegate(ScreenshotItemDelegate(self.list_widget))
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #2d2d2d;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #3d3d3d;
            }
        """)
        
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.customContextMenuRequested.connect(self._on_context_menu)
        
        layout.addWidget(self.list_widget)
        
        self.status_label = QLabel("共 0 张截图")
        self.status_label.setStyleSheet("background-color: #2d2d2d; color: #888; padding: 5px;")
        layout.addWidget(self.status_label)
        
    def set_screenshots(self, screenshots: List[ScreenshotMetadata]):
        """
        设置截图列表
        
        Args:
            screenshots: 截图元数据列表
        """
        self._screenshots = screenshots
        self._refresh_list()
        
    def add_screenshot(self, screenshot: ScreenshotMetadata):
        """
        添加截图到列表
        
        Args:
            screenshot: 截图元数据
        """
        self._screenshots.insert(0, screenshot)
        self._refresh_list()
        
    def remove_screenshot(self, screenshot_id: int):
        """
        从列表移除截图
        
        Args:
            screenshot_id: 截图ID
        """
        self._screenshots = [s for s in self._screenshots if s.id != screenshot_id]
        self._refresh_list()
        
    def update_screenshot(self, screenshot: ScreenshotMetadata):
        """
        更新截图信息
        
        Args:
            screenshot: 截图元数据
        """
        for i, s in enumerate(self._screenshots):
            if s.id == screenshot.id:
                self._screenshots[i] = screenshot
                self._refresh_list()
                break
                
    def _refresh_list(self):
        """刷新列表显示"""
        self.list_widget.clear()
        
        filtered = self._filter_screenshots()
        
        for screenshot in filtered:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, screenshot)
            item.setSizeHint(QSize(self.list_widget.width() - 20, 80))
            self.list_widget.addItem(item)
        
        self._update_status()
        
    def _filter_screenshots(self) -> List[ScreenshotMetadata]:
        """过滤截图列表"""
        if not self._current_filter:
            return self._screenshots
        
        keyword = self._current_filter.lower()
        filtered = []
        
        for screenshot in self._screenshots:
            # 高亮匹配
            if (keyword in screenshot.title.lower() or
                keyword in screenshot.tags.lower() or
                keyword in screenshot.notes.lower()):
                filtered.append(screenshot)
                
        return filtered
    
    def _update_status(self):
        """更新状态栏"""
        total = len(self._screenshots)
        filtered = len(self._filter_screenshots())
        
        if self._current_filter:
            self.status_label.setText(f"显示 {filtered} / 共 {total} 张截图")
        else:
            self.status_label.setText(f"共 {total} 张截图")
    
    def _on_search_text_changed(self, text: str):
        """搜索文本变化"""
        self._current_filter = text.strip()
        self.clear_btn.setVisible(bool(self._current_filter))
        self._refresh_list()
        self.search_text_changed.emit(self._current_filter)
        
    def _clear_search(self):
        """清除搜索"""
        self.search_edit.clear()
        
    def _on_item_clicked(self, item: QListWidgetItem):
        """项被点击"""
        metadata = item.data(Qt.ItemDataRole.UserRole)
        if metadata:
            self.item_selected.emit(metadata)
            
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """项被双击"""
        metadata = item.data(Qt.ItemDataRole.UserRole)
        if metadata:
            self.item_double_clicked.emit(metadata)
            
    def _on_context_menu(self, position):
        """显示右键菜单"""
        item = self.list_widget.itemAt(position)
        if not item:
            return
            
        metadata = item.data(Qt.ItemDataRole.UserRole)
        if not metadata:
            return
        
        menu = QMenu(self)
        
        # 查看
        view_action = menu.addAction("查看")
        view_action.triggered.connect(lambda: self.item_double_clicked.emit(metadata))
        
        menu.addSeparator()
        
        # 收藏/取消收藏
        if metadata.is_favorite:
            fav_action = menu.addAction("取消收藏")
        else:
            fav_action = menu.addAction("收藏")
        fav_action.triggered.connect(lambda: self.item_favorite_toggled.emit(
            metadata.id, not metadata.is_favorite))
        
        menu.addSeparator()
        
        # 删除
        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(lambda: self.item_deleted.emit(metadata.id))
        
        menu.exec(self.list_widget.mapToGlobal(position))
        
    def select_screenshot(self, screenshot_id: int):
        """
        选中指定截图
        
        Args:
            screenshot_id: 截图ID
        """
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            metadata = item.data(Qt.ItemDataRole.UserRole)
            if metadata and metadata.id == screenshot_id:
                self.list_widget.setCurrentItem(item)
                break
                
    def get_selected_screenshot(self) -> Optional[ScreenshotMetadata]:
        """
        获取当前选中的截图
        
        Returns:
            选中的截图元数据，没有则返回None
        """
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def clear(self):
        """清空列表"""
        self._screenshots.clear()
        self.list_widget.clear()
        self._update_status()
