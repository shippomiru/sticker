import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
  en: {
    translation: {
      search: 'Search images...',
      filterByTags: 'Trending Topics:',
      loadMore: 'Load More',
      loadingMore: 'Loading more images...',
      noResultsFound: 'No results found.',
      tryDifferentSearch: 'Try different keywords or remove filters to find more images.',
      transparentBackground: 'Transparent',
      whiteBorder: 'White Border',
      downloadImage: 'Download Image',
      currentImage: 'Current image:',
      foundImages: 'Found {{count}} images matching your criteria',
      footer: {
        about: 'About',
        contact: 'Contact',
        terms: 'Terms of Service',
        privacy: 'Privacy Policy',
        copyright: '© 2025 ClipPng. All rights reserved.',
      },
    },
  },
  zh: {
    translation: {
      search: '搜索图片...',
      filterByTags: '热门分类：',
      loadMore: '加载更多图片',
      loadingMore: '正在加载更多图片...',
      noResultsFound: '未找到结果。',
      tryDifferentSearch: '尝试不同的关键词或移除筛选条件以查找更多图片。',
      transparentBackground: '透明背景',
      whiteBorder: '白色边框',
      downloadImage: '下载图片',
      currentImage: '当前加载图片:',
      foundImages: '找到 {{count}} 张符合条件的图片',
      footer: {
        about: '关于我们',
        contact: '联系我们',
        terms: '服务条款',
        privacy: '隐私政策',
        copyright: '© 2025 ClipPng. 保留所有权利。',
      },
    },
  },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en', // Set default language to English
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;