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
  png_url: `/images/${img.png_url}`,
  sticker_url: `/images/${img.sticker_url}`,
}));

export default mockImages;