/**
 * Sitemap生成工具
 * 
 * 此文件用于在构建过程中自动生成sitemap.xml文件，
 * 基于images.json中的数据生成完整的站点地图。
 */

// 需要安装 Node.js 类型定义
// npm i --save-dev @types/node
import * as fs from 'fs';
import * as path from 'path';

interface ImageData {
  id: string;
  caption: string;
  description: string;
  tags: string[];
  slug: string;
  author: string;
  original_url: string;
  png_url: string;
  sticker_url: string;
  created_at: string;
}

/**
 * 从图片数据生成完整的sitemap.xml文件
 * @param {string} domain - 网站域名
 * @param {string} sourceDataPath - 图片数据JSON文件路径
 * @param {string} outputPath - 输出sitemap.xml文件路径
 * @returns {boolean} - 是否成功生成
 */
export async function generateSitemap(
  domain: string = process.env.VITE_SITE_URL || 'https://free-png.example.com',
  sourceDataPath: string = '../src/data/images.json',
  outputPath: string = '../public/sitemap.xml'
): Promise<boolean> {
  try {
    // 确保移除末尾的斜杠
    if (domain.endsWith('/')) {
      domain = domain.slice(0, -1);
    }

    console.log(`使用域名 ${domain} 生成站点地图`);

    // 读取图片数据
    const jsonPath = path.resolve(sourceDataPath);
    if (!fs.existsSync(jsonPath)) {
      console.error(`源数据文件不存在: ${jsonPath}`);
      return false;
    }

    const rawData = fs.readFileSync(jsonPath, 'utf-8');
    const images: ImageData[] = JSON.parse(rawData);
    console.log(`加载了 ${images.length} 个图片数据项`);

    // 获取当前日期，格式为YYYY-MM-DD
    const today = new Date().toISOString().split('T')[0];

    // 构建sitemap XML
    let sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <!-- 主页 -->
  <url>
    <loc>${domain}/</loc>
    <lastmod>${today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  
  <!-- 关于页面 -->
  <url>
    <loc>${domain}/about</loc>
    <lastmod>${today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  
  <!-- 图片详情页面 - 由系统自动生成 -->\n`;

    // 添加每个图片的详情页
    images.forEach(image => {
      sitemap += `  <url>
    <loc>${domain}/${image.slug}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>\n`;
    });

    // 获取所有唯一标签
    const allTags = Array.from(new Set(images.flatMap(img => img.tags)));
    
    // 添加标签筛选页面
    sitemap += `\n  <!-- 类别标签页 -->\n`;
    allTags.forEach(tag => {
      sitemap += `  <url>
    <loc>${domain}/?tag=${tag}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>\n`;
    });

    // 关闭urlset标签
    sitemap += `</urlset>`;

    // 写入文件
    const outputFilePath = path.resolve(outputPath);
    fs.writeFileSync(outputFilePath, sitemap);
    console.log(`站点地图已生成: ${outputFilePath}`);
    console.log(`收录了 ${images.length} 个图片页面和 ${allTags.length} 个标签页面`);

    return true;
  } catch (error) {
    console.error('生成站点地图失败:', error);
    return false;
  }
}

/**
 * 命令行入口点
 */
if (typeof require !== 'undefined' && require.main === module) {
  generateSitemap()
    .then(success => {
      if (success) {
        console.log('站点地图生成完成');
      } else {
        console.error('站点地图生成过程中出现错误');
        process.exit(1);
      }
    })
    .catch(err => {
      console.error('站点地图生成失败:', err);
      process.exit(1);
    });
} 