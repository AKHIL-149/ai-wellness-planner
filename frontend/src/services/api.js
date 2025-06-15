// frontend/src/services/api.js

import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    
    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message);
      return Promise.reject({
        message: 'Network error. Please check your connection.',
        type: 'network_error'
      });
    }
    
    // Handle API errors
    const errorMessage = error.response.data?.message || 
                        error.response.data?.error || 
                        'An unexpected error occurred';
    
    return Promise.reject({
      message: errorMessage,
      status: error.response.status,
      data: error.response.data
    });
  }
);

// API endpoints
export const endpoints = {
  // Authentication
  auth: {
    login: '/auth/login/',
    register: '/auth/register/',
    logout: '/auth/logout/',
    refresh: '/auth/refresh/',
    profile: '/auth/profile/',
  },
  
  // User Management
  users: {
    profile: '/users/profile/',
    goals: '/users/goals/',
    dashboard: '/users/dashboard/',
    insights: '/users/insights/',
  },
  
  // Nutrition
  nutrition: {
    foods: '/nutrition/foods/',
    search: '/nutrition/foods/search/',
    recipes: '/nutrition/recipes/',
    mealPlans: '/nutrition/meal-plans/',
    generatePlan: '/nutrition/meal-plans/generate/',
    nutritionLogs: '/nutrition/logs/',
    dashboard: '/nutrition/dashboard/',
    insights: '/nutrition/insights/',
    groceryLists: '/nutrition/grocery-lists/',
  },
  
  // Fitness
  fitness: {
    exercises: '/fitness/exercises/',
    searchExercises: '/fitness/exercises/search/',
    workoutPlans: '/fitness/workout-plans/',
    generatePlan: '/fitness/workout-plans/generate/',
    workouts: '/fitness/workouts/',
    goals: '/fitness/goals/',
    metrics: '/fitness/metrics/',
    dashboard: '/fitness/dashboard/',
    insights: '/fitness/insights/',
    analytics: '/fitness/analytics/',
  },
  
  // Chat
  chat: {
    sessions: '/chat/sessions/',
    startChat: '/chat/start/',
    sendMessage: '/chat/send/',
    streamMessage: '/chat/stream/',
    messages: '/chat/messages/',
    feedback: '/chat/feedback/',
    dashboard: '/chat/dashboard/',
    insights: '/chat/insights/',
    search: '/chat/search/',
    export: '/chat/export/',
  },
};

