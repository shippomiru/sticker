import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowDown, Tags, ChevronDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import images from '../data/images.json';
import { useNavigate } from 'react-router-dom';
import { trackTagClick, trackDownload } from '../utils/analytics';

interface ImageGridProps {
  searchTerm: string;
  selectedTags?: string[];
  onTagsChange?: (tags: string[]) => void;
}

export default function ImageGrid({ searchTerm = '', selectedTags = [], onTagsChange }: ImageGridProps) {
  const { t } = useTranslation();
  const [displayedImages, setDisplayedImages] = useState<typeof images>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const imagesPerPage = 24; // 每页显示24张图片
  const navigate = useNavigate();

  // 检查图片URL格式，确保所有URL都有/images/前缀
  const fixImageUrl = (url: string) => {
    if (!url.startsWith('/images/') && !url.startsWith('http')) {
      return `/images/${url}`;
    }
    return url;
  };

  // 获取筛选后的图片列表
  const getFilteredImages = () => {
    return images.filter((img) => {
      const matchesSearch = img.caption
        .toLowerCase()
        .includes(searchTerm.toLowerCase());
      const matchesTags =
        selectedTags.length === 0 ||
        selectedTags.some((tag) => img.tags.includes(tag));
      return matchesSearch && matchesTags;
    }).map(img => ({
      ...img,
      png_url: fixImageUrl(img.png_url),
      sticker_url: fixImageUrl(img.sticker_url)
    }));
  };

  // 初始加载和筛选条件变化时重新加载图片
  useEffect(() => {
    const filteredImgs = getFilteredImages();
    loadImages(1, filteredImgs);
    console.log(`筛选后图片数量: ${filteredImgs.length}`);
  }, [searchTerm, selectedTags, images]);

  // 加载指定页的图片
  const loadImages = (page: number, imageSource = getFilteredImages()) => {
    const startIndex = (page - 1) * imagesPerPage;
    const endIndex = startIndex + imagesPerPage;
    
    const newImages = imageSource.slice(startIndex, endIndex);
    if (page === 1) {
      setDisplayedImages(newImages);
    } else {
      setDisplayedImages(prev => [...prev, ...newImages]);
    }
    setCurrentPage(page);
    console.log(`当前页: ${page}, 显示图片数: ${newImages.length}, 总数据: ${imageSource.length}`);
  };

  // 加载更多图片
  const loadMoreImages = () => {
    const filteredImgs = getFilteredImages();
    const nextPage = currentPage + 1;
    loadImages(nextPage, filteredImgs);
  };

  const handleDownload = async (url: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation(); // 阻止事件冒泡，防止触发Link跳转
    
    try {
      console.log('开始下载图片:', url);
      
      // 找到对应的图片对象，以获取ID
      const normalizedUrl = url.includes('/images/') ? url : fixImageUrl(url);
      const imageObj = images.find(img => 
        fixImageUrl(img.png_url) === normalizedUrl || 
        img.png_url === normalizedUrl || 
        img.png_url === url);
      
      if (imageObj) {
        // 记录下载事件
        trackDownload(imageObj.id, url.includes('outlined') ? 'outlined' : 'transparent');
        console.log('找到匹配图片:', imageObj.caption);
      } else {
        console.error('未找到匹配图片对象');
      }
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      
      // 生成文件名
      const fileName = imageObj 
        ? `${imageObj.caption}-transparent.png` 
        : url.split('/').pop() || 'image.png';
      
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
      console.log('下载完成:', fileName);
    } catch (error) {
      console.error('下载失败:', error);
      alert('下载图片失败，请稍后重试');
    }
  };

  // Get unique tags from all images and sort them
  const allTags = Array.from(
    new Set(images.flatMap((img) => img.tags))
  ).sort((a, b) => {
    // 确保"others"标签显示在最后
    if (a === "others") return 1;
    if (b === "others") return -1;
    return a.localeCompare(b);
  });

  const toggleTag = (tag: string) => {
    // 记录标签点击
    trackTagClick(tag);
    
    // 重置为第一页
    setCurrentPage(1);
    
    // 切换标签，使用父组件提供的回调来维持状态
    if (onTagsChange) {
      onTagsChange(selectedTags.includes(tag) ? [] : [tag]);
    }
  };

  // 使用筛选后的图片
  const filteredImages = getFilteredImages();
  const hasMoreImages = currentPage * imagesPerPage < filteredImages.length;

  return (
    <>
      {/* Tags */}
      <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center space-x-2 mb-4">
          <Tags className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">{t('filterByTags')}</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {allTags.map((tag) => (
            <button
              key={tag}
              onClick={() => toggleTag(tag)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                selectedTags.includes(tag)
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-white text-gray-700 hover:bg-blue-50 hover:text-blue-600 border border-gray-200'
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
        <div className="mt-4 text-sm text-gray-500">
          {t('foundImages', { count: filteredImages.length })}
        </div>
      </div>

      {/* Image Grid */}
      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {displayedImages.map((image) => (
            <div
              key={image.id}
              className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden group"
            >
              <Link
                to={`/${image.slug}`}
                className="block relative aspect-square"
              >
                <img
                  src={image.png_url}
                  alt={image.caption}
                  className="w-full h-full object-cover bg-gray-900"
                  onError={(e) => {
                    console.error(`加载图片失败: ${image.png_url}`);
                    const target = e.target as HTMLImageElement;
                    target.onerror = null; // 防止无限循环
                    target.src = '/placeholder-image.png'; // 使用一个占位图像
                  }}
                  onLoad={() => console.log(`成功加载图片: ${image.png_url}`)}
                />
                <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-center justify-center backdrop-blur-[2px]">
                  <button 
                    className="p-3 bg-white/90 backdrop-blur rounded-xl hover:bg-white transition-all duration-300 shadow-lg transform translate-y-2 group-hover:translate-y-0 group-hover:scale-105"
                    onClick={(e) => handleDownload(image.png_url, e)}
                    aria-label="下载图片"
                    type="button"
                  >
                    <ArrowDown className="h-5 w-5 text-gray-900" />
                  </button>
                </div>
              </Link>
              <div className="p-4">
                <p className="text-sm text-gray-700 mb-3 line-clamp-2">{image.caption}</p>
                <div className="flex flex-wrap gap-1.5">
                  {image.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-gray-50 rounded-md text-xs font-medium text-gray-600"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* 底部加载更多按钮 */}
        {hasMoreImages && (
          <div className="flex justify-center mt-8 mb-12">
            <button
              onClick={loadMoreImages}
              className="px-6 py-3 bg-blue-50 text-blue-600 hover:bg-blue-100 border border-blue-200 transition duration-300 rounded-md font-medium shadow-sm"
            >
              {t('loadMore')}
            </button>
          </div>
        )}
      </main>
    </>
  );
}