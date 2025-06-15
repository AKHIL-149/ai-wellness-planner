// frontend/src/hooks/useAI.js

import { useState, useCallback, useRef, useEffect } from 'react';
import aiService from '../services/aiService';

export const useAI = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const activeStreamsRef = useRef(new Set());

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      activeStreamsRef.current.forEach(streamId => {
        aiService.cancelStream(streamId);
      });
    };
  }, []);

  const startChat = useCallback(async (message, chatType = 'general', context = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await aiService.startNewChat(message, chatType, context);
      if (!result.success) {
        setError(result.error);
      }
      return result;
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (sessionId, message, context = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await aiService.sendMessage(sessionId, message, context);
      if (!result.success) {
        setError(result.error);
      }
      return result;
    } finally {
      setLoading(false);
    }
  }, []);

  const streamMessage = useCallback(async (sessionId, message, onUpdate, context = {}) => {
    setError(null);
    
    const result = await aiService.streamMessage(sessionId, message, onUpdate, context);
    
    if (result.success) {
      activeStreamsRef.current.add(result.streamId);
    } else {
      setError(result.error);
    }
    
    return result;
  }, []);

  const cancelStream = useCallback((streamId) => {
    const cancelled = aiService.cancelStream(streamId);
    if (cancelled) {
      activeStreamsRef.current.delete(streamId);
    }
    return cancelled;
  }, []);

  const generateMealPlan = useCallback(async (preferences) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await aiService.generateMealPlan(preferences);
      if (!result.success) {
        setError(result.error);
      }
      return result;
    } finally {
      setLoading(false);
    }
  }, []);

  const generateWorkoutPlan = useCallback(async (preferences) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await aiService.generateWorkoutPlan(preferences);
      if (!result.success) {
        setError(result.error);
      }
      return result;
    } finally {
      setLoading(false);
    }
  }, []);

  const addFeedback = useCallback(async (messageId, rating, feedback = '') => {
    try {
      const result = await aiService.addMessageFeedback(messageId, rating, feedback);
      if (!result.success) {
        setError(result.error);
      }
      return result;
    } catch (err) {
      setError('Failed to submit feedback');
      return { success: false, error: 'Failed to submit feedback' };
    }
  }, []);

  return {
    loading,
    error,
    setError,
    startChat,
    sendMessage,
    streamMessage,
    cancelStream,
    generateMealPlan,
    generateWorkoutPlan,
    addFeedback,
    activeStreams: Array.from(activeStreamsRef.current),
  };
};