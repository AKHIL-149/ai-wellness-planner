// frontend/src/services/aiService.js

import { chatAPI, nutritionAPI, fitnessAPI, handleAPIError } from './api';

class AIService {
  constructor() {
    this.activeStreams = new Map();
    this.messageQueue = [];
    this.isProcessing = false;
  }

  // Chat-related AI services
  async startNewChat(message, chatType = 'general', context = {}) {
    try {
      const response = await chatAPI.startChat({
        message,
        chat_type: chatType,
        context,
      });

      return {
        success: true,
        sessionId: response.session_id,
        initialResponse: response.initial_response,
        sessionTitle: response.session_title,
      };
    } catch (error) {
      return {
        success: false,
        error: handleAPIError(error, 'Failed to start chat'),
      };
    }
  }

  async sendMessage(sessionId, message, context = {}) {
    try {
      const response = await chatAPI.sendMessage({
        session_id: sessionId,
        message,
        context,
      });

      return {
        success: true,
        userMessageId: response.user_message_id,
        aiResponse: response.ai_response,
      };
    } catch (error) {
      return {
        success: false,
        error: handleAPIError(error, 'Failed to send message'),
      };
    }
  }

  // Streaming message with real-time updates
  async streamMessage(sessionId, message, onUpdate, context = {}) {
    const streamId = `${sessionId}-${Date.now()}`;
    
    try {
      // Track active stream
      this.activeStreams.set(streamId, true);

      let fullResponse = '';
      let currentMessageId = null;

      const onChunk = (data) => {
        if (!this.activeStreams.get(streamId)) {
          return; // Stream was cancelled
        }

        if (data.error) {
          onUpdate({
            type: 'error',
            error: data.error,
            isComplete: true,
          });
          return;
        }

        if (data.message_id && !currentMessageId) {
          currentMessageId = data.message_id;
        }

        if (data.content_chunk) {
          fullResponse += data.content_chunk;
          onUpdate({
            type: 'chunk',
            content: data.content_chunk,
            fullContent: fullResponse,
            messageId: currentMessageId,
            isComplete: false,
          });
        }

        if (data.is_complete) {
          onUpdate({
            type: 'complete',
            fullContent: fullResponse,
            messageId: currentMessageId,
            isComplete: true,
            metadata: data.metadata,
          });
          this.activeStreams.delete(streamId);
        }
      };

      await chatAPI.streamMessage({
        session_id: sessionId,
        message,
        context,
      }, onChunk);

      return {
        success: true,
        streamId,
      };
    } catch (error) {
      this.activeStreams.delete(streamId);
      onUpdate({
        type: 'error',
        error: handleAPIError(error, 'Failed to stream message'),
        isComplete: true,
      });

      return {
        success: false,
        error: handleAPIError(error, 'Failed to stream message'),
      };
    }
  }

  // Cancel active stream
  cancelStream(streamId) {
    if (this.activeStreams.has(streamId)) {
      this.activeStreams.delete(streamId);
      return true;
    }
    return false;
  }

  // Get all active streams
  getActiveStreams() {
    return Array.from(this.activeStreams.keys());
  }

