# Free-PNG 自动化图片资源网站

一个专注于提供免费、高质量透明背景PNG图片的资源网站，具有自动化处理图片和元数据生成功能。

## 项目结构

```
free-png/
├── api/               # API和自动化处理部分
│   ├── data/          # 中央数据存储（元数据JSON文件）
│   ├── photos/        # 原始图片存储备份
│   └── processors/    # 图片处理脚本
│       ├── metadata_generator.py           # 元数据生成器
│       ├── process_with_improved_order.py  # 图片处理主脚本
│       ├── crop_all_images_improved.py     # 批量裁剪工具
│       └── test_smooth_no_gap_outline.py   # 边框平滑处理工具
│
├── project/           # 前端应用（React + TypeScript）
│   ├── public/        # 静态资源
│   │   └── images/    # 处理后的PNG图片
│   └── src/           # 源代码
│       ├── components/# React组件
│       ├── data/      # 前端数据（与api/data同步）
│       └── utils/     # 工具函数
│
├── results-photos-cropped/  # 处理后的图片（带白边和透明背景）
├── unsplash-images/         # 原始图片存储
└── test/                    # 测试代码和临时脚本
```

## 主要功能

1. **图片处理自动化**：
   - 从JPG图片中提取主体，生成透明背景PNG
   - 创建带白色边框的PNG图片变体
   - 智能裁剪，确保主体居中

2. **元数据生成**：
   - 自动识别图片主题和内容
   - 生成适合前端使用的JSON元数据
   - 支持按标签和关键词检索

3. **前端展示**：
   - 响应式设计，适配各种设备
   - 支持中英双语
   - 下载功能和图片预览

## 数据管理

本项目使用集中式数据管理方式：

1. 所有元数据统一存储在 `api/data/images.json`
2. 前端应用使用 `project/src/data/images.json` 作为数据源（通过同步脚本保持一致）
3. 图片处理脚本自动更新两处数据

### 数据同步

使用以下命令将API数据同步到前端：

```bash
cd project
npm run sync-data
```

## 开发指南

### 环境设置

1. **安装Python依赖**：
   ```bash
   pip install opencv-python pillow numpy python-slugify
   ```

2. **安装前端依赖**：
   ```bash
   cd project
   npm install
   ```

### 图片处理流程

1. 将原始JPG图片放入 `unsplash-images/` 目录
2. 运行处理脚本生成透明PNG：
   ```bash
   cd api/processors
   python process_with_improved_order.py
   ```
3. 运行元数据生成器：
   ```bash
   python metadata_generator.py
   ```
4. 同步数据到前端：
   ```bash
   cd ../../project
   npm run sync-data
   ```

### 启动前端开发服务器

```bash
cd project
npm run dev
```

## 许可协议

本项目中使用的图片来自Unsplash，遵循Unsplash许可协议。项目代码使用MIT许可协议。 