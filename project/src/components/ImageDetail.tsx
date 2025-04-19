import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowDown, X, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Helmet } from 'react-helmet';
import { images, ImageData } from '../data/images';
import { trackImageView, trackStyleSelection, trackDownload } from '../utils/analytics';
import { downloadImage } from '../utils/download';

type ImageStyle = 'transparent' | 'outlined';

interface ImageDetailProps {
  onClose?: () => void;
}

export function ImageDetail({ onClose }: ImageDetailProps) {
  const { t } = useTranslation();
  const { slug } = useParams<{ slug?: string }>();
  const navigate = useNavigate();
  const [selectedStyle, setSelectedStyle] = useState<ImageStyle>('transparent');
  const [imageLoaded, setImageLoaded] = useState(false);

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  const image = images.find(img => img.slug === slug);

  if (!image) {
    navigate('/');
    return null;
  }

  // 确保图片URL格式正确
  const fixImageUrl = (url: string) => {
    if (!url.startsWith('/images/') && !url.startsWith('http')) {
      return `/images/${url}`;
    }
    return url;
  };

  // 生成SEO元数据
  const getMainTag = () => {
    // 打印原始数据用于调试
    console.log('图片数据:', {
      id: image.id,
      caption: image.caption,
      tags: image.tags,
      main_noun: image.main_noun
    });
    
    // 优先使用非others标签
    const nonOthersTag = image.tags.find(tag => tag !== 'others');
    if (nonOthersTag) {
      console.log('使用非others标签:', nonOthersTag);
      return nonOthersTag;
    }
    
    // 如果标签都是others，则优先使用main_noun字段
    if (image.main_noun) {
      console.log('使用main_noun字段:', image.main_noun);
      return image.main_noun;
    }
    
    // 兜底逻辑：从图片标题中提取主体名词
    const titleWords = image.caption.split(' ');
    
    // 忽略冠词和常见修饰词
    const skipWords = ['a', 'an', 'the', 'small', 'large', 'big', 'tiny', 'huge', 'little'];
    
    // 寻找第一个非冠词、非修饰词的名词
    const mainNoun = titleWords.find(word => 
      !skipWords.includes(word.toLowerCase())
    );
    
    // 如果找不到合适的词，则使用第一个非冠词词语
    const firstNonArticle = titleWords.find(word => 
      !['a', 'an', 'the'].includes(word.toLowerCase())
    );
    
    const result = mainNoun || firstNonArticle || titleWords[0] || 'image';
    console.log('使用兜底逻辑:', result);
    return result;
  };

  const mainTag = getMainTag();
  // 首字母大写
  const capitalizedTag = mainTag.charAt(0).toUpperCase() + mainTag.slice(1);
  
  // 优化SEO标题，使用更精确的名词
  const seoTitle = `${capitalizedTag} Clipart – Transparent ${capitalizedTag} PNG Sticker | ClipPng`;
  
  // 优化SEO描述，添加更多细节
  const seoDescription = `Download free ${mainTag} clipart PNG with transparent background – ${image.caption}. Perfect for presentations, lesson plans, YouTube thumbnails, digital journals, and DIY collages.`;
  const imageAlt = `${image.caption} - transparent background png & clipart`;

  // 生成归属链接
  const getAttributionLinks = () => {
    const appName = 'ClipPng';
    
    // 按照Unsplash官方指南使用username构建链接
    let photographerLink = '';
    if (image.username) {
      // 使用用户名构建标准格式的链接
      photographerLink = `https://unsplash.com/@${image.username}?utm_source=${appName}&utm_medium=referral`;
      console.log('使用用户名构建链接:', photographerLink);
    } else if (image.unsplash_id) {
      // 如果有unsplash_id但没有username，使用ID构建链接
      photographerLink = `https://unsplash.com/photos/${image.unsplash_id}?utm_source=${appName}&utm_medium=referral`;
      console.log('使用unsplash_id构建链接:', photographerLink);
    } else if (image.photographer_url) {
      // 如果有摄影师URL，则使用它作为备选，但添加UTM参数
      const baseUrl = image.photographer_url.split('?')[0]; // 移除可能存在的参数
      photographerLink = `${baseUrl}?utm_source=${appName}&utm_medium=referral`;
      console.log('使用摄影师直接链接:', photographerLink);
    } else if (image.username) {
      // 如果有用户名，则构建链接
      photographerLink = `https://unsplash.com/@${image.username}?utm_source=${appName}&utm_medium=referral`;
      console.log('使用用户名构建链接:', photographerLink);
    } else {
      console.log('没有找到用户名或摄影师链接，作者信息将不可点击');
    }
    
    const unsplashLink = `https://unsplash.com/?utm_source=${appName}&utm_medium=referral`;
    
    return { photographerLink, unsplashLink };
  };
  
  const { photographerLink, unsplashLink } = getAttributionLinks();

  useEffect(() => {
    trackImageView(image.id);
  }, [image, navigate]);

  const getImageUrl = (style: ImageStyle) => {
    switch (style) {
      case 'outlined':
        return fixImageUrl(image.sticker_url);
      default:
        return fixImageUrl(image.png_url);
    }
  };

  const handleClose = () => {
    if (onClose) {
      onClose();
    }
    navigate('/');
  };

  const handleDownload = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation(); // 阻止事件冒泡
    
    try {
      if (!image) return;
      
      const downloadUrl = getImageUrl(selectedStyle);
      
      // 记录下载事件到Google Analytics
      trackDownload(image.id, selectedStyle);
      
      // 如果有Unsplash ID，在后台触发Unsplash下载事件，不影响主下载流程
      if (image.id && image.unsplash_id) {
        // 使用setTimeout确保下载逻辑先执行，不被上报逻辑阻塞
        setTimeout(() => {
          import('../utils/unsplash').then(({ triggerUnsplashDownload }) => {
            triggerUnsplashDownload(image.unsplash_id || image.id).catch(error => {
              console.error('触发Unsplash下载事件失败:', error);
            });
          });
        }, 100);
      }
      
      // 使用综合下载方法，但不传递第三个参数，避免新窗口下载
      const filename = `${image.caption}-${selectedStyle}.png`;
      const success = await downloadImage(downloadUrl, filename);
      
      if (!success) {
        console.warn('综合下载方法失败，可能是CORS限制，建议用户右键保存图片');
      }
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleImageLoad = () => {
    console.log(`图片已加载: ${selectedStyle}`);
    setImageLoaded(true);
  };

  const handleImageError = () => {
    console.error(`图片加载错误: ${getImageUrl(selectedStyle)}`);
  };

  // 切换样式时重置图片加载状态
  useEffect(() => {
    setImageLoaded(false);
  }, [selectedStyle]);

  const currentImageUrl = getImageUrl(selectedStyle);
  const bgColor = 'bg-gray-900'; // 始终使用深色背景

  return (
    <>
      <Helmet>
        <title>{seoTitle}</title>
        <meta name="description" content={seoDescription} />
        <link rel="canonical" href={`https://clippng.online/${slug}`} />
      </Helmet>
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4 md:p-6">
        <div className="relative w-full max-w-7xl bg-gradient-to-b from-gray-50 to-white rounded-xl sm:rounded-2xl shadow-2xl overflow-hidden max-h-[95vh] sm:max-h-[90vh] flex flex-col lg:flex-row">
          {/* 关闭按钮 */}
          <button
            onClick={handleClose}
            className="absolute top-3 right-3 sm:top-6 sm:right-6 md:top-8 md:right-8 z-10 p-2 bg-white/90 backdrop-blur-sm rounded-full shadow-md"
            aria-label="Close"
          >
            <X className="h-5 w-5 sm:h-5 sm:w-5 text-gray-700 hover:text-gray-900 transition-colors" />
          </button>

          {/* 图片预览区域 */}
          <div className="w-full lg:w-2/3 bg-gradient-to-br from-gray-900 to-black">
            <div className={`relative w-full h-[45vh] sm:h-[50vh] lg:h-full flex items-center justify-center p-4 sm:p-6 md:p-8 lg:p-16 transition-colors duration-300`}>
              <img
                key={currentImageUrl}
                src={currentImageUrl}
                alt={imageAlt}
                className="w-full h-full object-contain"
                onLoad={handleImageLoad}
                onError={handleImageError}
              />
              {!imageLoaded && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="animate-spin rounded-full h-10 w-10 sm:h-10 sm:w-10 md:h-12 md:w-12 border-t-2 border-b-2 border-blue-500"></div>
                </div>
              )}
            </div>
          </div>

          {/* 右侧内容区域 */}
          <div className="relative w-full lg:w-1/3 flex flex-col h-auto sm:h-[40vh] lg:h-[90vh] bg-white border-t lg:border-t-0 lg:border-l border-gray-100">
            {/* 标题区域 */}
            <div className="p-4 sm:p-6 md:p-8 lg:p-10 flex-grow overflow-y-auto">
              <div className="max-w-sm">
                <h1 className="text-lg sm:text-2xl font-semibold text-gray-900 mb-1 sm:mb-4 pr-6 sm:pr-12">
                  {image.caption}
                </h1>
                {/* 在移动端隐藏描述，在平板和桌面端显示 */}
                <div className="hidden sm:block space-y-3 sm:space-y-4">
                  <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                    High quality free PNG image with transparent background, perfect for presentations, video editing, journaling, and creative design.
                  </p>
                  <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                    Try the sticker version to add charm to your planners, scrapbooks, or collages.
                  </p>
                </div>
                {/* 在移动端隐藏标签，在平板和桌面端显示 */}
                <div className="hidden sm:flex flex-wrap gap-1.5 sm:gap-2 mt-6 sm:mt-8">
                  {image.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2.5 py-1 sm:px-3 sm:py-1.5 bg-gray-50 rounded-full text-xs sm:text-sm font-medium text-gray-600"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* 样式选择和下载 */}
            <div className="p-4 pb-5 sm:p-6 md:p-8 lg:p-10 space-y-4 sm:space-y-6 bg-white border-t border-gray-100">
              <div className="grid grid-cols-2 gap-3 sm:gap-3">
                <button
                  onClick={() => {
                    setSelectedStyle('transparent');
                    if (image) {
                      trackStyleSelection(image.id, 'transparent');
                    }
                  }}
                  className={`px-3 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-sm font-medium rounded-lg sm:rounded-xl transition-all duration-300 ${
                    selectedStyle === 'transparent'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:text-gray-900 border border-gray-200'
                  }`}
                >
                  {t('transparentBackground')}
                </button>
                <button
                  onClick={() => {
                    setSelectedStyle('outlined');
                    if (image) {
                      trackStyleSelection(image.id, 'outlined');
                    }
                  }}
                  className={`px-3 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-sm font-medium rounded-lg sm:rounded-xl transition-all duration-300 ${
                    selectedStyle === 'outlined'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:text-gray-900 border border-gray-200'
                  }`}
                >
                  {t('whiteBorder')}
                </button>
              </div>
              <button
                onClick={handleDownload}
                className="w-full flex items-center justify-center gap-2 px-4 sm:px-6 py-3 sm:py-3.5 bg-blue-600 text-white rounded-lg sm:rounded-xl hover:bg-blue-700 transition-all duration-300 shadow-md hover:shadow-lg"
              >
                <ArrowDown className="h-5 w-5 sm:h-5 sm:w-5" />
                <span className="text-base sm:text-base font-medium">{t('downloadImage')}</span>
              </button>
              <div className="text-center">
                <p className="text-xs sm:text-xs text-gray-500 mt-2 sm:mt-3">
                  Photo by <a href={photographerLink} target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-blue-500 transition-colors">
                    {image.username || image.author}
                  </a> on <a href={unsplashLink} target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-blue-500 transition-colors">Unsplash</a>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default ImageDetail;