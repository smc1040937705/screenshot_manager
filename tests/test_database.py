"""
数据库功能测试
"""

import unittest
import sys
import os
import tempfile
import shutil

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.storage.database import DatabaseManager, StorageManager, ScreenshotMetadata


class TestDatabase(unittest.TestCase):
    """测试数据库功能"""
    
    def setUp(self):
        """每个测试方法初始化"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """每个测试方法清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_screenshot(self):
        """测试添加截图记录"""
        metadata = ScreenshotMetadata(
            filename="test.png",
            title="测试截图",
            tags="测试,截图",
            notes="这是一个测试",
            file_path="/path/to/test.png",
            width=1920,
            height=1080,
            file_size=1024
        )
        
        screenshot_id = self.db.add_screenshot(metadata)
        
        self.assertIsNotNone(screenshot_id)
        self.assertGreater(screenshot_id, 0)
    
    def test_get_screenshot(self):
        """测试获取截图记录"""
        # 添加记录
        metadata = ScreenshotMetadata(
            filename="test.png",
            title="测试截图",
            file_path="/path/to/test.png"
        )
        screenshot_id = self.db.add_screenshot(metadata)
        
        # 获取记录
        retrieved = self.db.get_screenshot(screenshot_id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, screenshot_id)
        self.assertEqual(retrieved.filename, "test.png")
        self.assertEqual(retrieved.title, "测试截图")
    
    def test_update_screenshot(self):
        """测试更新截图记录"""
        # 添加记录
        metadata = ScreenshotMetadata(
            filename="test.png",
            title="原始标题",
            file_path="/path/to/test.png"
        )
        screenshot_id = self.db.add_screenshot(metadata)
        
        # 更新记录
        metadata.id = screenshot_id
        metadata.title = "更新后的标题"
        metadata.tags = "新标签"
        
        success = self.db.update_screenshot(metadata)
        
        self.assertTrue(success)
        
        # 验证更新
        retrieved = self.db.get_screenshot(screenshot_id)
        self.assertEqual(retrieved.title, "更新后的标题")
        self.assertEqual(retrieved.tags, "新标签")
    
    def test_delete_screenshot(self):
        """测试删除截图记录"""
        # 添加记录
        metadata = ScreenshotMetadata(
            filename="test.png",
            title="测试",
            file_path="/path/to/test.png"
        )
        screenshot_id = self.db.add_screenshot(metadata)
        
        # 删除记录
        success = self.db.delete_screenshot(screenshot_id)
        
        self.assertTrue(success)
        
        # 验证删除
        retrieved = self.db.get_screenshot(screenshot_id)
        self.assertIsNone(retrieved)
    
    def test_get_all_screenshots(self):
        """测试获取所有截图记录"""
        # 添加多条记录
        for i in range(5):
            metadata = ScreenshotMetadata(
                filename=f"test{i}.png",
                title=f"测试{i}",
                file_path=f"/path/to/test{i}.png"
            )
            self.db.add_screenshot(metadata)
        
        # 获取所有记录
        screenshots = self.db.get_all_screenshots()
        
        self.assertEqual(len(screenshots), 5)
    
    def test_get_all_screenshots_with_pagination(self):
        """测试分页获取截图记录"""
        # 添加多条记录
        for i in range(10):
            metadata = ScreenshotMetadata(
                filename=f"test{i}.png",
                title=f"测试{i}",
                file_path=f"/path/to/test{i}.png"
            )
            self.db.add_screenshot(metadata)
        
        # 分页获取
        screenshots = self.db.get_all_screenshots(limit=5, offset=0)
        self.assertEqual(len(screenshots), 5)
        
        screenshots = self.db.get_all_screenshots(limit=5, offset=5)
        self.assertEqual(len(screenshots), 5)
    
    def test_toggle_favorite(self):
        """测试切换收藏状态"""
        # 添加记录
        metadata = ScreenshotMetadata(
            filename="test.png",
            title="测试",
            file_path="/path/to/test.png",
            is_favorite=False
        )
        screenshot_id = self.db.add_screenshot(metadata)
        
        # 切换收藏
        new_status = self.db.toggle_favorite(screenshot_id)
        
        self.assertTrue(new_status)
        
        # 验证
        retrieved = self.db.get_screenshot(screenshot_id)
        self.assertTrue(retrieved.is_favorite)
        
        # 再次切换
        new_status = self.db.toggle_favorite(screenshot_id)
        self.assertFalse(new_status)
    
    def test_get_favorites(self):
        """测试获取收藏的截图"""
        # 添加记录
        for i in range(5):
            metadata = ScreenshotMetadata(
                filename=f"test{i}.png",
                title=f"测试{i}",
                file_path=f"/path/to/test{i}.png",
                is_favorite=(i % 2 == 0)  # 偶数索引为收藏
            )
            screenshot_id = self.db.add_screenshot(metadata)
            if i % 2 != 0:
                self.db.toggle_favorite(screenshot_id)
        
        # 获取收藏的截图
        favorites = self.db.get_favorites()
        
        self.assertGreater(len(favorites), 0)
        for fav in favorites:
            self.assertTrue(fav.is_favorite)
    
    def test_search_screenshots(self):
        """测试搜索截图"""
        # 添加记录
        metadata1 = ScreenshotMetadata(
            filename="test1.png",
            title="登录页面",
            tags="登录,用户",
            notes="这是登录页面截图",
            file_path="/path/to/test1.png"
        )
        metadata2 = ScreenshotMetadata(
            filename="test2.png",
            title="首页",
            tags="首页,导航",
            notes="这是首页截图",
            file_path="/path/to/test2.png"
        )
        self.db.add_screenshot(metadata1)
        self.db.add_screenshot(metadata2)
        
        # 搜索
        results = self.db.search_screenshots("登录")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "登录页面")
        
        # 搜索标签
        results = self.db.search_screenshots("导航")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "首页")
    
    def test_get_screenshots_by_tag(self):
        """测试按标签获取截图"""
        # 添加记录
        metadata1 = ScreenshotMetadata(
            filename="test1.png",
            title="测试1",
            tags="工作,重要",
            file_path="/path/to/test1.png"
        )
        metadata2 = ScreenshotMetadata(
            filename="test2.png",
            title="测试2",
            tags="个人,生活",
            file_path="/path/to/test2.png"
        )
        self.db.add_screenshot(metadata1)
        self.db.add_screenshot(metadata2)
        
        # 按标签获取
        results = self.db.get_screenshots_by_tag("工作")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "测试1")
    
    def test_get_all_tags(self):
        """测试获取所有标签"""
        # 添加记录
        metadata1 = ScreenshotMetadata(
            filename="test1.png",
            title="测试1",
            tags="标签1, 标签2, 标签3",
            file_path="/path/to/test1.png"
        )
        metadata2 = ScreenshotMetadata(
            filename="test2.png",
            title="测试2",
            tags="标签2, 标签4",
            file_path="/path/to/test2.png"
        )
        self.db.add_screenshot(metadata1)
        self.db.add_screenshot(metadata2)
        
        # 获取所有标签
        tags = self.db.get_all_tags()
        
        self.assertEqual(len(tags), 4)
        self.assertIn("标签1", tags)
        self.assertIn("标签2", tags)
        self.assertIn("标签3", tags)
        self.assertIn("标签4", tags)
    
    def test_update_annotation_data(self):
        """测试更新标注数据"""
        # 添加记录
        metadata = ScreenshotMetadata(
            filename="test.png",
            title="测试",
            file_path="/path/to/test.png"
        )
        screenshot_id = self.db.add_screenshot(metadata)
        
        # 更新标注数据
        annotation_data = '[{"type": "RECTANGLE", "rect": [0, 0, 100, 100]}]'
        success = self.db.update_annotation_data(screenshot_id, annotation_data)
        
        self.assertTrue(success)
        
        # 验证
        retrieved = self.db.get_screenshot(screenshot_id)
        self.assertEqual(retrieved.annotation_data, annotation_data)
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        # 添加记录
        for i in range(5):
            metadata = ScreenshotMetadata(
                filename=f"test{i}.png",
                title=f"测试{i}",
                file_path=f"/path/to/test{i}.png",
                file_size=1024 * (i + 1),
                is_favorite=(i == 0)
            )
            self.db.add_screenshot(metadata)
        
        # 获取统计
        stats = self.db.get_statistics()
        
        self.assertEqual(stats["total_count"], 5)
        self.assertEqual(stats["favorite_count"], 1)
        self.assertEqual(stats["total_size"], 1024 + 2048 + 3072 + 4096 + 5120)


