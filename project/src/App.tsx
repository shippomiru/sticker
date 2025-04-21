import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Helmet } from 'react-helmet';
import Layout from './components/Layout';
import ImageGrid from './components/ImageGrid';
import ImageDetail from './components/ImageDetail';
import About from './components/About';
import TagPage from './components/TagPage';

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
      <Helmet>
        <title>Free Clipart, PNG & Stickers for Creators – ClipPng</title>
        <meta 
          name="description" 
          content="Browse and download thousands of PNGs, clipart graphics, and stickers for decoration, crafts, digital art, or school projects. All files are free to use." 
        />
        <link rel="canonical" href="https://clippng.online/" />
      </Helmet>
      <Routes>
        <Route path="/" element={<Layout searchTerm={searchTerm} onSearchChange={setSearchTerm} />}>
          <Route index element={
            <ImageGrid 
              searchTerm={searchTerm} 
              selectedTags={selectedTags}
              onTagsChange={setSelectedTags}
            />
          } />
          <Route path="about" element={<About />} />
          <Route path="airplane-clipart" element={<TagPage />} />
          <Route path="apple-clipart" element={<TagPage />} />
          <Route path="baby-clipart" element={<TagPage />} />
          <Route path="bird-clipart" element={<TagPage />} />
          <Route path="birthday-clipart" element={<TagPage />} />
          <Route path="book-clipart" element={<TagPage />} />
          <Route path="camera-clipart" element={<TagPage />} />
          <Route path="car-clipart" element={<TagPage />} />
          <Route path="cat-clipart" element={<TagPage />} />
          <Route path="christmas-clipart" element={<TagPage />} />
          <Route path="crown-png" element={<TagPage />} />
          <Route path="dog-clipart" element={<TagPage />} />
          <Route path="flower-clipart" element={<TagPage />} />
          <Route path="gun-png" element={<TagPage />} />
          <Route path="money-png" element={<TagPage />} />
          <Route path="pumpkin-clipart" element={<TagPage />} />
          <Route path="other-png" element={<TagPage />} />
          <Route path=":slug" element={<ImageDetail onClose={handleDetailClose} />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;