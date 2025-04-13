import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowDown, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import images from '../data/images.json';

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
    const url = getImageUrl(selectedStyle);
    try {
      const response = await fetch(url);
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
      console.error('下载失败:', error);
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
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-6">
      <div className="relative w-full max-w-7xl bg-gradient-to-b from-gray-50 to-white rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col lg:flex-row">
        {/* 关闭按钮 */}
        <button
          onClick={handleClose}
          className="absolute top-8 right-8 z-10"
          aria-label="Close"
        >
          <X className="h-5 w-5 text-gray-600 hover:text-gray-900 transition-colors" />
        </button>

        {/* 图片预览区域 */}
        <div className="w-full lg:w-2/3 bg-gradient-to-br from-gray-50 to-white">
          <div className={`relative w-full h-full flex items-center justify-center p-8 lg:p-16 ${bgColor} transition-colors duration-300`}>
            <img
              key={currentImageUrl}
              src={currentImageUrl}
              alt={`${image.caption} - ${selectedStyle === 'transparent' ? 'Transparent' : 'Outlined'}`}
              className="w-full h-full object-contain"
              onLoad={handleImageLoad}
              onError={handleImageError}
            />
            {!imageLoaded && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
              </div>
            )}
          </div>
        </div>

        {/* 右侧内容区域 */}
        <div className="relative w-full lg:w-1/3 flex flex-col h-[40vh] lg:h-[90vh] bg-white border-l border-gray-100">
          <div className="p-6 lg:p-10 flex-grow overflow-y-auto">
            <div className="max-w-sm">
              <h1 className="text-2xl font-semibold text-gray-900 mb-4 pr-12">
                {image.caption}
              </h1>
              <p className="text-gray-600 mb-8 leading-relaxed">
                {image.description}
              </p>
              <div className="flex flex-wrap gap-2 mb-8">
                {image.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1.5 bg-gray-50 rounded-full text-sm font-medium text-gray-600"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* 样式选择和下载 */}
          <div className="p-6 lg:p-10 space-y-6 bg-white">
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setSelectedStyle('transparent')}
                className={`px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-300 ${
                  selectedStyle === 'transparent'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-gray-50 text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                {t('transparentBackground')}
              </button>
              <button
                onClick={() => setSelectedStyle('outlined')}
                className={`px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-300 ${
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
              className="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all duration-300 shadow-sm hover:shadow"
            >
              <ArrowDown className="h-5 w-5" />
              <span className="font-medium">{t('downloadImage')}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ImageDetail;