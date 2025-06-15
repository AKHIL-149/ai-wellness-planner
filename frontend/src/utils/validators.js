// frontend/src/utils/validators.js

export const validators = {
  // Basic validators
  required: (value) => {
    if (!value || (typeof value === 'string' && !value.trim())) {
      return 'This field is required';
    }
    return '';
  },

  email: (value) => {
    if (!value) return '';
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      return 'Please enter a valid email address';
    }
    return '';
    },

 password: (value) => {
   if (!value) return '';
   
   const issues = [];
   
   if (value.length < 8) {
     issues.push('at least 8 characters');
   }
   
   if (!/[A-Z]/.test(value)) {
     issues.push('one uppercase letter');
   }
   
   if (!/[a-z]/.test(value)) {
     issues.push('one lowercase letter');
   }
   
   if (!/\d/.test(value)) {
     issues.push('one number');
   }
   
   if (!/[!@#$%^&*(),.?":{}|<>]/.test(value)) {
     issues.push('one special character');
   }
   
   if (issues.length > 0) {
     return `Password must contain ${issues.join(', ')}`;
   }
   
   return '';
 },

 confirmPassword: (value, originalPassword) => {
   if (!value) return '';
   if (value !== originalPassword) {
     return 'Passwords do not match';
   }
   return '';
 },

 minLength: (min) => (value) => {
   if (!value) return '';
   if (value.length < min) {
     return `Must be at least ${min} characters long`;
   }
   return '';
 },

 maxLength: (max) => (value) => {
   if (!value) return '';
   if (value.length > max) {
     return `Must be no more than ${max} characters long`;
   }
   return '';
 },

 // Number validators
 number: (value) => {
   if (!value) return '';
   if (isNaN(Number(value))) {
     return 'Please enter a valid number';
   }
   return '';
 },

 min: (minimum) => (value) => {
   if (!value) return '';
   if (Number(value) < minimum) {
     return `Must be at least ${minimum}`;
   }
   return '';
 },

 max: (maximum) => (value) => {
   if (!value) return '';
   if (Number(value) > maximum) {
     return `Must be no more than ${maximum}`;
   }
   return '';
 },

 range: (min, max) => (value) => {
   if (!value) return '';
   const num = Number(value);
   if (num < min || num > max) {
     return `Must be between ${min} and ${max}`;
   }
   return '';
 },

 // Health-specific validators
 age: (value) => {
   if (!value) return '';
   const num = Number(value);
   if (isNaN(num)) return 'Please enter a valid age';
   if (num < 13 || num > 120) {
     return 'Age must be between 13 and 120';
   }
   return '';
 },

 weight: (value, unit = 'kg') => {
   if (!value) return '';
   const num = Number(value);
   if (isNaN(num)) return 'Please enter a valid weight';
   
   if (unit === 'kg') {
     if (num < 30 || num > 300) {
       return 'Weight must be between 30 and 300 kg';
     }
   } else if (unit === 'lbs') {
     if (num < 66 || num > 660) {
       return 'Weight must be between 66 and 660 lbs';
     }
   }
   return '';
 },

 height: (value, unit = 'cm') => {
   if (!value) return '';
   const num = Number(value);
   if (isNaN(num)) return 'Please enter a valid height';
   
   if (unit === 'cm') {
     if (num < 100 || num > 250) {
       return 'Height must be between 100 and 250 cm';
     }
   } else if (unit === 'ft') {
     if (num < 3 || num > 8) {
       return 'Height must be between 3 and 8 feet';
     }
   }
   return '';
 },

 calories: (value) => {
   if (!value) return '';
   const num = Number(value);
   if (isNaN(num)) return 'Please enter valid calories';
   if (num < 800 || num > 5000) {
     return 'Daily calories should be between 800 and 5000';
   }
   return '';
 },

 // Date validators
 date: (value) => {
   if (!value) return '';
   const date = new Date(value);
   if (isNaN(date.getTime())) {
     return 'Please enter a valid date';
   }
   return '';
 },

 futureDate: (value) => {
   if (!value) return '';
   const date = new Date(value);
   const today = new Date();
   if (date <= today) {
     return 'Date must be in the future';
   }
   return '';
 },

 pastDate: (value) => {
   if (!value) return '';
   const date = new Date(value);
   const today = new Date();
   if (date >= today) {
     return 'Date must be in the past';
   }
   return '';
 },

 // Custom validators
 phone: (value) => {
   if (!value) return '';
   const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
   if (!phoneRegex.test(value.replace(/[\s\-\(\)]/g, ''))) {
     return 'Please enter a valid phone number';
   }
   return '';
 },

 url: (value) => {
   if (!value) return '';
   try {
     new URL(value);
     return '';
   } catch {
     return 'Please enter a valid URL';
   }
 },

 // Composite validators
 combine: (...validators) => (value, formValues) => {
   for (const validator of validators) {
     const error = validator(value, formValues);
     if (error) return error;
   }
   return '';
 },
};