import imagesData from './images.json';

// 类型定义
export interface ImageData {
  id: string;
  caption: string;
  description: string;
  tags: string[];
  main_noun?: string; // 从元数据中提取的主体名词，用于SEO优化
  slug: string;
  author: string;
  title: string;
  original_url: string;
  png_url: string;
  sticker_url: string;
  created_at: string;
}

// R2 CDN基础URL，从环境变量中获取
const R2_CDN_URL = import.meta.env.VITE_R2_CDN_URL || '';

// 导出实际数据
export const images: ImageData[] = imagesData as ImageData[];

// 处理图片URL的函数
const getImageUrl = (url: string): string => {
  // 如果已经是完整URL，则直接返回
  if (url.startsWith('http')) return url;
  
  // 如果已经包含/images/前缀，则去除它（因为会和R2路径重复）
  const cleanUrl = url.startsWith('/images/') ? url.substring(8) : url;
  
  // 如果有R2 CDN URL，则使用它，否则使用本地路径
  return R2_CDN_URL ? 
    `${R2_CDN_URL}/${cleanUrl}` : 
    `/images/${cleanUrl}`;
};

// 兼容原有的mockImages数据结构
export const mockImages = images.map(img => ({
  ...img,
  // 使用处理函数获取正确的URL
  png_url: getImageUrl(img.png_url),
  sticker_url: getImageUrl(img.sticker_url),
}));

export default mockImages;