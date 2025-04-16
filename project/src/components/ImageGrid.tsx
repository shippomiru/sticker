import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowDown, Tags, ChevronDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import images from '../data/images.json';
import { useNavigate } from 'react-router-dom';

// 定义图片对象的接口
interface ImageItem {
  id: string;
  caption: string;
  description: string;
  tags: string[];
  slug: string;
  author: string;
  original_url: string;
  png_url: string;
  sticker_url: string;
  created_at: string;
  tag_pages?: Record<string, string>; // 标签对应的内页链接
}

// 标签顺序 - 用于确保前端展示顺序一致
const TAG_ORDER = [
  "christmas", "flower", "book", "christmas tree", "dog", "car", 
  "cat", "pumpkin", "apple", "airplane", "birthday", "santa hat", 
  "crown", "gun", "books", "baby", "camera", "flowers", "money", "others"
];

interface ImageGridProps {
  searchTerm: string;
  selectedTags?: string[];
  onTagsChange?: (tags: string[]) => void;
}

export default function ImageGrid({ searchTerm = '', selectedTags = [], onTagsChange }: ImageGridProps) {
  const { t } = useTranslation();
  const [displayedImages, setDisplayedImages] = useState<ImageItem[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const imagesPerPage = 20; // 增加每页显示的图片数量
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
    return (images as ImageItem[]).filter((img) => {
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
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      
      // 找到对应的图片对象，以获取 caption
      const imageObj = (images as ImageItem[]).find(img => img.png_url === url || fixImageUrl(img.png_url) === url);
      const fileName = imageObj ? `${imageObj.caption}-transparent.png` : 'image.png';
      
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  // 获取所有使用中的标签，并按预设顺序排序
  const getOrderedTags = () => {
    // 从图片中获取所有使用中的标签集合
    const usedTags = new Set((images as ImageItem[]).flatMap((img) => img.tags));
    
    // 返回按TAG_ORDER排序的标签列表，只包含图片中实际使用的标签
    return TAG_ORDER.filter(tag => usedTags.has(tag));
  };

  // 获取标签对应的内页链接
  const getTagPageLink = (tag: string) => {
    // 找到任何一个包含该标签的图片
    const imageWithTag = (images as ImageItem[]).find(img => img.tags.includes(tag));
    
    // 如果图片有tag_pages属性且包含该标签，返回对应的内页链接
    if (imageWithTag?.tag_pages && tag in imageWithTag.tag_pages) {
      return imageWithTag.tag_pages[tag];
    }
    
    // 默认链接
    return `/?tag=${tag}`;
  };

  // 处理标签点击事件
  const handleTagClick = (tag: string) => {
    const tagLink = getTagPageLink(tag);
    
    // 如果是内部查询参数格式(/?tag=xxx)，使用筛选功能
    if (tagLink.startsWith('/?tag=')) {
      // 重置为第一页
      setCurrentPage(1);
      
      // 切换标签，使用父组件提供的回调来维持状态
      if (onTagsChange) {
        onTagsChange(selectedTags.includes(tag) ? [] : [tag]);
      }
    } else {
      // 否则导航到对应的内页链接
      navigate(tagLink);
    }
  };

  // 使用筛选后的图片
  const filteredImages = getFilteredImages();
  const hasMoreImages = currentPage * imagesPerPage < filteredImages.length;
  // 获取排序后的标签列表
  const orderedTags = getOrderedTags();

  return (
    <>
      {/* Tags */}
      <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center space-x-2 mb-4">
          <Tags className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">{t('filterByTags')}</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {orderedTags.map((tag) => (
            <button
              key={tag}
              onClick={() => handleTagClick(tag)}
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
                  >
                    <ArrowDown className="h-5 w-5 text-gray-900" />
                  </button>
                </div>
              </Link>
              <div className="p-4">
                <p className="text-sm text-gray-700 mb-3 line-clamp-2">{image.caption}</p>
                <div className="flex flex-wrap gap-1.5">
                  {image.tags.map((tag) => (
                    <button
                      key={tag}
                      onClick={() => handleTagClick(tag)}
                      className="px-2 py-1 bg-gray-50 rounded-md text-xs font-medium text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                    >
                      {tag}
                    </button>
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
              {t('loadMore')} <ChevronDown className="h-4 w-4 inline mb-0.5" />
            </button>
          </div>
        )}
      </main>
    </>
  );
}