import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ArrowDown, Tags, ChevronDown, Filter, Search } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import images from '../data/images.json';
import { useNavigate } from 'react-router-dom';
import { trackTagClick, trackDownload } from '../utils/analytics';
import { downloadImage } from '../utils/download';

interface ImageGridProps {
  searchTerm: string;
  selectedTags?: string[];
  onTagsChange?: (tags: string[]) => void;
}

export default function ImageGrid({ searchTerm = '', selectedTags = [], onTagsChange }: ImageGridProps) {
  const { t } = useTranslation();
  const [displayedImages, setDisplayedImages] = useState<typeof images>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [showTagsOnMobile, setShowTagsOnMobile] = useState(false);
  const imagesPerPage = 24; // 每页显示24张图片
  const navigate = useNavigate();
  const loadMoreRef = useRef<HTMLDivElement>(null);

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
    e.stopPropagation(); // 阻止事件冒泡，防止点击下载按钮时触发详情页跳转
    
    try {
      // 找到对应的图片对象，以获取ID
      const imageObj = images.find(img => img.png_url === url || fixImageUrl(img.png_url) === url);
      if (imageObj) {
        // 记录下载事件
        trackDownload(imageObj.id, url === imageObj.sticker_url ? 'outlined' : 'transparent');
      }
      
      // 使用综合下载方法
      const filename = imageObj ? `${imageObj.caption}-transparent.png` : 'image-transparent.png';
      const success = await downloadImage(url, filename);
      
      if (!success) {
        console.warn('综合下载方法失败，可能是CORS限制，建议用户右键保存图片');
      }
    } catch (error) {
      console.error('Download failed:', error);
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

  // 使用IntersectionObserver监听"加载更多"按钮
  useEffect(() => {
    // 如果没有更多图片可加载，则不需要监听
    if (!hasMoreImages || !loadMoreRef.current) return;
    
    const observer = new IntersectionObserver((entries) => {
      // 当"加载更多"按钮进入视口时，自动加载更多图片
      if (entries[0].isIntersecting) {
        loadMoreImages();
      }
    }, { 
      rootMargin: '0px 0px 300px 0px', // 当元素距离视口底部300px时触发
      threshold: 0.1 
    });
    
    observer.observe(loadMoreRef.current);
    
    return () => {
      if (loadMoreRef.current) {
        observer.unobserve(loadMoreRef.current);
      }
    };
  }, [loadMoreRef.current, hasMoreImages, currentPage]);

  return (
    <>
      {/* Tags - 标签部分移动端可折叠 */}
      <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Tags className="h-5 w-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">{t('filterByTags')}</h2>
          </div>
          
          {/* 移动端展开/折叠按钮 */}
          <button 
            className="md:hidden flex items-center text-sm text-gray-700 hover:text-blue-600"
            onClick={() => setShowTagsOnMobile(!showTagsOnMobile)}
          >
            <Filter className="h-4 w-4 mr-1" />
            <span>{showTagsOnMobile ? t('hideTags') : t('showTags')}</span>
            <ChevronDown 
              className={`h-4 w-4 ml-1 transition-transform ${showTagsOnMobile ? 'rotate-180' : ''}`}
            />
          </button>
        </div>
        
        <div className={`${showTagsOnMobile ? 'max-h-64' : 'max-h-0 md:max-h-none'} overflow-y-auto md:overflow-visible transition-all duration-300 ease-in-out md:max-h-none`}>
          <div className="flex flex-wrap gap-2 mb-2">
            {allTags.map((tag) => (
              <button
                key={tag}
                onClick={() => toggleTag(tag)}
                className={`px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedTags.includes(tag)
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-white text-gray-700 hover:bg-blue-50 hover:text-blue-600 border border-gray-200'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
        
        {/* 暂时注释掉图片数量显示，因为网站图片太少 */}
        {/* <div className="mt-4 text-sm text-gray-500">
          {t('foundImages', { count: filteredImages.length })}
        </div> */}
      </div>

      {/* Image Grid - 响应式网格 */}
      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6 md:gap-8">
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
                  loading="lazy" // 添加懒加载
                />
                <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-center justify-center backdrop-blur-[2px]">
                  <button 
                    className="p-2 sm:p-3 bg-white/90 backdrop-blur rounded-xl hover:bg-white transition-all duration-300 shadow-lg transform translate-y-2 group-hover:translate-y-0 group-hover:scale-105"
                    onClick={(e) => handleDownload(image.png_url, e)}
                  >
                    <ArrowDown className="h-4 w-4 sm:h-5 sm:w-5 text-gray-900" />
                  </button>
                </div>
              </Link>
              <div className="p-3 sm:p-4">
                <p className="text-xs sm:text-sm text-gray-700 mb-2 sm:mb-3 line-clamp-2">{image.caption}</p>
                <div className="flex flex-wrap gap-1 sm:gap-1.5">
                  {image.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="px-1.5 py-0.5 sm:px-2 sm:py-1 bg-gray-50 rounded-md text-xs font-medium text-gray-600"
                    >
                      {tag}
                    </span>
                  ))}
                  {image.tags.length > 3 && (
                    <span className="px-1.5 py-0.5 sm:px-2 sm:py-1 bg-gray-50 rounded-md text-xs font-medium text-gray-500">
                      +{image.tags.length - 3}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 加载更多区域 - 无限滚动 */}
        {filteredImages.length > 0 && (
          <div 
            ref={loadMoreRef}
            className="mt-12 flex flex-col items-center justify-center"
          >
            {hasMoreImages ? (
              <div className="text-center">
                <div className="animate-pulse flex items-center justify-center space-x-2">
                  <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
                  <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
                  <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
                </div>
                <p className="text-sm text-gray-500 mt-3">{t('loadingMore')}</p>
              </div>
            ) : (
              <p className="text-sm text-gray-500">{t('noMoreImages')}</p>
            )}
          </div>
        )}
        
        {/* 无结果提示 */}
        {filteredImages.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="bg-gray-100 rounded-full p-6 mb-4">
              <Search className="h-8 w-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">{t('noResultsFound')}</h3>
            <p className="text-gray-500 text-center max-w-md">
              {t('tryDifferentSearch')}
            </p>
          </div>
        )}
      </main>
    </>
  );
}