  // Message feedback
  async addMessageFeedback(messageId, rating, feedback = '') {
    try {
      await chatAPI.addMessageFeedback(messageId, {
        rating,
        feedback,
      });

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: handleAPIError(error, 'Failed to submit feedback'),
      };
    }
  }

  // AI-powered meal planning
  async generateMealPlan(preferences) {
    try {
      const response = await nutritionAPI.generateMealPlan(preferences);

      return {
        success: true,
        mealPlan: response.meal_plan,
        confidence: response.ai_confidence,
        planId: response.meal_plan_id,
      };
    } catch (error) {
      return {
        success: false,
        error: handleAPIError(error, 'Failed to generate meal plan'),
      };
    }
  }

  // Stream meal plan generation with progress updates
  async streamMealPlanGeneration(preferences, onUpdate) {
    const streamId = `meal-plan-${Date.now()}`;
    
    try {
      this.activeStreams.set(streamId, true);

      // Simulate streaming for meal plan generation
      // In a real implementation, this would use Server-Sent Events or WebSockets
      const steps = [
        { step: 'analyzing', message: 'Analyzing your preferences...', progress: 10 },
        { step: 'calculating', message: 'Calculating nutritional requirements...', progress: 30 },
        { step: 'searching', message: 'Finding suitable recipes...', progress: 50 },
        { step: 'optimizing', message: 'Optimizing meal combinations...', progress: 70 },
        { step: 'generating', message: 'Generating your personalized plan...', progress: 90 },
      ];

      for (const stepData of steps) {
        if (!this.activeStreams.get(streamId)) break;

        onUpdate({
          type: 'progress',
          ...stepData,
          isComplete: false,
        });

        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      if (this.activeStreams.get(streamId)) {
        const result = await this.generateMealPlan(preferences);
        
        onUpdate({
          type: 'complete',
          ...result,
          progress: 100,
          isComplete: true,
        });
      }

      this.activeStreams.delete(streamId);
      return { success: true, streamId };
    } catch (error) {
      this.activeStreams.delete(streamId);
      onUpdate({
        type: 'error',
        error: handleAPIError(error, 'Failed to generate meal plan'),
        isComplete: true,
      });

      return {
        success: false,
        error: handleAPIError(error, 'Failed to generate meal plan'),
      };
    }
  }

  // AI-powered workout planning
  async generateWorkoutPlan(preferences) {
    try {
      const response = await fitnessAPI.generateWorkoutPlan(preferences);

      return {
        success: true,
        workoutPlan: response.workout_plan,
        confidence: response.ai_confidence,
        planId: response.workout_plan_id,
      };
    } catch (error) {
      return {
        success: false,
        error: handleAPIError(error, 'Failed to generate workout plan'),
      };
    }
  }

  // Stream workout plan generation
  async streamWorkoutPlanGeneration(preferences, onUpdate) {
    const streamId = `workout-plan-${Date.now()}`;
    
    try {
      this.activeStreams.set(streamId, true);

      const steps = [
        { step: 'assessing', message: 'Assessing your fitness level...', progress: 15 },
        { step: 'planning', message: 'Creating workout structure...', progress: 35 },
        { step: 'selecting', message: 'Selecting appropriate exercises...', progress: 55 },
        { step: 'balancing', message: 'Balancing muscle groups...', progress: 75 },
        { step: 'finalizing', message: 'Finalizing your workout plan...', progress: 95 },
      ];

      for (const stepData of steps) {
        if (!this.activeStreams.get(streamId)) break;

        onUpdate({
          type: 'progress',
          ...stepData,
          isComplete: false,
        });

        await new Promise(resolve => setTimeout(resolve, 800));
      }

      if (this.activeStreams.get(streamId)) {
        const result = await this.generateWorkoutPlan(preferences);
        
        onUpdate({
          type: 'complete',
          ...result,
          progress: 100,
          isComplete: true,
        });
      }

      this.activeStreams.delete(streamId);
      return { success: true, streamId };
    } catch (error) {
      this.activeStreams.delete(streamId);
      onUpdate({
        type: 'error',
        error: handleAPIError(error, 'Failed to generate workout plan'),
        isComplete: true,
      });

      return {
        success: false,
        error: handleAPIError(error, 'Failed to generate workout plan'),
      };
    }
  }

  // Exercise recommendations
  async getExerciseRecommendations(criteria) {
    try {
      const response = await fitnessAPI.searchExercises(criteria);

      return {
        success: true,
        exercises: response.exercises,
        totalCount: response.total_count,
      };
    } catch (error) {
      return {
        success: false,
        error: handleAPIError(error, 'Failed to get exercise recommendations'),
      };
    }
  }

  // Get exercise substitutes
  async getExerciseSubstitutes(exerciseId, reason = '') {
    try {
      const response = await fitnessAPI.getExerciseSubstitutes(exerciseId, reason);

      return {
        success: true,
        originalExercise: response.original_exercise,
        substitutes: response.substitutes,
      };
    } catch (error) {
      return {
        success: false,
        error: handleAPIError(error, 'Failed to get exercise substitutes'),
      };
    }
  }

  // AI insights and analytics
  async getChatInsights(periodDays = 30) {
    try {
      const insights = await chatAPI.getInsights(periodDays);

      return {
        success: true,
        insights,
      };
    } catch (error) {
      return {
        success: false,
        error: handleAPIError(error, 'Failed to get chat insights'),
      };
    }
  }

  async getNutritionInsights() {
    try {
      const insights = await nutritionAPI.getInsights();

      return {
        success: true,
        insights,
      };
    } catch (error) {
      return {
        success: false,
        error: handleAPIError(error, 'Failed to get nutrition insights'),
      };
    }
  }

  async getFitnessInsights() {
    try {
      const insights = await fitnessAPI.getInsights();

      return {
        success: true,
        insights,
      };
    } catch (error) {
      return {
        success: false,
        error: handleAPIError(error, 'Failed to get fitness insights'),
      };
    }
  }

  // Search and data operations
  async searchConversations(query, filters = {}) {
    try {
      const response = await chatAPI.searchConversations({
        query,
        ...filters,
      });

      return {
        success: true,
        results: response.results,
        totalFound: response.total_found,
      };
    } catch (error) {
      return {
        success: false,
        error: handleAPIError(error, 'Failed to search conversations'),
      };
    }
  }

  async exportChatData(options = {}) {
    try {
      const response = await chatAPI.exportChatData(options);

      return {
        success: true,
        data: response.data,
        format: response.format,
        filename: response.filename,
      };
    } catch (error) {
      return {
        success: false,
        error: handleAPIError(error, 'Failed to export chat data'),
      };
    }
  }

  // Utility methods
  formatResponse(response) {
    if (!response || typeof response !== 'object') {
      return { text: String(response || '') };
    }

    // Handle different response types
    if (response.message_type === 'meal_plan') {
      return {
        type: 'meal_plan',
        data: response.structured_data,
        text: response.content,
      };
    }

    if (response.message_type === 'workout_plan') {
      return {
        type: 'workout_plan',
        data: response.structured_data,
        text: response.content,
      };
    }

    if (response.message_type === 'nutrition_analysis') {
      return {
        type: 'nutrition_analysis',
        data: response.structured_data,
        text: response.content,
      };
    }

    return {
      type: 'text',
      text: response.content || String(response),
    };
  }

  getConfidenceLevel(score) {
    if (score >= 0.8) return 'high';
    if (score >= 0.6) return 'medium';
    return 'low';
  }

  getConfidenceColor(score) {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  }

  // Queue management for multiple simultaneous requests
  async queueRequest(requestFn, priority = 'normal') {
    return new Promise((resolve, reject) => {
      this.messageQueue.push({
        requestFn,
        priority,
        resolve,
        reject,
        timestamp: Date.now(),
      });

      this.processQueue();
    });
  }

  async processQueue() {
    if (this.isProcessing || this.messageQueue.length === 0) {
      return;
    }

    this.isProcessing = true;

    // Sort by priority and timestamp
    this.messageQueue.sort((a, b) => {
      const priorityOrder = { high: 3, normal: 2, low: 1 };
      const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
      
      if (priorityDiff !== 0) {
        return priorityDiff;
      }
      
      return a.timestamp - b.timestamp;
    });

    const request = this.messageQueue.shift();

    try {
      const result = await request.requestFn();
      request.resolve(result);
    } catch (error) {
      request.reject(error);
    } finally {
      this.isProcessing = false;
      
      // Process next request after a short delay
      if (this.messageQueue.length > 0) {
        setTimeout(() => this.processQueue(), 100);
      }
    }
  }

  // Cleanup methods
  cleanup() {
    // Cancel all active streams
    this.activeStreams.clear();
    
    // Clear message queue
    this.messageQueue.forEach(request => {
      request.reject(new Error('Service cleanup - request cancelled'));
    });
    this.messageQueue = [];
    
    this.isProcessing = false;
  }

  // Statistics and monitoring
  getStats() {
    return {
      activeStreams: this.activeStreams.size,
      queuedRequests: this.messageQueue.length,
      isProcessing: this.isProcessing,
    };
  }
}

