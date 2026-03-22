# 截图标注与历史管理器

基于 Python + PyQt6 构建的本地截图标注与历史管理工具。

## 功能特性

### 截图功能
- **全屏截图** (F1) - 截取整个屏幕
- **区域截图** (F2) - 拖拽选择区域进行截图
- **窗口截图** - 截取指定窗口

### 标注工具
- **矩形** - 绘制矩形框，支持填充
- **箭头** - 绘制指向箭头
- **文字** - 添加文字标注，支持背景色
- **马赛克** - 对敏感区域打码

### 历史管理
- **截图列表** - 左侧显示所有截图历史
- **收藏功能** - 收藏重要截图 (Ctrl+D)
- **标签分类** - 为截图添加标签
- **搜索功能** - 按标题/标签/备注搜索
- **删除功能** - 删除不需要的截图 (Delete)

### 导出功能
- **复制到剪贴板** (Ctrl+C)
- **另存为 PNG**
- **导出为 PDF**

### 系统托盘
- **托盘图标** - 最小化到托盘
- **快捷菜单** - 右键菜单快速操作
- **气泡通知** - 操作完成提示

## 项目结构

```
.
├── main.py                 # 程序入口
├── requirements.txt        # 依赖列表
├── src/
│   ├── app/               # 应用程序模块
│   │   ├── __init__.py
│   │   └── main_window.py # 主窗口
│   ├── components/        # UI 组件
│   │   ├── __init__.py
│   │   ├── history_list.py    # 历史列表组件
│   │   └── image_editor.py    # 图片编辑器组件
│   ├── core/              # 核心功能
│   │   ├── __init__.py
│   │   ├── screenshot.py      # 截图功能
│   │   └── annotation.py      # 标注功能
│   ├── storage/           # 存储模块
│   │   ├── __init__.py
│   │   └── database.py        # SQLite 数据库
│   └── system/            # 系统功能
│       ├── __init__.py
│       ├── tray.py            # 系统托盘
│       ├── clipboard.py       # 剪贴板
│       └── export.py          # 导出功能
└── tests/                 # 测试用例
    ├── __init__.py
    ├── test_screenshot.py     # 截图测试
    ├── test_annotation.py     # 标注测试
    ├── test_database.py       # 数据库测试
    └── test_export.py         # 导出测试
```

## 安装运行

### 环境要求
- Python 3.8+
- PyQt6

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行程序
```bash
python main.py
```

### 运行测试
```bash
python -m unittest discover tests
```

## 使用说明

### 快捷键
| 快捷键 | 功能 |
|--------|------|
| F1 | 全屏截图 |
| F2 | 区域截图 |
| Ctrl+S | 保存当前截图 |
| Ctrl+Shift+S | 另存为 |
| Ctrl+C | 复制到剪贴板 |
| Ctrl+D | 收藏/取消收藏 |
| Delete | 删除当前截图 |
| F5 | 刷新列表 |

### 数据存储
- 截图图片: `~/.screenshot_manager/images/`
- 数据库: `~/.screenshot_manager/screenshots.db`
- 窗口设置: 系统注册表/QSettings

## 技术要点

1. **截图**: 使用 `QScreen.grabWindow()` 获取屏幕图像
2. **标注**: 基于 `QPainter` 实现各种绘制工具
3. **存储**: 图片文件 + SQLite 元数据
4. **系统 API**: 剪贴板、托盘、通知
5. **持久化**: `QSettings` 保存窗口状态

## 许可证

MIT License
