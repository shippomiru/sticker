import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Search, Image as ImageIcon } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface LayoutProps {
  searchTerm?: string;
  onSearchChange?: (term: string) => void;
}

export function Layout({ searchTerm = '', onSearchChange = () => {} }: LayoutProps) {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'zh' : 'en';
    i18n.changeLanguage(newLang);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center space-x-3">
              <ImageIcon className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">ImageAI</h1>
            </Link>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                <input
                  type="text"
                  placeholder={t('search')}
                  value={searchTerm}
                  onChange={(e) => onSearchChange(e.target.value)}
                  className="pl-10 pr-4 py-2 w-64 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none transition-colors"
                />
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
              <ImageIcon className="h-6 w-6 text-blue-600" />
              <span className="text-xl font-semibold text-gray-900">ImageAI</span>
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