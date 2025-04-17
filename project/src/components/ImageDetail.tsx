import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowDown, X, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Helmet } from 'react-helmet';
import images from '../data/images.json';
import { trackImageView, trackStyleSelection, trackDownload } from '../utils/analytics';

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

  // 生成SEO元数据
  const getMainTag = () => {
    // 如果标签是others，则使用图片标题中的主体名词
    if (image.tags.includes('others') && image.tags.length === 1) {
      // 提取标题中的第一个单词作为主体名词
      const titleWords = image.caption.split(' ');
      return titleWords[0];
    }
    // 使用第一个非others标签
    const nonOthersTag = image.tags.find(tag => tag !== 'others');
    return nonOthersTag || image.tags[0];
  };

  const mainTag = getMainTag();
  // 首字母大写
  const capitalizedTag = mainTag.charAt(0).toUpperCase() + mainTag.slice(1);
  
  const seoTitle = `${capitalizedTag} Clipart – Transparent ${capitalizedTag} PNG Sticker | ClipPng`;
  const seoDescription = `Download free ${mainTag} clipart PNG with transparent background – perfect for presentations, lesson plans, YouTube thumbnails, digital journals, and DIY collages.`;
  const imageAlt = `${image.caption} - transparent background png & clipart`;

  useEffect(() => {
    trackImageView(image.id);
  }, [image, navigate]);

  const getImageUrl = (style: ImageStyle) => {
    switch (style) {
      case 'outlined':
        return image.sticker_url;
      default:
        return image.png_url;
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
    
    try {
      if (!image) return;
      
      const downloadUrl = selectedStyle === 'transparent' 
        ? image.png_url 
        : image.sticker_url;
      
      trackDownload(image.id, selectedStyle);
      
      const response = await fetch(downloadUrl);
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `${image.caption}-${selectedStyle}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
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
            className="absolute top-4 right-4 sm:top-6 sm:right-6 md:top-8 md:right-8 z-10 p-1.5 bg-white/80 backdrop-blur-sm rounded-full shadow-sm"
            aria-label="Close"
          >
            <X className="h-4 w-4 sm:h-5 sm:w-5 text-gray-600 hover:text-gray-900 transition-colors" />
          </button>

          {/* 图片预览区域 */}
          <div className="w-full lg:w-2/3 bg-gradient-to-br from-gray-50 to-white">
            <div className={`relative w-full h-[40vh] sm:h-[50vh] lg:h-full flex items-center justify-center p-4 sm:p-6 md:p-8 lg:p-16 ${bgColor} transition-colors duration-300`}>
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
                  <div className="animate-spin rounded-full h-8 w-8 sm:h-10 sm:w-10 md:h-12 md:w-12 border-t-2 border-b-2 border-blue-500"></div>
                </div>
              )}
            </div>
          </div>

          {/* 右侧内容区域 */}
          <div className="relative w-full lg:w-1/3 flex flex-col h-[55vh] sm:h-[40vh] lg:h-[90vh] bg-white border-t lg:border-t-0 lg:border-l border-gray-100">
            <div className="p-4 sm:p-6 md:p-8 lg:p-10 flex-grow overflow-y-auto">
              <div className="max-w-sm">
                <h1 className="text-xl sm:text-2xl font-semibold text-gray-900 mb-3 sm:mb-4 pr-8 sm:pr-12">
                  {image.caption}
                </h1>
                <div className="space-y-3 sm:space-y-4">
                  <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                    High quality free PNG image with transparent background, perfect for presentations, video editing, journaling, and creative design.
                  </p>
                  <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                    Try the sticker version to add charm to your planners, scrapbooks, or collages.
                  </p>
                </div>
                <div className="flex flex-wrap gap-1.5 sm:gap-2 mt-6 sm:mt-8">
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
            <div className="p-4 sm:p-6 md:p-8 lg:p-10 space-y-4 sm:space-y-6 bg-white">
              <div className="grid grid-cols-2 gap-2 sm:gap-3">
                <button
                  onClick={() => {
                    setSelectedStyle('transparent');
                    if (image) {
                      trackStyleSelection(image.id, 'transparent');
                    }
                  }}
                  className={`px-3 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-sm font-medium rounded-lg sm:rounded-xl transition-all duration-300 ${
                    selectedStyle === 'transparent'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-gray-50 text-gray-600 hover:bg-gray-100 hover:text-gray-900'
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
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-gray-50 text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  {t('whiteBorder')}
                </button>
              </div>
              <button
                onClick={handleDownload}
                className="w-full flex items-center justify-center gap-2 px-4 sm:px-6 py-3 sm:py-3.5 bg-blue-600 text-white rounded-lg sm:rounded-xl hover:bg-blue-700 transition-all duration-300 shadow-sm hover:shadow"
              >
                <ArrowDown className="h-4 w-4 sm:h-5 sm:w-5" />
                <span className="text-sm sm:text-base font-medium">{t('downloadImage')}</span>
              </button>
              <div className="text-center">
                <p className="text-[10px] sm:text-xs text-gray-300 mt-2 sm:mt-3">
                  Photo by {image.author} on Unsplash
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