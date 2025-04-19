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
      whiteBorder: 'Sticker',
      downloadImage: 'Download Image',
      currentImage: 'Current image:',
      showTags: 'show',
      hideTags: 'hide',
      foundImages: 'Found {{count}} images matching your criteria',
      footer: {
        about: 'About',
        contact: 'Contact',
        terms: 'Terms of Service',
        privacy: 'Privacy Policy',
        copyright: '© 2025 ClipPng. All rights reserved. Images powered by Unsplash.',
      },
      about: {
        title: 'About ClipPng',
        mission: {
          title: 'Our Mission',
          content: 'ClipPng is a free image resource platform dedicated to providing high-quality image assets for designers, developers, and creators. Our platform offers a curated collection of professional images that are free to use in both personal and commercial projects.'
        },
        howToUse: {
          title: 'How to Use',
          search: {
            title: 'Search Images',
            content: 'Use the search bar at the top to find images instantly. Our search supports searching through image titles and descriptions.'
          },
          filter: {
            title: 'Filter by Tags',
            content: 'Use tags to quickly filter specific types of images.'
          },
          download: {
            title: 'Download Images',
            content: 'Each image comes in multiple formats: transparent sticker and white background sticker. Click on any image to access the download options.'
          }
        },
        license: {
          title: 'Image License',
          intro: 'All images on ClipPng are free to use for both personal and commercial purposes. Our license terms are simple:',
          terms: [
            'Free to use, no payment required',
            'Suitable for both commercial and non-commercial use',
            'Attribution to ClipPng is appreciated but not required',
            'Reselling unmodified images is not permitted'
          ]
        },
        contact: {
          title: 'Contact Us',
          intro: 'Have questions, suggestions, or interested in collaboration? We\'d love to hear from you:',
          email: 'Email: contact@clippng.online'
        }
      }
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
      whiteBorder: '贴纸',
      downloadImage: '下载图片',
      currentImage: '当前加载图片:',
      showTags: '显示',
      hideTags: '隐藏',
      foundImages: '找到 {{count}} 张符合条件的图片',
      footer: {
        about: '关于我们',
        contact: '联系我们',
        terms: '服务条款',
        privacy: '隐私政策',
        copyright: '© 2025 ClipPng. 保留所有权利。图片由Unsplash提供。',
      },
      about: {
        title: '关于 ClipPng',
        mission: {
          title: '我们的使命',
          content: 'ClipPng 是一个免费的图片资源平台，致力于为设计师、开发者和创作者提供高质量的图片素材。我们的平台提供精心策划的专业图片集合，可免费用于个人和商业项目。'
        },
        howToUse: {
          title: '使用方法',
          search: {
            title: '搜索图片',
            content: '使用顶部的搜索栏即时查找图片。我们的搜索功能支持搜索图片标题和描述。'
          },
          filter: {
            title: '按标签筛选',
            content: '使用标签快速筛选特定类型的图片。'
          },
          download: {
            title: '下载图片',
            content: '每张图片都提供多种格式：透明背景贴纸和白色背景贴纸。点击任意图片，即可访问下载选项。'
          }
        },
        license: {
          title: '图片许可',
          intro: 'ClipPng 上的所有图片均可免费用于个人和商业用途。我们的许可条款简单明了：',
          terms: [
            '免费使用，无需付费',
            '适用于商业和非商业用途',
            '感谢您标注 ClipPng，但这不是必需的',
            '不允许转售未经修改的图片'
          ]
        },
        contact: {
          title: '联系我们',
          intro: '有问题、建议或合作意向？我们很乐意听取您的意见：',
          email: '邮箱：contact@clippng.online'
        }
      }
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