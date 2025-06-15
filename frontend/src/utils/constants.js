// frontend/src/utils/constants.js

export const API_ENDPOINTS = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  AUTH: {
    LOGIN: '/auth/login/',
    REGISTER: '/auth/register/',
    LOGOUT: '/auth/logout/',
    PROFILE: '/auth/profile/',
  },
  NUTRITION: {
    FOODS: '/nutrition/foods/',
    RECIPES: '/nutrition/recipes/',
    MEAL_PLANS: '/nutrition/meal-plans/',
    LOGS: '/nutrition/logs/',
  },
  FITNESS: {
    EXERCISES: '/fitness/exercises/',
    WORKOUTS: '/fitness/workouts/',
    PLANS: '/fitness/workout-plans/',
    GOALS: '/fitness/goals/',
  },
  CHAT: {
    SESSIONS: '/chat/sessions/',
    MESSAGES: '/chat/messages/',
    START: '/chat/start/',
    STREAM: '/chat/stream/',
  },
};

export const USER_ROLES = {
  USER: 'user',
  PREMIUM: 'premium',
  ADMIN: 'admin',
};

export const ACTIVITY_LEVELS = {
  SEDENTARY: 'sedentary',
  LIGHTLY_ACTIVE: 'lightly_active',
  MODERATELY_ACTIVE: 'moderately_active',
  VERY_ACTIVE: 'very_active',
  EXTREMELY_ACTIVE: 'extremely_active',
};

export const FITNESS_GOALS = {
  LOSE_WEIGHT: 'lose_weight',
  MAINTAIN_WEIGHT: 'maintain_weight',
  GAIN_WEIGHT: 'gain_weight',
  BUILD_MUSCLE: 'build_muscle',
  IMPROVE_ENDURANCE: 'improve_endurance',
  GENERAL_FITNESS: 'general_fitness',
};

export const DIETARY_PREFERENCES = {
  BALANCED: 'balanced',
  LOW_CARB: 'low_carb',
  HIGH_PROTEIN: 'high_protein',
  VEGETARIAN: 'vegetarian',
  VEGAN: 'vegan',
  KETO: 'keto',
  PALEO: 'paleo',
  MEDITERRANEAN: 'mediterranean',
};

export const WORKOUT_TYPES = {
  STRENGTH: 'strength',
  CARDIO: 'cardio',
  HIIT: 'hiit',
  YOGA: 'yoga',
  PILATES: 'pilates',
  FUNCTIONAL: 'functional',
  SPORTS: 'sports',
};

export const MEAL_TYPES = {
  BREAKFAST: 'breakfast',
  LUNCH: 'lunch',
  DINNER: 'dinner',
  SNACK: 'snack',
};

export const CHART_COLORS = {
  PRIMARY: '#3B82F6',
  SECONDARY: '#8B5CF6',
  SUCCESS: '#10B981',
  WARNING: '#F59E0B',
  DANGER: '#EF4444',
  INFO: '#06B6D4',
  GRAY: '#6B7280',
};

export const BREAKPOINTS = {
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  '2XL': 1536,
};