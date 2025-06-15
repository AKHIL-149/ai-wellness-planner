// frontend/src/utils/formatters.js

import { format, formatDistanceToNow, isToday, isYesterday, parseISO } from 'date-fns';

export const formatters = {
  // Date formatters
  date: (date, formatString = 'MMM dd, yyyy') => {
    if (!date) return '';
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return format(dateObj, formatString);
  },

  time: (date, formatString = 'HH:mm') => {
    if (!date) return '';
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return format(dateObj, formatString);
  },

  dateTime: (date, formatString = 'MMM dd, yyyy HH:mm') => {
    if (!date) return '';
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return format(dateObj, formatString);
  },

  relativeTime: (date) => {
    if (!date) return '';
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    
    if (isToday(dateObj)) {
      return `Today at ${format(dateObj, 'HH:mm')}`;
    }
    if (isYesterday(dateObj)) {
      return `Yesterday at ${format(dateObj, 'HH:mm')}`;
    }
    
    return formatDistanceToNow(dateObj, { addSuffix: true });
  },

  // Number formatters
  number: (value, decimals = 0) => {
    if (value === null || value === undefined) return '0';
    return Number(value).toFixed(decimals);
  },

  currency: (value, currency = 'USD') => {
    if (value === null || value === undefined) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(value);
  },

  percentage: (value, decimals = 1) => {
    if (value === null || value === undefined) return '0%';
    return `${Number(value).toFixed(decimals)}%`;
  },

  // Health/fitness formatters
  calories: (value) => {
    if (value === null || value === undefined) return '0 cal';
    return `${Math.round(value)} cal`;
  },

  weight: (value, unit = 'kg') => {
    if (value === null || value === undefined) return `0 ${unit}`;
    return `${Number(value).toFixed(1)} ${unit}`;
  },

  duration: (minutes) => {
    if (!minutes || minutes === 0) return '0m';
    if (minutes < 60) return `${minutes}m`;
    
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    
    if (mins === 0) return `${hours}h`;
    return `${hours}h ${mins}m`;
  },

  distance: (value, unit = 'km') => {
    if (value === null || value === undefined) return `0 ${unit}`;
    return `${Number(value).toFixed(2)} ${unit}`;
  },

  // Text formatters
  capitalize: (str) => {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
  },

  title: (str) => {
    if (!str) return '';
    return str.replace(/\w\S*/g, (txt) => 
      txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()
    );
  },

  truncate: (str, length = 100) => {
    if (!str) return '';
    if (str.length <= length) return str;
    return str.substring(0, length) + '...';
  },

  // Nutrition formatters
  macros: (protein, carbs, fat) => {
    const total = protein + carbs + fat;
    if (total === 0) return { protein: 0, carbs: 0, fat: 0 };
    
    return {
      protein: Math.round((protein / total) * 100),
      carbs: Math.round((carbs / total) * 100),
      fat: Math.round((fat / total) * 100),
    };
  },

  nutrient: (value, unit = 'g') => {
    if (value === null || value === undefined) return `0${unit}`;
    if (unit === 'g' && value < 1) {
      return `${Math.round(value * 1000)}mg`;
    }
    return `${Math.round(value)}${unit}`;
  },
};