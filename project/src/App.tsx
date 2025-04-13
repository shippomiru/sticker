import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import Layout from './components/Layout';
import ImageGrid from './components/ImageGrid';
import ImageDetail from './components/ImageDetail';
import About from './components/About';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [scrollPosition, setScrollPosition] = useState(0);

  // 监听页面滚动，保存滚动位置
  useEffect(() => {
    const handleScroll = () => {
      setScrollPosition(window.scrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // 从详情页返回时恢复滚动位置
  const handleDetailClose = () => {
    setTimeout(() => {
      window.scrollTo(0, scrollPosition);
    }, 100);
  };

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout searchTerm={searchTerm} onSearchChange={setSearchTerm} />}>
          <Route index element={
            <ImageGrid 
              searchTerm={searchTerm} 
              selectedTags={selectedTags}
              onTagsChange={setSelectedTags}
            />
          } />
          <Route path="/about" element={<About />} />
          <Route path="/:slug" element={<ImageDetail onClose={handleDetailClose} />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;