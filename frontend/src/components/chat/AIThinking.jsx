// frontend/src/components/chat/AIThinking.jsx

import React from 'react';

const AIThinking = () => {
  return (
    <div className="bg-gray-100 rounded-lg px-4 py-3">
      <div className="flex items-center space-x-2">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
        <span className="text-sm text-gray-500">AI is thinking...</span>
      </div>
    </div>
  );
};

export default AIThinking;