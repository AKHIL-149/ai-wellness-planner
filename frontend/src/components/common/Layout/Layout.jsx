// frontend/src/components/layout/Layout.jsx

import React from 'react';
import Header from '../common/Header';
import Sidebar from './Sidebar';
import { useMediaQuery } from '../../hooks/useMediaQuery';

const Layout = ({ children }) => {
  const isMobile = useMediaQuery('(max-width: 768px)');

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="flex">
        {!isMobile && (
          <div className="w-64 bg-white shadow-sm border-r border-gray-200">
            <Sidebar />
          </div>
        )}
        
        <main className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;