// Create singleton instance
const aiService = new AIService();

export default aiService;

// Export utility functions
export const aiHelpers = {
  // Format streaming text with typing effect
  typewriterEffect: (text, onUpdate, speed = 50) => {
    let index = 0;
    const interval = setInterval(() => {
      if (index <= text.length) {
        onUpdate(text.slice(0, index));
        index++;
      } else {
        clearInterval(interval);
      }
    }, speed);
    
    return () => clearInterval(interval);
  },

  // Parse structured AI responses
  parseStructuredResponse: (response) => {
    try {
      if (typeof response === 'string') {
        // Try to extract JSON from text response
        const jsonMatch = response.match(/```json\n([\s\S]*?)\n```/);
        if (jsonMatch) {
          return JSON.parse(jsonMatch[1]);
        }
        
        // Try to parse as direct JSON
        return JSON.parse(response);
      }
      
      return response;
    } catch {
      return null;
    }
  },

  // Validate AI response quality
  validateResponse: (response) => {
    const issues = [];
    
    if (!response || typeof response !== 'object') {
      issues.push('Invalid response format');
      return { isValid: false, issues };
    }
    
    if (!response.content && !response.structured_data) {
      issues.push('Response contains no content');
    }
    
    if (response.confidence_score !== undefined && response.confidence_score < 0.3) {
      issues.push('Low confidence score');
    }
    
    if (response.content && response.content.length < 10) {
      issues.push('Response too short');
    }
    
    return {
      isValid: issues.length === 0,
      issues,
      quality: issues.length === 0 ? 'good' : 
               issues.length <= 1 ? 'acceptable' : 'poor'
    };
  },

  // Extract actionable items from AI responses
  extractActionItems: (response) => {
    const content = response.content || '';
    const actionItems = [];
    
    // Look for common action patterns
    const patterns = [
      /(?:try|consider|start|begin|add|include|avoid|reduce|increase|track|monitor)[\s\w]*[.!]/gi,
      /(?:you should|you could|i recommend|i suggest)[\s\w]*[.!]/gi,
      /(?:next step|action item|to do|task)[\s:]*[\s\w]*[.!]/gi,
    ];
    
    patterns.forEach(pattern => {
      const matches = content.match(pattern);
      if (matches) {
        actionItems.push(...matches.map(match => match.trim()));
      }
    });
    
    return [...new Set(actionItems)]; // Remove duplicates
  },

  // Generate response summary
  generateSummary: (response, maxLength = 150) => {
    const content = response.content || '';
    
    if (content.length <= maxLength) {
      return content;
    }
    
    // Find the best break point near the maxLength
    const truncated = content.substring(0, maxLength);
    const lastSentence = truncated.lastIndexOf('.');
    const lastSpace = truncated.lastIndexOf(' ');
    
    const breakPoint = lastSentence > maxLength * 0.7 ? lastSentence + 1 : lastSpace;
    
    return content.substring(0, breakPoint) + '...';
  },
};