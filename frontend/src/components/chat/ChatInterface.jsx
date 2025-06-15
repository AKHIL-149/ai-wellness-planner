// frontend/src/components/chat/ChatInterface.jsx

import React, { useState, useEffect, useRef } from 'react';
import { useAI } from '../../hooks/useAI';
import MessageBubble from './MessageBubble';
import StreamingResponse from './StreamingResponse';
import AIThinking from './AIThinking';
import Button from '../common/Button';
import Input from '../common/Input';
import { PaperAirplaneIcon, PlusIcon } from '@heroicons/react/24/outline';

const ChatInterface = ({ sessionId: initialSessionId, onSessionChange }) => {
  const [sessionId, setSessionId] = useState(initialSessionId);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState(null);
  const [streamingContent, setStreamingContent] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const { streamMessage, startChat, loading, error } = useAI();

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSendMessage = async (message = inputValue.trim()) => {
    if (!message || isStreaming) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsStreaming(true);
    setStreamingContent('');

    try {
      if (!sessionId) {
        // Start new chat session
        const result = await startChat(message, 'general');
        if (result.success) {
          setSessionId(result.sessionId);
          onSessionChange?.(result.sessionId);
          
          // Add initial AI response
          const aiMessage = {
            id: result.initialResponse.message_id,
            role: 'assistant',
            content: result.initialResponse.content,
            timestamp: new Date(),
            confidence: result.initialResponse.confidence_score,
            responseTime: result.initialResponse.response_time_ms,
          };
          setMessages(prev => [...prev, aiMessage]);
        }
      } else {
        // Stream message in existing session
        await streamMessage(sessionId, message, (update) => {
          switch (update.type) {
            case 'chunk':
              setStreamingContent(update.fullContent);
              setStreamingMessageId(update.messageId);
              break;
            case 'complete':
              const aiMessage = {
                id: update.messageId,
                role: 'assistant',
                content: update.fullContent,
                timestamp: new Date(),
                metadata: update.metadata,
              };
              setMessages(prev => [...prev, aiMessage]);
              setStreamingContent('');
              setStreamingMessageId(null);
              break;
            case 'error':
              console.error('Streaming error:', update.error);
              const errorMessage = {
                id: `error-${Date.now()}`,
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.',
                timestamp: new Date(),
                isError: true,
              };
              setMessages(prev => [...prev, errorMessage]);
              setStreamingContent('');
              setStreamingMessageId(null);
              break;
          }
        });
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleNewChat = () => {
    setSessionId(null);
    setMessages([]);
    setStreamingContent('');
    setStreamingMessageId(null);
    onSessionChange?.(null);
    inputRef.current?.focus();
  };

  const quickPrompts = [
    "Help me plan a healthy meal for today",
    "Create a workout routine for beginners",
    "What are some good protein sources?",
    "How can I improve my sleep quality?",
  ];

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Chat Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            AI Wellness Coach
          </h2>
          <p className="text-sm text-gray-500">
            Your personal health and fitness assistant
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          icon={PlusIcon}
          onClick={handleNewChat}
        >
          New Chat
        </Button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !streamingContent ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mx-auto mb-4 flex items-center justify-center">
              <span className="text-white font-bold text-xl">AI</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Welcome to your AI Wellness Coach!
            </h3>
            <p className="text-gray-600 mb-6">
              I'm here to help you with nutrition, fitness, and wellness questions.
            </p>
            
            {/* Quick Prompts */}
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700 mb-3">
                Try asking me about:
              </p>
              <div className="grid gap-2">
                {quickPrompts.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => handleSendMessage(prompt)}
                    className="p-3 text-left bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors text-sm border border-gray-200"
                    disabled={isStreaming}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                showTimestamp
              />
            ))}
            
            {isStreaming && (
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-bold text-sm">AI</span>
                </div>
                <div className="flex-1">
                  {streamingContent ? (
                    <StreamingResponse content={streamingContent} />
                  ) : (
                    <AIThinking />
                  )}
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200">
        {error && (
          <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
        
        <div className="flex items-end space-x-3">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about health, nutrition, or fitness..."
              className="w-full resize-none rounded-lg border border-gray-300 px-4 py-3 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-opacity-20"
              rows={1}
              style={{
                minHeight: '44px',
                maxHeight: '120px',
                resize: 'none',
              }}
              disabled={isStreaming}
            />
          </div>
          <Button
            onClick={() => handleSendMessage()}
            disabled={!inputValue.trim() || isStreaming}
            icon={PaperAirplaneIcon}
            className="px-4 py-3"
          >
            Send
          </Button>
        </div>
        
        <div className="mt-2 text-xs text-gray-500 text-center">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;