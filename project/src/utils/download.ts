/**
 * 下载工具函数
 * 提供多种方法下载图片，确保在不同浏览器和环境下都能正常工作
 */

import { triggerUnsplashDownload } from './unsplash';

/**
 * 使用fetch API下载图片
 * 这种方法可以绕过某些CORS限制
 */
export async function downloadImageWithFetch(url: string, filename: string): Promise<boolean> {
  try {
    console.log('使用fetch方法下载图片:', url);
    const response = await fetch(url, {
      mode: 'cors', // 尝试跨域请求
      cache: 'no-cache', // 不使用缓存
    });
    
    if (!response.ok) {
      console.error('Fetch失败，状态:', response.status);
      return false;
    }
    
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
    return true;
  } catch (error) {
    console.error('使用fetch下载失败:', error);
    return false;
  }
}

/**
 * 使用直接链接方法下载图片
 * 简单但可能受CORS限制
 */
export function downloadImageWithLink(url: string, filename: string): boolean {
  try {
    console.log('使用链接方法下载图片:', url);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    return true;
  } catch (error) {
    console.error('使用链接下载失败:', error);
    return false;
  }
}

/**
 * 使用window.open方法下载图片
 * 作为后备方案
 */
export function downloadImageWithWindow(url: string): boolean {
  try {
    console.log('使用window.open方法下载图片:', url);
    window.open(url, '_blank');
    return true;
  } catch (error) {
    console.error('使用window.open下载失败:', error);
    return false;
  }
}

/**
 * 为R2 CDN URL添加处理
 * 针对Cloudflare R2特别优化
 */
export function processR2Url(url: string): string {
  // 检查是否为R2 URL
  if (url.includes('.r2.dev') || url.includes('r2.cloudflarestorage.com')) {
    // 如果是R2 URL，我们可以尝试通过类似于这样的方式来解决CORS问题：
    // 1. 使用Cloudflare Worker作为代理（如果已配置）
    // 2. 确保URL使用HTTPS协议
    
    // 确保使用HTTPS协议
    if (url.startsWith('http://')) {
      url = url.replace('http://', 'https://');
    }
    
    // 这里可以添加自定义代理前缀，如果您有设置Cloudflare Worker代理的话
    // url = `https://your-proxy-worker.your-domain.workers.dev/?url=${encodeURIComponent(url)}`;
    
    console.log('处理R2 URL:', url);
  }
  
  return url;
}

/**
 * 使用图片的blob方式下载，绕过R2限制
 */
export async function downloadImageViaImgElement(url: string, filename: string): Promise<boolean> {
  return new Promise(resolve => {
    try {
      console.log('使用Image元素方法下载图片:', url);
      
      // 创建一个图片元素加载图片
      const img = new Image();
      img.crossOrigin = 'anonymous'; // 尝试允许跨域
      img.onload = () => {
        // 创建canvas
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        
        // 将图像绘制到canvas
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          console.error('无法获取canvas上下文');
          resolve(false);
          return;
        }
        
        ctx.drawImage(img, 0, 0);
        
        // 从canvas获取数据URL并下载
        try {
          // 检查是否为PNG图片
          const mimeType = url.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg';
          canvas.toBlob((blob) => {
            if (!blob) {
              console.error('无法创建blob');
              resolve(false);
              return;
            }
            
            const blobUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(blobUrl);
            resolve(true);
          }, mimeType);
        } catch (err) {
          console.error('Canvas转换失败:', err);
          resolve(false);
        }
      };
      
      img.onerror = () => {
        console.error('图片加载失败:', url);
        resolve(false);
      };
      
      // 设置图片源
      img.src = url;
      
      // 如果图片已经在缓存中，可能不会触发onload
      if (img.complete) {
        img.onload(new Event('load'));
      }
      
    } catch (error) {
      console.error('使用Image元素下载失败:', error);
      resolve(false);
    }
  });
}

/**
 * 综合下载方法，按顺序尝试不同的下载方式
 * 
 * @param url 图片URL
 * @param filename 下载后的文件名
 * @returns 是否成功下载
 */
export async function downloadImage(url: string, filename: string): Promise<boolean> {
  // 处理R2等特殊URL
  url = processR2Url(url);
  
  // 首先尝试使用链接方法（最直接的方法）
  const linkResult = downloadImageWithLink(url, filename);
  if (linkResult) return true;
  
  // 如果链接方法失败，尝试fetch方法
  const fetchResult = await downloadImageWithFetch(url, filename);
  if (fetchResult) return true;
  
  // 如果fetch方法失败，尝试Image元素方法
  const imgResult = await downloadImageViaImgElement(url, filename);
  if (imgResult) return true;
  
  // 最后使用window.open作为后备方案
  console.warn('所有下载方法都失败，使用window.open作为最后手段');
  return downloadImageWithWindow(url);
} 