class TestStorageManager(unittest.TestCase):
    """测试存储管理器"""
    
    def setUp(self):
        """每个测试方法初始化"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = StorageManager(self.temp_dir)
    
    def tearDown(self):
        """每个测试方法清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_screenshot(self):
        """测试保存截图"""
        # 创建测试图片数据
        image_data = b"fake_image_data"
        filename = "test.png"
        
        metadata = ScreenshotMetadata(
            title="测试截图",
            width=1920,
            height=1080
        )
        
        # 保存
        result = self.storage.save_screenshot(image_data, filename, metadata)
        
        self.assertIsNotNone(result.id)
        self.assertEqual(result.filename, filename)
        self.assertEqual(result.file_size, len(image_data))
        self.assertTrue(os.path.exists(result.file_path))
    
    def test_delete_screenshot(self):
        """测试删除截图"""
        # 先保存
        image_data = b"fake_image_data"
        metadata = ScreenshotMetadata(title="测试")
        result = self.storage.save_screenshot(image_data, "test.png", metadata)
        
        file_path = result.file_path
        
        # 删除
        success = self.storage.delete_screenshot(result.id)
        
        self.assertTrue(success)
        self.assertFalse(os.path.exists(file_path))
    
    def test_get_image_path(self):
        """测试获取图片路径"""
        # 保存
        image_data = b"fake_image_data"
        metadata = ScreenshotMetadata(title="测试")
        result = self.storage.save_screenshot(image_data, "test.png", metadata)
        
        # 获取路径
        path = self.storage.get_image_path(result.id)
        
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))
    
    def test_get_storage_info(self):
        """测试获取存储信息"""
        # 保存一些数据
        for i in range(3):
            image_data = b"x" * (1024 * (i + 1))
            metadata = ScreenshotMetadata(title=f"测试{i}")
            self.storage.save_screenshot(image_data, f"test{i}.png", metadata)
        
        # 获取信息
        info = self.storage.get_storage_info()
        
        self.assertEqual(info["total_count"], 3)
        self.assertEqual(info["base_path"], self.temp_dir)
        self.assertIn("images_path", info)
        self.assertIn("db_path", info)


if __name__ == '__main__':
    unittest.main()
