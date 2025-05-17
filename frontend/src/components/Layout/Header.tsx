import React from 'react';
import { ImageIcon } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <header className="bg-gray-800 py-4 px-6 border-b border-gray-700">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ImageIcon className="h-6 w-6 text-blue-400" />
          <h1 className="text-xl font-bold text-white">Image Analyzer</h1>
        </div>
        <div className="text-sm text-gray-400">
          Powered by AI Vision
        </div>
      </div>
    </header>
  );
};

export default Header;