# Free-PNG 自动化图片资源网站

## 项目目标

构建一个**自动化图片资源网站**，提供两种高附加值的图片资源：
1. 从 Unsplash 自动抓取图片；
2. 使用本地模型处理后生成两种格式：
   - 去背景的透明 PNG（抠图）；
   - 去背景 + 添加白边的贴纸风格 PNG；
3. 同时自动为每张图片生成英文描述和关键词标签，方便用户分类浏览、搜索和 SEO 优化。

目标用户是需要素材的内容创作者、YouTube 视频制作者、设计师、PPT 制作用户等。网站主打「实用 + 高质 + 免费」。

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
├── batch_manager.py   # 批次管理工具
├── process_images.py  # 图像处理主脚本
├── metadata/          # 批次和处理记录
├── project/           # 前端应用（React + TypeScript）
│   ├── public/        # 静态资源
│   │   └── images/    # 处理后的PNG图片
│   └── src/           # 源代码
│       ├── components/# React组件
│       ├── data/      # 前端数据（与api/data同步）
│       └── utils/     # 工具函数
│
├── processed-images/  # 处理后的图片（带白边和透明背景）
│   └── YYYYMMDD/      # 按日期组织的批次目录
├── unsplash-images/   # 原始图片存储
│   └── YYYYMMDD/      # 按日期组织的批次目录
├── temp-results/      # 处理过程中的临时文件
│   └── YYYYMMDD/      # 按日期组织的批次目录
└── test/              # 测试代码和临时脚本
```

## 技术架构设计

### 内容来源
- 使用 **Unsplash API**（遵循其许可证，可用于免费商用）自动获取高清图片。

### 图片处理流程（全部本地运行 + GitHub Actions 自动化）

| 步骤         | 工具 / 模型              | 说明 | 实现状态 |
|--------------|---------------------------|------|-------|
| 抠图         | [`rembg`（基于 U²-Net）](https://github.com/danielgatis/rembg) | 去背景，生成透明 PNG | ✅ 已实现 |
| 智能裁剪     | Python + NumPy           | 自动检测主体，居中裁剪并保持适当比例 | ✅ 已实现 |
| 添加白边     | Python + `Pillow`         | 抠图后自动加白边，生成贴纸风格 | ✅ 已实现 |
| 自动打标签   | [`CLIP` 模型](https://github.com/openai/CLIP) | 提取关键词用于搜索 / SEO | ✅ 已实现 |
| 自动生成描述 | [`BLIP`](https://github.com/salesforce/BLIP) 模型 | 自动写出类似 "a cat jumping on the bed" 的英文句子 | ✅ 已实现 |
| 原始图片匹配 | Python 正则表达式         | 基于 Unsplash ID 精确匹配原始图片 | ✅ 已实现 |

处理过程计划由 GitHub Actions 定时触发（例如每日更新），无需人工干预，实现纯自动化运行。

### 前端架构

- **框架**：`Vite` + `React` + `Tailwind CSS` ✅ 已实现
- **部署平台**：`Cloudflare Pages`（静态站点，加载快，免费流量大）❓ 待实现
- **图片 CDN**：`Cloudflare R2` 作为图床，配合 Pages 低延迟访问 ❓ 待实现
- **功能**：
  - 分类浏览（基于自动生成的标签）✅ 已实现
  - 搜索功能（关键词搜索）✅ 已实现
  - 下载功能（透明 / 贴纸图分别可下载）✅ 已实现
  - 多语言支持（中英文界面切换）✅ 已实现
  - 深色背景呈现（增强透明图片可视性）✅ 已实现
  - 后续可考虑 SEO 自动优化（基于图像描述）❓ 待实现

### 数据存储

- 当前：使用本地JSON文件存储 ✅ 已实现
- 计划：使用 `Supabase`（PostgreSQL + RESTful API + 免费额度大）存储 ❓ 待实现
  ```json
  {
    id: "uuid",
    original_url: "https://unsplash.com/...",
    png_url: "https://cdn.cloudflare.r2/...",
    sticker_url: "...",
    tags: ["cat", "funny", "meme"],
    caption: "a funny cat jumping on the bed",
    created_at: "2025-04-11T12:00:00Z"
  }
  ```

### 图片分类系统

采用预定义标签集进行分类，包括：
- car（汽车）
- christmas（圣诞）
- flower（花卉）
- dog（狗）
- cat（猫）
- pumpkin（南瓜）
- airplane（飞机）
- birthday（生日）
- baby（婴儿）
- camera（相机）
- crown（皇冠）
- others（其他）

分类系统采用多层匹配逻辑：
1. 直接匹配描述中的关键词
2. 同义词扩展匹配
3. 主体名词提取及匹配
4. 语义规则推断
5. 无法匹配时归类为"others"

### 特别强调
全部处理流程使用**本地开源模型 + GitHub Actions 自动执行**，完全**无需调用付费 API**，可大规模扩展。

## 主要功能

1. **图片处理自动化**：
   - 从JPG图片中提取主体，生成透明背景PNG
   - 创建带白色边框的PNG图片变体
   - 智能裁剪，确保主体居中

   批次处理支持：
   ```bash
   # 创建新批次
   python3 batch_manager.py create [--date YYYYMMDD]

   # 导入图片到批次
   python3 batch_manager.py import SOURCE_DIR --batch YYYYMMDD

   # 处理批次图片
   python3 process_images.py --batch YYYYMMDD

   # 查看批次状态
   python3 batch_manager.py status YYYYMMDD
   ```

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
   pip install opencv-python pillow numpy python-slugify rembg
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

## 项目进展状况

已完成的部分：
- ✅ 完整的图片处理流程（抠图、添加白边、裁剪、标签生成、描述生成）
- ✅ 基本的前端功能（浏览、搜索、下载、双语支持）
- ✅ 本地数据存储（JSON文件）
- ✅ 数据同步机制
- ✅ SEO优化（robots.txt、sitemap.xml）
- ✅ Cloudflare R2图片CDN集成（上传脚本与公共访问设置）
- ✅ Cloudflare Pages部署配置

待完成或确认的部分：
- ❓ Supabase数据库集成
- ❓ GitHub Actions自动化工作流
- ❓ 自定义域名配置
- ❓ 监控与分析系统集成

## 部署信息

当前部署状态：
- 网站已部署到Cloudflare Pages：https://sticker.pages.dev
- 图片资源存储在Cloudflare R2 CDN
- 使用集中式JSON数据管理，数据文件也纳入版本控制

访问[DEPLOYMENT.md](./DEPLOYMENT.md)文件获取完整的部署指南。

## 许可协议

本项目中使用的图片来自Unsplash，遵循Unsplash许可协议。项目代码使用MIT许可协议。 