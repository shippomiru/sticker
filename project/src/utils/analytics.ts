/**
 * 统计数据工具
 * 用于跟踪用户行为数据到Google Analytics
 */

/**
 * 跟踪搜索关键词
 */
export function trackSearch(term: string) {
  // Google Analytics 跟踪
  if (window.gtag) {
    window.gtag('event', 'search', {
      search_term: term
    });
  }
}

/**
 * 跟踪标签点击
 */
export function trackTagClick(tag: string) {
  // Google Analytics 跟踪
  if (window.gtag) {
    window.gtag('event', 'tag_click', {
      tag: tag
    });
  }
}

/**
 * 跟踪图片下载
 */
export function trackDownload(imageId: string, style: 'transparent' | 'outlined' = 'transparent') {
  // Google Analytics 跟踪
  if (window.gtag) {
    window.gtag('event', 'download', {
      image_id: imageId,
      style: style
    });
  }
}

/**
 * 跟踪图片详情页查看
 */
export function trackImageView(imageId: string) {
  // Google Analytics 跟踪
  if (window.gtag) {
    window.gtag('event', 'image_view', {
      image_id: imageId
    });
  }
}

/**
 * 跟踪样式选择
 */
export function trackStyleSelection(imageId: string, style: 'transparent' | 'outlined') {
  // Google Analytics 跟踪
  if (window.gtag) {
    window.gtag('event', 'style_selection', {
      image_id: imageId,
      style: style
    });
  }
}

// 声明全局gtag变量
declare global {
  interface Window {
    gtag: (
      command: 'event',
      action: string,
      params: Record<string, any>
    ) => void;
  }
} 