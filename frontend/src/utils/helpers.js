// frontend/src/utils/helpers.js

import { ACTIVITY_LEVELS, FITNESS_GOALS } from './constants';

export const helpers = {
 // Health calculations
 calculateBMI: (weight, height, weightUnit = 'kg', heightUnit = 'cm') => {
   if (!weight || !height) return 0;
   
   // Convert to metric if needed
   const weightKg = weightUnit === 'lbs' ? weight * 0.453592 : weight;
   const heightM = heightUnit === 'ft' ? height * 0.3048 : 
                   heightUnit === 'in' ? height * 0.0254 : height / 100;
   
   return weightKg / (heightM * heightM);
 },

 getBMICategory: (bmi) => {
   if (bmi < 18.5) return { category: 'Underweight', color: 'text-blue-600' };
   if (bmi < 25) return { category: 'Normal weight', color: 'text-green-600' };
   if (bmi < 30) return { category: 'Overweight', color: 'text-yellow-600' };
   return { category: 'Obese', color: 'text-red-600' };
 },

 calculateBMR: (weight, height, age, gender, weightUnit = 'kg', heightUnit = 'cm') => {
   if (!weight || !height || !age || !gender) return 0;
   
   // Convert to metric if needed
   const weightKg = weightUnit === 'lbs' ? weight * 0.453592 : weight;
   const heightCm = heightUnit === 'ft' ? height * 30.48 : 
                    heightUnit === 'in' ? height * 2.54 : height;
   
   // Mifflin-St Jeor Equation
   const bmr = (10 * weightKg) + (6.25 * heightCm) - (5 * age);
   return gender.toLowerCase() === 'male' ? bmr + 5 : bmr - 161;
 },

 calculateTDEE: (bmr, activityLevel) => {
   const multipliers = {
     [ACTIVITY_LEVELS.SEDENTARY]: 1.2,
     [ACTIVITY_LEVELS.LIGHTLY_ACTIVE]: 1.375,
     [ACTIVITY_LEVELS.MODERATELY_ACTIVE]: 1.55,
     [ACTIVITY_LEVELS.VERY_ACTIVE]: 1.725,
     [ACTIVITY_LEVELS.EXTREMELY_ACTIVE]: 1.9,
   };
   
   return bmr * (multipliers[activityLevel] || 1.2);
 },

 calculateCalorieGoal: (tdee, goal) => {
   const adjustments = {
     [FITNESS_GOALS.LOSE_WEIGHT]: -500, // 1 lb per week
     [FITNESS_GOALS.MAINTAIN_WEIGHT]: 0,
     [FITNESS_GOALS.GAIN_WEIGHT]: 500, // 1 lb per week
     [FITNESS_GOALS.BUILD_MUSCLE]: 300,
   };
   
   return tdee + (adjustments[goal] || 0);
 },

 calculateMacros: (calories, goal) => {
   const ratios = {
     [FITNESS_GOALS.LOSE_WEIGHT]: { protein: 0.35, carbs: 0.35, fat: 0.3 },
     [FITNESS_GOALS.MAINTAIN_WEIGHT]: { protein: 0.25, carbs: 0.45, fat: 0.3 },
     [FITNESS_GOALS.GAIN_WEIGHT]: { protein: 0.25, carbs: 0.5, fat: 0.25 },
     [FITNESS_GOALS.BUILD_MUSCLE]: { protein: 0.35, carbs: 0.4, fat: 0.25 },
   };
   
   const ratio = ratios[goal] || ratios[FITNESS_GOALS.MAINTAIN_WEIGHT];
   
   return {
     protein: Math.round((calories * ratio.protein) / 4), // 4 cal per gram
     carbs: Math.round((calories * ratio.carbs) / 4), // 4 cal per gram
     fat: Math.round((calories * ratio.fat) / 9), // 9 cal per gram
   };
 },

 // Data processing helpers
 groupBy: (array, key) => {
   return array.reduce((groups, item) => {
     const group = key instanceof Function ? key(item) : item[key];
     groups[group] = groups[group] || [];
     groups[group].push(item);
     return groups;
   }, {});
 },

 sortBy: (array, key, direction = 'asc') => {
   return [...array].sort((a, b) => {
     const aVal = key instanceof Function ? key(a) : a[key];
     const bVal = key instanceof Function ? key(b) : b[key];
     
     if (direction === 'desc') {
       return bVal > aVal ? 1 : -1;
     }
     return aVal > bVal ? 1 : -1;
   });
 },

 filterBy: (array, filters) => {
   return array.filter(item => {
     return Object.entries(filters).every(([key, value]) => {
       if (value === null || value === undefined || value === '') return true;
       
       if (Array.isArray(value)) {
         return value.includes(item[key]);
       }
       
       if (typeof value === 'string') {
         return item[key]?.toString().toLowerCase().includes(value.toLowerCase());
       }
       
       return item[key] === value;
     });
   });
 },

 // Chart data helpers
 generateChartData: (data, xKey, yKey, groupKey = null) => {
   if (groupKey) {
     const groups = helpers.groupBy(data, groupKey);
     return Object.entries(groups).map(([group, items]) => ({
       name: group,
       data: items.map(item => ({
         x: item[xKey],
         y: item[yKey],
       })),
     }));
   }
   
   return data.map(item => ({
     x: item[xKey],
     y: item[yKey],
   }));
 },

 // Progress helpers
 calculateProgress: (current, target) => {
   if (!target || target === 0) return 0;
   return Math.min((current / target) * 100, 100);
 },

 getProgressColor: (percentage) => {
   if (percentage >= 90) return 'text-green-600';
   if (percentage >= 70) return 'text-yellow-600';
   if (percentage >= 50) return 'text-orange-600';
   return 'text-red-600';
 },

 // String helpers
 generateSlug: (text) => {
   return text
     .toLowerCase()
     .replace(/[^\w\s-]/g, '')
     .replace(/[\s_-]+/g, '-')
     .replace(/^-+|-+$/g, '');
 },

 generateInitials: (name) => {
   if (!name) return '';
   return name
     .split(' ')
     .map(word => word.charAt(0).toUpperCase())
     .join('')
     .slice(0, 2);
 },

 // Color helpers
 hexToRgb: (hex) => {
   const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
   return result ? {
     r: parseInt(result[1], 16),
     g: parseInt(result[2], 16),
     b: parseInt(result[3], 16)
   } : null;
 },

 rgbToHex: (r, g, b) => {
   return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
 },

 // Storage helpers
 setLocalStorage: (key, value) => {
   try {
     localStorage.setItem(key, JSON.stringify(value));
   } catch (error) {
     console.warn('Failed to set localStorage:', error);
   }
 },

 getLocalStorage: (key, defaultValue = null) => {
   try {
     const item = localStorage.getItem(key);
     return item ? JSON.parse(item) : defaultValue;
   } catch (error) {
     console.warn('Failed to get localStorage:', error);
     return defaultValue;
   }
 },

 removeLocalStorage: (key) => {
   try {
     localStorage.removeItem(key);
   } catch (error) {
     console.warn('Failed to remove localStorage:', error);
   }
 },

 // Debounce helper
 debounce: (func, wait) => {
   let timeout;
   return function executedFunction(...args) {
     const later = () => {
       clearTimeout(timeout);
       func(...args);
     };
     clearTimeout(timeout);
     timeout = setTimeout(later, wait);
   };
 },

 // URL helpers
 buildQueryString: (params) => {
   const queryParams = new URLSearchParams();
   
   Object.entries(params).forEach(([key, value]) => {
     if (value !== null && value !== undefined && value !== '') {
       if (Array.isArray(value)) {
         value.forEach(v => queryParams.append(key, v));
       } else {
         queryParams.append(key, value.toString());
       }
     }
   });
   
   return queryParams.toString();
 },

 parseQueryString: (queryString) => {
   const params = new URLSearchParams(queryString);
   const result = {};
   
   for (const [key, value] of params.entries()) {
     if (result[key]) {
       if (Array.isArray(result[key])) {
         result[key].push(value);
       } else {
         result[key] = [result[key], value];
       }
     } else {
       result[key] = value;
     }
   }
   
   return result;
 },

 // File helpers
 formatFileSize: (bytes) => {
   if (bytes === 0) return '0 Bytes';
   
   const k = 1024;
   const sizes = ['Bytes', 'KB', 'MB', 'GB'];
   const i = Math.floor(Math.log(bytes) / Math.log(k));
   
   return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
 },

 isValidImageType: (file) => {
   const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
   return validTypes.includes(file.type);
 },

 // Error helpers
 getErrorMessage: (error, defaultMessage = 'An error occurred') => {
   if (typeof error === 'string') return error;
   if (error?.message) return error.message;
   if (error?.error) return error.error;
   if (error?.data?.message) return error.data.message;
   return defaultMessage;
 },
};