// frontend/src/components/chat/StreamingResponse.jsx

import React, { useState, useEffect } from 'react';
import { aiHelpers } from '../../services/aiService';

const StreamingResponse = ({ content, showCursor = true }) => {
  const [displayedContent, setDisplayedContent] = useState('');
  const [isTyping, setIsTyping] = useState(true);

  useEffect(() => {
    if (!content) return;

    // If content is complete, show it all immediately
    if (content.length <= displayedContent.length) {
      setDisplayedContent(content);
      setIsTyping(false);
      return;
    }

    // Typewriter effect for new content
    const timeout = setTimeout(() => {
      if (displayedContent.length < content.length) {
        setDisplayedContent(content.slice(0, displayedContent.length + 1));
      } else {
        setIsTyping(false);
      }
    }, 30); // Adjust typing speed here

    return () => clearTimeout(timeout);
  }, [content, displayedContent]);

  const formatContent = (text) => {
    // Basic markdown-like formatting
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  };

  return (
    <div className="bg-gray-100 rounded-lg px-4 py-3">
      <div
        className="prose prose-sm max-w-none"
        dangerouslySetInnerHTML={{
          __html: formatContent(displayedContent)
        }}
      />
      
      {showCursor && isTyping && (
        <span className="inline-block w-2 h-4 bg-blue-600 ml-1 animate-pulse" />
      )}
      
      {/* Show structured data if available */}
      {content.includes('```json') && (
        <div className="mt-3 p-3 bg-white rounded border border-gray-200">
          <div className="text-xs font-medium text-gray-500 mb-2">
            Structured Data:
          </div>
          <pre className="text-xs text-gray-700 overflow-x-auto">
            {JSON.stringify(aiHelpers.parseStructuredResponse(content), null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default StreamingResponse;