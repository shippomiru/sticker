/**
 * 数据同步工具
 * 
 * 此文件用于在开发过程中从 api/data 目录同步数据到前端项目
 * 可以在构建脚本中使用
 */

// 需要安装 Node.js 类型定义
// npm i --save-dev @types/node
import * as fs from 'fs';
import * as path from 'path';

/**
 * 同步API数据到前端项目
 * @param {string} sourceDir - API数据源目录
 * @param {string} targetDir - 前端目标目录
 * @returns {boolean} - 是否成功
 */
export async function syncDataFromAPI(
  sourceDir: string = '../../api/data',
  targetDir: string = '../src/data'
): Promise<boolean> {
  try {
    // 确保目标目录存在
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
      console.log(`创建目录: ${targetDir}`);
    }

    // 读取源目录中的images.json
    const sourcePath = path.resolve(sourceDir, 'images.json');
    const targetPath = path.resolve(targetDir, 'images.json');
    
    // 检查源文件是否存在
    if (!fs.existsSync(sourcePath)) {
      console.warn(`源数据文件不存在: ${sourcePath}`);
      
      // 检查目标文件是否已经存在
      if (fs.existsSync(targetPath)) {
        console.log(`保留现有的目标文件: ${targetPath}`);
        return true; // 如果目标文件已存在，则跳过同步
      } else {
        console.error(`无法同步数据，源文件和目标文件都不存在`);
        return false;
      }
    }

    // 读取数据
    const data = fs.readFileSync(sourcePath, 'utf-8');

    // 写入目标文件
    fs.writeFileSync(targetPath, data);
    console.log(`数据同步成功: ${sourcePath} -> ${targetPath}`);

    // 检查是否需要更新images.ts
    const tsFilePath = path.resolve(targetDir, 'images.ts');
    if (!fs.existsSync(tsFilePath)) {
      // 如果images.ts不存在，创建一个基本的TypeScript接口文件
      const tsContent = `
import imagesData from './images.json';

// 类型定义
export interface ImageData {
  id: string;
  caption: string;
  description: string;
  tags: string[];
  slug: string;
  author: string;
  title: string;
  original_url: string;
  png_url: string;
  sticker_url: string;
  created_at: string;
}

// 导出实际数据
export const images: ImageData[] = imagesData as ImageData[];

// 兼容原有的mockImages数据结构
export const mockImages = images.map(img => ({
  ...img,
  // 使用/images/目录
  png_url: \`/images/\${img.png_url}\`,
  sticker_url: \`/images/\${img.sticker_url}\`,
}));

export default mockImages;
`;
      fs.writeFileSync(tsFilePath, tsContent);
      console.log(`创建TypeScript接口文件: ${tsFilePath}`);
    }

    return true;
  } catch (error) {
    console.error('数据同步失败:', error);
    return false;
  }
}

// 注意：要使用此脚本，请先安装 @types/node
// 命令：npm i --save-dev @types/node
/**
 * 命令行入口点
 */
if (typeof require !== 'undefined' && require.main === module) {
  syncDataFromAPI()
    .then(success => {
      if (success) {
        console.log('数据同步完成');
      } else {
        console.error('数据同步过程中出现错误');
        process.exit(1);
      }
    })
    .catch(err => {
      console.error('数据同步失败:', err);
      process.exit(1);
    });
} 