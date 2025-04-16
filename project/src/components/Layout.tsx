import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Search } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { trackSearch } from '../utils/analytics';

// 极简高级优雅的字母C Logo组件
const CLogo = ({ className = '', size = 24 }) => {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 512 512" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* 方形背景，带圆角 */}
      <rect width="512" height="512" rx="80" fill="currentColor" />
      
      {/* 居中的白色字母C，设计风格极简优雅 */}
      <path 
        d="M336 176C336 176 270 144 206 176C142 208 126 304 206 336C286 368 336 336 336 336" 
        stroke="white" 
        strokeWidth="40" 
        strokeLinecap="round" 
        strokeLinejoin="round"
        fill="none" 
      />
    </svg>
  );
};

interface LayoutProps {
  searchTerm?: string;
  onSearchChange?: (term: string) => void;
}

export function Layout({ searchTerm = '', onSearchChange = () => {} }: LayoutProps) {
  const { t, i18n } = useTranslation();
  const location = useLocation();

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'zh' : 'en';
    i18n.changeLanguage(newLang);
  };

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const term = (e.currentTarget.elements.namedItem('search') as HTMLInputElement).value;
    onSearchChange(term);
    
    // 记录搜索词
    if (term.trim()) {
      trackSearch(term.trim());
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center space-x-3">
              <CLogo className="text-blue-600" size={32} />
              <h1 className="text-2xl font-bold text-gray-900">ClipPng</h1>
            </Link>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                <form onSubmit={handleSearch} className="w-64">
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                      <Search className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      type="text"
                      name="search"
                      value={searchTerm}
                      onChange={(e) => onSearchChange(e.target.value)}
                      className="block w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none transition-colors"
                      placeholder={t('search')}
                    />
                  </div>
                </form>
              </div>
              <button
                onClick={toggleLanguage}
                className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors rounded-lg hover:bg-blue-50"
              >
                {i18n.language === 'en' ? 'ZH' : 'EN'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <Outlet />

      {/* Footer */}
      <footer className="bg-white border-t border-gray-100 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <CLogo className="text-blue-600" size={24} />
              <span className="text-xl font-semibold text-gray-900">ClipPng</span>
            </div>
            <div className="flex flex-wrap gap-6 text-sm">
              <Link 
                to="/about" 
                className={`transition-colors ${
                  location.pathname === '/about'
                    ? 'text-blue-600'
                    : 'text-gray-600 hover:text-blue-600'
                }`}
              >
                {t('footer.about')}
              </Link>
              <a href="#" className="text-gray-600 hover:text-blue-600 transition-colors">
                {t('footer.contact')}
              </a>
              <a href="#" className="text-gray-600 hover:text-blue-600 transition-colors">
                {t('footer.terms')}
              </a>
              <a href="#" className="text-gray-600 hover:text-blue-600 transition-colors">
                {t('footer.privacy')}
              </a>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-100">
            <p className="text-center text-sm text-gray-500">
              {t('footer.copyright')}
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Layout;