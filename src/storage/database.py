"""
数据库存储模块
管理截图元数据的SQLite存储
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScreenshotMetadata:
    """截图元数据"""
    id: Optional[int] = None
    filename: str = ""  # 图片文件名
    title: str = ""  # 标题
    tags: str = ""  # 标签，逗号分隔
    notes: str = ""  # 备注
    is_favorite: bool = False  # 是否收藏
    annotation_data: str = ""  # 标注数据JSON
    file_path: str = ""  # 图片文件路径
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    width: int = 0
    height: int = 0
    file_size: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "filename": self.filename,
            "title": self.title,
            "tags": self.tags,
            "notes": self.notes,
            "is_favorite": self.is_favorite,
            "annotation_data": self.annotation_data,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "width": self.width,
            "height": self.height,
            "file_size": self.file_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScreenshotMetadata":
        """从字典创建"""
        return cls(
            id=data.get("id"),
            filename=data.get("filename", ""),
            title=data.get("title", ""),
            tags=data.get("tags", ""),
            notes=data.get("notes", ""),
            is_favorite=data.get("is_favorite", False),
            annotation_data=data.get("annotation_data", ""),
            file_path=data.get("file_path", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            width=data.get("width", 0),
            height=data.get("height", 0),
            file_size=data.get("file_size", 0)
        )


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_directory()
        self._init_database()
    
    def _ensure_directory(self):
        """确保数据库目录存在"""
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建截图元数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    title TEXT DEFAULT '',
                    tags TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    is_favorite INTEGER DEFAULT 0,
                    annotation_data TEXT DEFAULT '',
                    file_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    width INTEGER DEFAULT 0,
                    height INTEGER DEFAULT 0,
                    file_size INTEGER DEFAULT 0
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_screenshots_created_at 
                ON screenshots(created_at DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_screenshots_favorite 
                ON screenshots(is_favorite)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_screenshots_title 
                ON screenshots(title)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_screenshots_tags 
                ON screenshots(tags)
            """)
            
            conn.commit()
    
    def add_screenshot(self, metadata: ScreenshotMetadata) -> int:
        """
        添加截图记录
        
        Args:
            metadata: 截图元数据
            
        Returns:
            新记录的ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO screenshots 
                (filename, title, tags, notes, is_favorite, annotation_data, 
                 file_path, width, height, file_size, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.filename,
                metadata.title,
                metadata.tags,
                metadata.notes,
                1 if metadata.is_favorite else 0,
                metadata.annotation_data,
                metadata.file_path,
                metadata.width,
                metadata.height,
                metadata.file_size,
                datetime.now(),
                datetime.now()
            ))
            conn.commit()
            return cursor.lastrowid
    
    def update_screenshot(self, metadata: ScreenshotMetadata) -> bool:
        """
        更新截图记录
        
        Args:
            metadata: 截图元数据
            
        Returns:
            是否成功
        """
        if metadata.id is None:
            return False
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE screenshots SET
                    filename = ?,
                    title = ?,
                    tags = ?,
                    notes = ?,
                    is_favorite = ?,
                    annotation_data = ?,
                    file_path = ?,
                    width = ?,
                    height = ?,
                    file_size = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                metadata.filename,
                metadata.title,
                metadata.tags,
                metadata.notes,
                1 if metadata.is_favorite else 0,
                metadata.annotation_data,
                metadata.file_path,
                metadata.width,
                metadata.height,
                metadata.file_size,
                datetime.now(),
                metadata.id
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_screenshot(self, screenshot_id: int) -> bool:
        """
        删除截图记录
        
        Args:
            screenshot_id: 截图ID
            
        Returns:
            是否成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM screenshots WHERE id = ?", (screenshot_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_screenshot(self, screenshot_id: int) -> Optional[ScreenshotMetadata]:
        """
        获取单个截图记录
        
        Args:
            screenshot_id: 截图ID
            
        Returns:
            截图元数据，不存在返回None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM screenshots WHERE id = ?
            """, (screenshot_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_metadata(row)
            return None
    
    def get_all_screenshots(self, limit: Optional[int] = None, 
                           offset: int = 0) -> List[ScreenshotMetadata]:
        """
        获取所有截图记录
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            截图元数据列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if limit is not None:
                cursor.execute("""
                    SELECT * FROM screenshots 
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM screenshots 
                    ORDER BY created_at DESC
                """)
            
            rows = cursor.fetchall()
            return [self._row_to_metadata(row) for row in rows]
    
    def get_favorites(self) -> List[ScreenshotMetadata]:
        """
        获取收藏的截图
        
        Returns:
            收藏的截图元数据列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM screenshots 
                WHERE is_favorite = 1
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            return [self._row_to_metadata(row) for row in rows]
    
    def search_screenshots(self, keyword: str) -> List[ScreenshotMetadata]:
        """
        搜索截图
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的截图元数据列表
        """
        keyword = f"%{keyword}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM screenshots 
                WHERE title LIKE ? 
                   OR tags LIKE ? 
                   OR notes LIKE ?
                ORDER BY 
                    CASE 
                        WHEN title LIKE ? THEN 1
                        WHEN tags LIKE ? THEN 2
                        ELSE 3
                    END,
                    created_at DESC
            """, (keyword, keyword, keyword, keyword, keyword))
            rows = cursor.fetchall()
            return [self._row_to_metadata(row) for row in rows]
    
    def get_screenshots_by_tag(self, tag: str) -> List[ScreenshotMetadata]:
        """
        按标签获取截图
        
        Args:
            tag: 标签
            
        Returns:
            匹配的截图元数据列表
        """
        tag_pattern = f"%{tag}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM screenshots 
                WHERE tags LIKE ?
                ORDER BY created_at DESC
            """, (tag_pattern,))
            rows = cursor.fetchall()
            return [self._row_to_metadata(row) for row in rows]
    
    def get_all_tags(self) -> List[str]:
        """
        获取所有标签
        
        Returns:
            标签列表（去重）
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tags FROM screenshots WHERE tags != ''")
            rows = cursor.fetchall()
            
            tags = set()
            for row in rows:
                for tag in row["tags"].split(","):
                    tag = tag.strip()
                    if tag:
                        tags.add(tag)
            
            return sorted(list(tags))
    
    def toggle_favorite(self, screenshot_id: int) -> bool:
        """
        切换收藏状态
        
        Args:
            screenshot_id: 截图ID
            
        Returns:
            新的收藏状态
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE screenshots 
                SET is_favorite = NOT is_favorite,
                    updated_at = ?
                WHERE id = ?
            """, (datetime.now(), screenshot_id))
            conn.commit()
            
            # 获取新的状态
            cursor.execute("SELECT is_favorite FROM screenshots WHERE id = ?", 
                         (screenshot_id,))
            row = cursor.fetchone()
            return bool(row["is_favorite"]) if row else False
    
    def update_annotation_data(self, screenshot_id: int, annotation_data: str) -> bool:
        """
        更新标注数据
        
        Args:
            screenshot_id: 截图ID
            annotation_data: 标注数据JSON字符串
            
        Returns:
            是否成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE screenshots 
                SET annotation_data = ?,
                    updated_at = ?
                WHERE id = ?
            """, (annotation_data, datetime.now(), screenshot_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 总数
            cursor.execute("SELECT COUNT(*) as count FROM screenshots")
            total = cursor.fetchone()["count"]
            
            # 收藏数
            cursor.execute("SELECT COUNT(*) as count FROM screenshots WHERE is_favorite = 1")
            favorites = cursor.fetchone()["count"]
            
            # 总文件大小
            cursor.execute("SELECT SUM(file_size) as total_size FROM screenshots")
            total_size = cursor.fetchone()["total_size"] or 0
            
            # 最早和最晚
            cursor.execute("""
                SELECT MIN(created_at) as earliest, MAX(created_at) as latest 
                FROM screenshots
            """)
            row = cursor.fetchone()
            
            return {
                "total_count": total,
                "favorite_count": favorites,
                "total_size": total_size,
                "earliest": row["earliest"],
                "latest": row["latest"]
            }
    
    def _row_to_metadata(self, row: sqlite3.Row) -> ScreenshotMetadata:
        """将数据库行转换为元数据对象"""
        return ScreenshotMetadata(
            id=row["id"],
            filename=row["filename"],
            title=row["title"],
            tags=row["tags"],
            notes=row["notes"],
            is_favorite=bool(row["is_favorite"]),
            annotation_data=row["annotation_data"],
            file_path=row["file_path"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
            width=row["width"],
            height=row["height"],
            file_size=row["file_size"]
        )


class StorageManager:
    """存储管理器 - 统一管理文件和数据库"""
    
    def __init__(self, base_path: str):
        """
        初始化存储管理器
        
        Args:
            base_path: 基础存储路径
        """
        self.base_path = Path(base_path)
        self.images_path = self.base_path / "images"
        self.db_path = self.base_path / "screenshots.db"
        
        # 确保目录存在
        self._ensure_directories()
        
        # 初始化数据库
        self.db = DatabaseManager(str(self.db_path))
    
    def _ensure_directories(self):
        """确保目录存在"""
        self.images_path.mkdir(parents=True, exist_ok=True)
    
    def save_screenshot(self, image_data: bytes, filename: str,
                       metadata: Optional[ScreenshotMetadata] = None) -> ScreenshotMetadata:
        """
        保存截图
        
        Args:
            image_data: 图片数据
            filename: 文件名
            metadata: 元数据（可选）
            
        Returns:
            保存后的元数据
        """
        if metadata is None:
            metadata = ScreenshotMetadata()
        
        # 保存文件
        file_path = self.images_path / filename
        with open(file_path, "wb") as f:
            f.write(image_data)
        
        # 更新元数据
        metadata.filename = filename
        metadata.file_path = str(file_path)
        metadata.file_size = len(image_data)
        
        # 保存到数据库
        if metadata.id is None:
            metadata.id = self.db.add_screenshot(metadata)
        else:
            self.db.update_screenshot(metadata)
        
        return metadata
    
    def delete_screenshot(self, screenshot_id: int) -> bool:
        """
        删除截图
        
        Args:
            screenshot_id: 截图ID
            
        Returns:
            是否成功
        """
        # 获取元数据
        metadata = self.db.get_screenshot(screenshot_id)
        if not metadata:
            return False
        
        # 删除文件
        try:
            if metadata.file_path and os.path.exists(metadata.file_path):
                os.remove(metadata.file_path)
        except OSError:
            pass
        
        # 删除数据库记录
        return self.db.delete_screenshot(screenshot_id)
    
    def get_image_path(self, screenshot_id: int) -> Optional[str]:
        """
        获取图片路径
        
        Args:
            screenshot_id: 截图ID
            
        Returns:
            图片路径，不存在返回None
        """
        metadata = self.db.get_screenshot(screenshot_id)
        if metadata and metadata.file_path and os.path.exists(metadata.file_path):
            return metadata.file_path
        return None
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        获取存储信息
        
        Returns:
            存储信息字典
        """
        stats = self.db.get_statistics()
        
        # 计算目录大小
        total_dir_size = 0
        try:
            for file in self.images_path.iterdir():
                if file.is_file():
                    total_dir_size += file.stat().st_size
        except OSError:
            pass
        
        return {
            **stats,
            "base_path": str(self.base_path),
            "images_path": str(self.images_path),
            "db_path": str(self.db_path),
            "directory_size": total_dir_size
        }