// Helper functions for common API patterns
export const apiHelpers = {
  // GET request with optional query params
  get: async (endpoint, params = {}) => {
    try {
      const response = await api.get(endpoint, { params });
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // POST request
  post: async (endpoint, data = {}) => {
    try {
      const response = await api.post(endpoint, data);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // PUT request
  put: async (endpoint, data = {}) => {
    try {
      const response = await api.put(endpoint, data);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // PATCH request
  patch: async (endpoint, data = {}) => {
    try {
      const response = await api.patch(endpoint, data);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // DELETE request
  delete: async (endpoint) => {
    try {
      const response = await api.delete(endpoint);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // Upload file
  upload: async (endpoint, formData, onProgress = null) => {
    try {
      const response = await api.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: onProgress ? (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        } : undefined,
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // Streaming request for real-time data
  stream: async (endpoint, data = {}, onChunk = null) => {
    try {
      const response = await api.post(endpoint, data, {
        responseType: 'stream',
        headers: {
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
      });
      
      if (onChunk && response.data) {
        const reader = response.data.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                onChunk(data);
                
                if (data.is_complete) {
                  return;
                }
              } catch (e) {
                console.warn('Failed to parse streaming data:', line);
              }
            }
          }
        }
      }
      
      return response.data;
    } catch (error) {
      throw error;
    }
  },
};

// Specific API service functions
export const authAPI = {
  login: (credentials) => apiHelpers.post(endpoints.auth.login, credentials),
  register: (userData) => apiHelpers.post(endpoints.auth.register, userData),
  logout: () => apiHelpers.post(endpoints.auth.logout),
  getProfile: () => apiHelpers.get(endpoints.auth.profile),
  updateProfile: (data) => apiHelpers.patch(endpoints.auth.profile, data),
};

export const nutritionAPI = {
  searchFoods: (query) => apiHelpers.get(endpoints.nutrition.search, { q: query }),
  getFoods: (params) => apiHelpers.get(endpoints.nutrition.foods, params),
  getRecipes: (params) => apiHelpers.get(endpoints.nutrition.recipes, params),
  createRecipe: (data) => apiHelpers.post(endpoints.nutrition.recipes, data),
  
  getMealPlans: (params) => apiHelpers.get(endpoints.nutrition.mealPlans, params),
  generateMealPlan: (data) => apiHelpers.post(endpoints.nutrition.generatePlan, data),
  activateMealPlan: (id) => apiHelpers.post(`${endpoints.nutrition.mealPlans}${id}/activate/`),
  
  getNutritionLogs: (params) => apiHelpers.get(endpoints.nutrition.nutritionLogs, params),
  createNutritionLog: (data) => apiHelpers.post(endpoints.nutrition.nutritionLogs, data),
  
  getDashboard: () => apiHelpers.get(endpoints.nutrition.dashboard),
  getInsights: () => apiHelpers.get(endpoints.nutrition.insights),
  
  getGroceryLists: () => apiHelpers.get(endpoints.nutrition.groceryLists),
  generateGroceryList: (mealPlanId) => apiHelpers.post(
    `${endpoints.nutrition.mealPlans}${mealPlanId}/grocery-list/`
  ),
};

export const fitnessAPI = {
  getExercises: (params) => apiHelpers.get(endpoints.fitness.exercises, params),
  searchExercises: (data) => apiHelpers.post(endpoints.fitness.searchExercises, data),
  getExerciseSubstitutes: (exerciseId, reason) => apiHelpers.get(
    `${endpoints.fitness.exercises}${exerciseId}/substitutes/`,
    { reason }
  ),
  
  getWorkoutPlans: (params) => apiHelpers.get(endpoints.fitness.workoutPlans, params),
  generateWorkoutPlan: (data) => apiHelpers.post(endpoints.fitness.generatePlan, data),
  activateWorkoutPlan: (id) => apiHelpers.post(`${endpoints.fitness.workoutPlans}${id}/activate/`),
  optimizeWorkoutPlan: (id, criteria) => apiHelpers.post(
    `${endpoints.fitness.workoutPlans}${id}/optimize/`,
    criteria
  ),
  
  getWorkouts: (params) => apiHelpers.get(endpoints.fitness.workouts, params),
  createWorkout: (data) => apiHelpers.post(endpoints.fitness.workouts, data),
  startWorkout: (id) => apiHelpers.post(`${endpoints.fitness.workouts}${id}/start/`),
  completeWorkout: (id, data) => apiHelpers.post(`${endpoints.fitness.workouts}${id}/complete/`, data),
  trackProgress: (id, progressData) => apiHelpers.post(
    `${endpoints.fitness.workouts}${id}/track-progress/`,
    progressData
  ),
  
  getFitnessGoals: (params) => apiHelpers.get(endpoints.fitness.goals, params),
  createFitnessGoal: (data) => apiHelpers.post(endpoints.fitness.goals, data),
  updateGoalProgress: (id, progress) => apiHelpers.post(
    `${endpoints.fitness.goals}${id}/update-progress/`,
    progress
  ),
  
  getFitnessMetrics: (params) => apiHelpers.get(endpoints.fitness.metrics, params),
  createFitnessMetric: (data) => apiHelpers.post(endpoints.fitness.metrics, data),
  getMetricTrends: (metricType, days = 90) => apiHelpers.get(
    `${endpoints.fitness.metrics}trends/`,
    { metric_type: metricType, days }
  ),
  
  getDashboard: () => apiHelpers.get(endpoints.fitness.dashboard),
  getInsights: () => apiHelpers.get(endpoints.fitness.insights),
  getAnalytics: (period = 'month') => apiHelpers.get(endpoints.fitness.analytics, { period }),
};

export const chatAPI = {
  getSessions: (params) => apiHelpers.get(endpoints.chat.sessions, params),
  createSession: (data) => apiHelpers.post(endpoints.chat.sessions, data),
  archiveSession: (id) => apiHelpers.post(`${endpoints.chat.sessions}${id}/archive/`),
  getSessionMessages: (id, params) => apiHelpers.get(
    `${endpoints.chat.sessions}${id}/messages/`,
    params
  ),
  
  startChat: (data) => apiHelpers.post(endpoints.chat.startChat, data),
  sendMessage: (data) => apiHelpers.post(endpoints.chat.sendMessage, data),
  streamMessage: (data, onChunk) => apiHelpers.stream(endpoints.chat.streamMessage, data, onChunk),
  
  addMessageFeedback: (messageId, feedback) => apiHelpers.post(
    `${endpoints.chat.messages}${messageId}/add-feedback/`,
    feedback
  ),
  
  getDashboard: () => apiHelpers.get(endpoints.chat.dashboard),
  getInsights: (periodDays = 30) => apiHelpers.get(endpoints.chat.insights, { period_days: periodDays }),
  
  searchConversations: (data) => apiHelpers.post(endpoints.chat.search, data),
  exportChatData: (data) => apiHelpers.post(endpoints.chat.export, data),
};

// Error handling utilities
export const handleAPIError = (error, defaultMessage = 'An error occurred') => {
  if (error.type === 'network_error') {
    return 'Please check your internet connection and try again.';
  }
  
  if (error.status === 400) {
    return error.message || 'Invalid request. Please check your input.';
  }
  
  if (error.status === 403) {
    return 'You do not have permission to perform this action.';
  }
  
  if (error.status === 404) {
    return 'The requested resource was not found.';
  }
  
  if (error.status === 500) {
    return 'Server error. Please try again later.';
  }
  
  return error.message || defaultMessage;
};

// Cache utilities for performance
export const cache = {
  get: (key) => {
    try {
      const item = localStorage.getItem(`cache_${key}`);
      if (!item) return null;
      
      const { data, expiry } = JSON.parse(item);
      if (Date.now() > expiry) {
        localStorage.removeItem(`cache_${key}`);
        return null;
      }
      
      return data;
    } catch {
      return null;
    }
  },
  
  set: (key, data, ttl = 300000) => { // 5 minutes default
    try {
      const item = {
        data,
        expiry: Date.now() + ttl,
      };
      localStorage.setItem(`cache_${key}`, JSON.stringify(item));
    } catch (error) {
      console.warn('Cache storage failed:', error);
    }
  },
  
  clear: (key) => {
    localStorage.removeItem(`cache_${key}`);
  },
  
  clearAll: () => {
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('cache_')) {
        localStorage.removeItem(key);
      }
    });
  },
};

export default api;