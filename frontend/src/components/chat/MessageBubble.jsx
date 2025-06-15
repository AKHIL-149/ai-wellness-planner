// frontend/src/components/chat/MessageBubble.jsx

import React, { useState } from 'react';
import { 
  HandThumbUpIcon, 
  HandThumbDownIcon,
  ClipboardDocumentIcon,
  ShareIcon 
} from '@heroicons/react/24/outline';
import { 
  HandThumbUpIcon as HandThumbUpSolid, 
  HandThumbDownIcon as HandThumbDownSolid 
} from '@heroicons/react/24/solid';
import { useAI } from '../../hooks/useAI';
import { formatDistanceToNow } from 'date-fns';

const MessageBubble = ({ message, showTimestamp = false, showActions = true }) => {
  const [feedback, setFeedback] = useState(null);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const { addFeedback } = useAI();

  const isUser = message.role === 'user';
  const isError = message.isError;

  const handleFeedback = async (rating) => {
    if (isUser || feedback) return;

    setFeedback(rating);
    
    try {
      await addFeedback(message.id, rating, feedbackText);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      setFeedback(null);
    }
    
    setShowFeedbackForm(false);
    setFeedbackText('');
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      // You could show a toast notification here
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const formatContent = (content) => {
    // Basic markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex items-start space-x-3 max-w-3xl ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
        {/* Avatar */}
        {!isUser && (
          <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
            isError ? 'bg-red-500' : 'bg-gradient-to-r from-blue-500 to-purple-600'
          }`}>
            <span className="text-white font-bold text-sm">AI</span>
          </div>
        )}
        
        {isUser && (
          <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-sm">You</span>
          </div>
        )}

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div
            className={`rounded-lg px-4 py-3 max-w-none ${
              isUser
                ? 'bg-blue-600 text-white'
                : isError
                ? 'bg-red-50 text-red-900 border border-red-200'
                : 'bg-gray-100 text-gray-900'
            }`}
          >
            <div
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{
                __html: formatContent(message.content)
              }}
            />
            
            {/* Message metadata */}
            {!isUser && message.confidence && (
              <div className="mt-2 pt-2 border-t border-gray-200">
                <div className="flex items-center space-x-2 text-xs text-gray-500">
                  <span>Confidence:</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full"
                      style={{ width: `${message.confidence * 100}%` }}
                    />
                  </div>
                  <span>{Math.round(message.confidence * 100)}%</span>
                </div>
              </div>
            )}
          </div>

          {/* Timestamp */}
          {showTimestamp && (
            <div className={`mt-1 text-xs text-gray-500 ${isUser ? 'text-right' : 'text-left'}`}>
              {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
              {message.responseTime && (
                <span className="ml-2">• {message.responseTime}ms</span>
              )}
            </div>
          )}

          {/* Actions */}
          {showActions && !isUser && !isError && (
            <div className="flex items-center space-x-2 mt-2">
              <button
                onClick={copyToClipboard}
                className="p-1 text-gray-400 hover:text-gray-600 rounded"
                title="Copy to clipboard"
              >
                <ClipboardDocumentIcon className="w-4 h-4" />
              </button>
              
              <button
                onClick={() => setShowFeedbackForm(!showFeedbackForm)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded"
                title="Share"
              >
                <ShareIcon className="w-4 h-4" />
              </button>

              <div className="flex items-center space-x-1 ml-2">
                <button
                  onClick={() => handleFeedback(5)}
                  disabled={!!feedback}
                  className={`p-1 rounded ${
                    feedback === 5
                      ? 'text-green-600'
                      : 'text-gray-400 hover:text-green-600'
                  }`}
                  title="Good response"
                >
                  {feedback === 5 ? (
                    <HandThumbUpSolid className="w-4 h-4" />
                  ) : (
                    <HandThumbUpIcon className="w-4 h-4" />
                  )}
                </button>
                
                <button
                  onClick={() => handleFeedback(1)}
                  disabled={!!feedback}
                  className={`p-1 rounded ${
                    feedback === 1
                      ? 'text-red-600'
                      : 'text-gray-400 hover:text-red-600'
                  }`}
                  title="Poor response"
                >
                  {feedback === 1 ? (
                    <HandThumbDownSolid className="w-4 h-4" />
                  ) : (
                    <HandThumbDownIcon className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Feedback Form */}
          {showFeedbackForm && (
            <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200 w-full max-w-sm">
              <textarea
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                placeholder="Tell us more about this response..."
                className="w-full p-2 text-sm border border-gray-300 rounded resize-none"
                rows={3}
              />
              <div className="flex items-center justify-between mt-2">
                <button
                  onClick={() => setShowFeedbackForm(false)}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Cancel
                </button>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleFeedback(1)}
                    className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                  >
                    Not Helpful
                  </button>
                  <button
                    onClick={() => handleFeedback(5)}
                    className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200"
                  >
                    Helpful
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;