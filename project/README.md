# Free-PNG 自动化图片资源网站

## 项目目标

构建一个**自动化图片网站**，提供两种高附加值的图片资源：
1. 从 Unsplash 自动抓取图片；
2. 使用本地模型处理后生成两种格式：
   - 去背景的透明 PNG（抠图）；
   - 去背景 + 添加白边的贴纸风格 PNG；
3. 同时自动为每张图片生成英文描述和关键词标签，方便用户分类浏览、搜索和 SEO 优化。

目标用户是需要素材的内容创作者、YouTube 视频制作者、设计师、PPT 制作用户等。网站主打「实用 + 高质 + 免费」。

## 技术架构设计

### 内容来源
- 使用 **Unsplash API**（遵循其许可证，可用于免费商用）自动获取高清图片。

### 图片处理流程（全部本地运行 + GitHub Actions 自动化）

| 步骤         | 工具 / 模型              | 说明 |
|--------------|---------------------------|------|
| 抠图         | [`rembg`（基于 U²-Net）](https://github.com/danielgatis/rembg) | 去背景，生成透明 PNG |
| 添加白边     | Python + `Pillow`         | 抠图后自动加白边，生成贴纸风格 |
| 自动打标签   | [`CLIP` 模型](https://github.com/openai/CLIP) | 提取关键词用于搜索 / SEO |
| 自动生成描述 | [`BLIP`](https://github.com/salesforce/BLIP) 模型 | 自动写出类似 "a cat jumping on the bed" 的英文句子 |

处理过程将由 GitHub Actions 定时触发（例如每日更新），无需人工干预，纯自动化运行。

### 前端架构

- **框架**：`Vite` + `React` + `Tailwind CSS`
- **部署平台**：`Cloudflare Pages`（静态站点，加载快，免费流量大）
- **图片 CDN**：`Cloudflare R2` 作为图床，配合 Pages 低延迟访问
- **功能**：
  - 分类浏览（基于自动生成的标签）
  - 搜索功能（关键词搜索）
  - 下载功能（透明 / 贴纸图分别可下载）
  - 后续可考虑 SEO 自动优化（基于图像描述）

### 数据存储

- 使用 `Supabase`（PostgreSQL + RESTful API + 免费额度大）存储：
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

### 特别强调
全部处理流程使用**本地开源模型 + GitHub Actions 自动执行**，完全**无需调用付费 API**，可大规模扩展。 