/**
 * Unsplash API 工具函数
 * 用于处理与 Unsplash API 相关的操作
 */

// Unsplash API 密钥和端点
const UNSPLASH_ACCESS_KEY = 'UNexRajSsADsyMXrFwKf9UJmNryJOohrFXpJoRwqR_8';
const UNSPLASH_API_URL = 'https://api.unsplash.com';

/**
 * 从图片ID中提取Unsplash ID
 * 支持多种格式如: 
 * - author-name-{ID}-unsplash
 * - {ID}-unsplash
 * - 包含ID的其他格式
 */
export function extractUnsplashId(imageId: string): string | null {
  if (!imageId) return null;
  
  // 首先检查是否是纯Unsplash ID (10-13位字母和数字)
  if (/^[a-zA-Z0-9_-]{10,13}$/.test(imageId)) {
    return imageId;
  }
  
  // 如果是JSON对象格式的字符串，尝试解析
  if (imageId.startsWith('{') && imageId.endsWith('}')) {
    try {
      const parsedData = JSON.parse(imageId);
      if (parsedData.unsplash_id) {
        return parsedData.unsplash_id;
      }
    } catch (e) {
      // 解析失败，继续尝试其他方法
    }
  }
  
  // 尝试各种可能的正则模式
  const patterns = [
    // 标准格式: author-name-{ID}-unsplash
    /[-_]([a-zA-Z0-9_-]{10,13})(?:-unsplash|$)/,
    // ID在末尾: something-{ID}
    /-([a-zA-Z0-9_-]{10,13})$/,
    // 在unsplash前面的部分: {ID}-unsplash
    /([a-zA-Z0-9_-]{10,13})-unsplash/,
    // 文件名开头就是ID: {ID}-something
    /^([a-zA-Z0-9_-]{10,13})-/
  ];
  
  for (const pattern of patterns) {
    const match = imageId.match(pattern);
    if (match && match[1]) {
      return match[1];
    }
  }
  
  // 如果所有模式都失败，尝试提取任何看起来像ID的部分
  // 搜索10-13位的字母数字串
  const generalMatch = imageId.match(/([a-zA-Z0-9_-]{10,13})/);
  if (generalMatch && generalMatch[1]) {
    console.log(`使用通用模式匹配提取ID: ${generalMatch[1]}，原ID: ${imageId}`);
    return generalMatch[1];
  }
  
  return null;
}

/**
 * 触发 Unsplash 下载事件
 * 实现 Unsplash API 指南要求的下载事件触发
 * 
 * @param imageId 图片ID (可以是完整的图片ID、Unsplash ID或包含下载链接的对象)
 * @returns 成功返回true，失败返回false
 */
export async function triggerUnsplashDownload(imageId: string | {id?: string, download_location?: string}): Promise<boolean> {
  try {
    console.log('触发 Unsplash 下载事件:', imageId);
    
    // 处理不同类型的输入
    let downloadUrl: string | null = null;
    let unsplashId: string | null = null;
    
    // 如果是对象(包含download_location)，优先使用该链接
    if (typeof imageId === 'object' && imageId !== null) {
      if (imageId.download_location) {
        downloadUrl = imageId.download_location;
        console.log('使用提供的download_location链接');
      } else if (imageId.id) {
        unsplashId = typeof imageId.id === 'string' ? 
                     extractUnsplashId(imageId.id) : 
                     String(imageId.id);
        console.log('从对象中提取ID:', unsplashId);
      }
    } else if (typeof imageId === 'string') {
      // 检查是否直接提供了下载链接
      if (imageId.includes('/photos/') && imageId.includes('/download')) {
        downloadUrl = imageId;
        console.log('使用提供的下载链接');
      } else {
        // 尝试从字符串中提取ID
        unsplashId = extractUnsplashId(imageId);
        console.log('从字符串中提取ID:', unsplashId);
      }
    }
    
    // 如果没有下载链接但有ID，构建下载链接
    if (!downloadUrl && unsplashId) {
      downloadUrl = `${UNSPLASH_API_URL}/photos/${unsplashId}/download?client_id=${UNSPLASH_ACCESS_KEY}`;
      console.log('构建下载链接:', downloadUrl);
    }
    
    // 如果无法获取下载链接，返回失败
    if (!downloadUrl) {
      console.warn('无法构建Unsplash下载链接:', imageId);
      return false;
    }
    
    // 发送请求触发下载事件（异步，不等待响应）
    fetch(downloadUrl, {
      method: 'GET',
      headers: {
        'Accept-Version': 'v1'
      }
    }).then(response => {
      if (response.ok) {
        console.log('成功触发Unsplash下载事件');
      } else {
        console.warn('触发Unsplash下载事件失败:', response.status, response.statusText);
      }
    }).catch(error => {
      console.error('触发Unsplash下载事件发生错误:', error);
    });
    
    // 无论后续请求如何，都返回true以不阻塞下载流程
    return true;
  } catch (error) {
    console.error('触发Unsplash下载事件失败:', error);
    return false;
  }
} 