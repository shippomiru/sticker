import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Helmet } from 'react-helmet';
import { useTranslation } from 'react-i18next';
import ImageGrid from './ImageGrid';
import { images } from '../data/images';
import { trackTagClick } from '../utils/analytics';

// 标签到slug的映射表
const TAG_TO_SLUG: Record<string, string> = {
  'airplane': 'airplane-clipart',
  'apple': 'apple-clipart',
  'baby': 'baby-clipart',
  'bird': 'bird-clipart',
  'birthday': 'birthday-clipart',
  'book': 'book-clipart',
  'camera': 'camera-clipart',
  'car': 'car-clipart',
  'cat': 'cat-clipart',
  'christmas': 'christmas-clipart',
  'crown': 'crown-png',
  'dog': 'dog-clipart',
  'flower': 'flower-clipart',
  'gun': 'gun-png',
  'money': 'money-png',
  'pumpkin': 'pumpkin-clipart',
  'others': 'other-png'
};

// slug到标签的反向映射
const SLUG_TO_TAG: Record<string, string> = Object.entries(TAG_TO_SLUG).reduce(
  (acc, [tag, slug]) => ({ ...acc, [slug]: tag }), 
  {}
);

export default function TagPage() {
  console.log('TagPage rendering');
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  // 直接从路径中获取tagSlug，不使用useParams
  const pathname = location.pathname.startsWith('/') 
    ? location.pathname.substring(1) 
    : location.pathname;
  
  console.log('Current pathname:', pathname);
  
  // 从URL路径查找对应的标签名
  const tag = SLUG_TO_TAG[pathname];
  
  console.log('Found tag from pathname:', tag);

  // 如果没有找到对应的标签，重定向到首页
  useEffect(() => {
    if (!tag) {
      console.log('No matching tag found, redirecting to home');
      navigate('/', { replace: true });
    } else {
      console.log('Tag found:', tag);
    }
  }, [tag, navigate]);

  // 记录页面访问
  useEffect(() => {
    if (tag) {
      trackTagClick(tag);
    }
  }, [tag]);

  // 计算与该标签相关的图片数量
  const taggedImagesCount = tag ? images.filter(img => img.tags.includes(tag)).length : 0;

  // 获取相关标签（出现在同一个图片中的其他标签）
  const getRelatedTags = () => {
    if (!tag) return [];
    
    // 获取包含当前标签的所有图片
    const taggedImages = images.filter(img => img.tags.includes(tag));
    
    // 从这些图片中收集所有标签
    const relatedTagsMap: Record<string, number> = {};
    taggedImages.forEach(img => {
      img.tags.forEach(imgTag => {
        if (imgTag !== tag && imgTag !== 'others') {
          relatedTagsMap[imgTag] = (relatedTagsMap[imgTag] || 0) + 1;
        }
      });
    });
    
    // 按出现频率排序并返回前5个
    return Object.entries(relatedTagsMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([relatedTag]) => relatedTag);
  };

  const relatedTags = getRelatedTags();

  // 生成标签描述文本
  const getTagDescription = () => {
    const currentLang = i18n.language;
    
    if (currentLang === 'zh') {
      return `免费下载高质量${tag}透明PNG图像，所有${tag}图片都拥有透明背景。适用于设计、演示文稿、数字笔记和创意项目。`;
    }
    
    return `Download free ${tag} PNG images with transparent backgrounds. Our high-quality ${tag} clipart is perfect for presentations, digital planners, and creative projects.`;
  };

  // 如果标签不存在，不渲染任何内容（会通过useEffect重定向）
  if (!tag) {
    console.log('Rendering null due to missing tag');
    return null;
  }

  console.log('Rendering tag page for:', tag);
  
  return (
    <>
      <Helmet>
        <title>{`${tag.charAt(0).toUpperCase() + tag.slice(1)} Clipart – Transparent ${tag.charAt(0).toUpperCase() + tag.slice(1)} PNG Sticker | ClipPng`}</title>
        <meta 
          name="description" 
          content={`Download free ${tag} clipart PNG with transparent background – perfect for presentations, lesson plans, YouTube thumbnails, digital journals, and DIY collages.`} 
        />
        <link rel="canonical" href={`https://clippng.online/${TAG_TO_SLUG[tag]}`} />
      </Helmet>
      
      {/* 使用ImageGrid组件，预设当前标签但保留标签选择器，与首页保持一致的用户体验 */}
      <ImageGrid 
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        selectedTags={[tag]} 
        hideTagSelector={false}
      />
    </>
  );
} 