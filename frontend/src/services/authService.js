// frontend/src/services/authService.js

import { authAPI, handleAPIError } from './api';

class AuthService {
  constructor() {
    this.token = localStorage.getItem('authToken');
    this.user = this.getStoredUser();
    this.listeners = new Set();
  }

  // Event system for auth state changes
  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify(event, data = null) {
    this.listeners.forEach(listener => {
      try {
        listener(event, data);
      } catch (error) {
        console.error('Auth listener error:', error);
      }
    });
  }

  // Token management
  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('authToken', token);
    } else {
      localStorage.removeItem('authToken');
    }
  }

  getToken() {
    return this.token || localStorage.getItem('authToken');
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('authToken');
  }

  // User data management
  setUser(user) {
    this.user = user;
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    } else {
      localStorage.removeItem('user');
    }
    this.notify('userChanged', user);
  }

  getUser() {
    return this.user || this.getStoredUser();
  }

  getStoredUser() {
    try {
      const stored = localStorage.getItem('user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  }

  clearUser() {
    this.user = null;
    localStorage.removeItem('user');
    this.notify('userChanged', null);
  }

  // Authentication state
  isAuthenticated() {
    return !!(this.getToken() && this.getUser());
  }

  // Login
  async login(credentials) {
    try {
      const response = await authAPI.login(credentials);
      
      if (response.access_token || response.token) {
        const token = response.access_token || response.token;
        this.setToken(token);
        
        // Fetch user profile after login
        const userProfile = await this.fetchUserProfile();
        
        this.notify('loginSuccess', userProfile);
        
        return {
          success: true,
          user: userProfile,
          token
        };
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      const message = handleAPIError(error, 'Login failed');
      this.notify('loginError', message);
      
      return {
        success: false,
        error: message
      };
    }
  }

  // Register
  async register(userData) {
    try {
      const response = await authAPI.register(userData);
      
      if (response.access_token || response.token) {
        const token = response.access_token || response.token;
        this.setToken(token);
        
        // Fetch user profile after registration
        const userProfile = await this.fetchUserProfile();
        
        this.notify('registerSuccess', userProfile);
        
        return {
          success: true,
          user: userProfile,
          token
        };
      } else {
        // Registration successful but may need email verification
        this.notify('registerSuccess', response);
        
        return {
          success: true,
          message: response.message || 'Registration successful',
          requiresVerification: !response.access_token
        };
      }
    } catch (error) {
      const message = handleAPIError(error, 'Registration failed');
      this.notify('registerError', message);
      
      return {
        success: false,
        error: message
      };
    }
  }

  // Logout
  async logout() {
    try {
      // Call logout endpoint if user is authenticated
      if (this.isAuthenticated()) {
        await authAPI.logout();
      }
    } catch (error) {
      console.warn('Logout API call failed:', error);
      // Continue with local logout even if API call fails
    } finally {
      // Clear local storage regardless of API success
      this.clearToken();
      this.clearUser();
      this.notify('logout');
    }
  }

  // Fetch user profile
  async fetchUserProfile() {
    try {
      const userProfile = await authAPI.getProfile();
      this.setUser(userProfile);
      return userProfile;
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      // Don't clear auth on profile fetch failure
      return this.getUser();
    }
  }

  // Update user profile
  async updateProfile(updates) {
    try {
      const updatedProfile = await authAPI.updateProfile(updates);
      this.setUser(updatedProfile);
      this.notify('profileUpdated', updatedProfile);
      
      return {
        success: true,
        user: updatedProfile
      };
    } catch (error) {
      const message = handleAPIError(error, 'Profile update failed');
      
      return {
        success: false,
        error: message
      };
    }
  }

  // Token refresh (if your API supports it)
  async refreshToken() {
    try {
      const response = await authAPI.refresh();
      
      if (response.access_token || response.token) {
        const token = response.access_token || response.token;
        this.setToken(token);
        this.notify('tokenRefreshed', token);
        return token;
      }
      
      throw new Error('No token in refresh response');
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Clear auth on refresh failure
      this.clearToken();
      this.clearUser();
      this.notify('tokenExpired');
      throw error;
    }
  }

  // Auto-refresh token before expiration
  setupTokenRefresh() {
    if (!this.getToken()) return;

    // Decode JWT to get expiration (basic implementation)
    try {
      const token = this.getToken();
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // Convert to milliseconds
      const now = Date.now();
      const timeUntilExpiry = exp - now;
      
      // Refresh 5 minutes before expiration
      const refreshTime = timeUntilExpiry - (5 * 60 * 1000);
      
      if (refreshTime > 0) {
        setTimeout(async () => {
          try {
            await this.refreshToken();
            this.setupTokenRefresh(); // Setup next refresh
          } catch (error) {
            console.error('Auto token refresh failed:', error);
          }
        }, refreshTime);
      } else {
        // Token already expired or expires soon
        this.refreshToken().catch(() => {
          // Handle refresh failure
          this.logout();
        });
      }
    } catch (error) {
      console.warn('Failed to setup token refresh:', error);
    }
  }

  // Initialize auth service
  async initialize() {
    const token = this.getToken();
    const user = this.getUser();
    
    if (token && user) {
      try {
        // Verify token is still valid by fetching profile
        await this.fetchUserProfile();
        this.setupTokenRefresh();
        this.notify('initialized', user);
        return true;
      } catch (error) {
        console.warn('Token validation failed during initialization:', error);
        this.clearToken();
        this.clearUser();
        this.notify('initializationFailed');
        return false;
      }
    }
    
    this.notify('initialized', null);
    return false;
  }

  // Utility methods
  hasRole(role) {
    const user = this.getUser();
    return user?.roles?.includes(role) || user?.role === role;
  }

  hasPermission(permission) {
    const user = this.getUser();
    return user?.permissions?.includes(permission);
  }

  isProfileComplete() {
    const user = this.getUser();
    if (!user) return false;

    // Check for required profile fields
    const requiredFields = ['first_name', 'last_name', 'email'];
    return requiredFields.every(field => user[field]);
  }

  getProfileCompletionStatus() {
    const user = this.getUser();
    if (!user) return { complete: false, missing: [] };

    const allFields = [
      'first_name',
      'last_name', 
      'email',
      'date_of_birth',
      'gender',
      'height',
      'weight',
      'activity_level',
      'health_goals'
    ];

    const missing = allFields.filter(field => !user[field]);
    const complete = missing.length === 0;
    const completionPercentage = ((allFields.length - missing.length) / allFields.length) * 100;

    return {
      complete,
      missing,
      completionPercentage: Math.round(completionPercentage)
    };
  }

  // Error handling helpers
  isAuthError(error) {
    return error.status === 401 || error.status === 403;
  }

  handleAuthError(error) {
    if (error.status === 401) {
      this.logout();
      return 'Your session has expired. Please log in again.';
    }
    
    if (error.status === 403) {
      return 'You do not have permission to access this resource.';
    }
    
    return handleAPIError(error);
  }
}

// Create singleton instance
const authService = new AuthService();

// Export both the instance and class for flexibility
export default authService;
export { AuthService };

// React hook for using auth service
export const useAuthService = () => {
  return authService;
};

// Helper functions for common auth operations
export const authHelpers = {
  // Format user display name
  getUserDisplayName: (user) => {
    if (!user) return 'Guest';
    
    if (user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    
    if (user.first_name) {
      return user.first_name;
    }
    
    if (user.username) {
      return user.username;
    }
    
    return user.email || 'User';
  },

  // Get user initials for avatar
  getUserInitials: (user) => {
    if (!user) return 'G';
    
    if (user.first_name && user.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    
    if (user.first_name) {
      return user.first_name[0].toUpperCase();
    }
    
    if (user.username) {
      return user.username.slice(0, 2).toUpperCase();
    }
    
    if (user.email) {
      return user.email[0].toUpperCase();
    }
    
    return 'U';
  },

  // Validate email format
  isValidEmail: (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },

  // Validate password strength
  validatePassword: (password) => {
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    
    const issues = [];
    
    if (password.length < minLength) {
      issues.push(`Password must be at least ${minLength} characters long`);
    }
    
    if (!hasUpperCase) {
      issues.push('Password must contain at least one uppercase letter');
    }
    
    if (!hasLowerCase) {
      issues.push('Password must contain at least one lowercase letter');
    }
    
    if (!hasNumbers) {
      issues.push('Password must contain at least one number');
    }
    
    if (!hasSpecialChar) {
      issues.push('Password must contain at least one special character');
    }
    
    return {
      isValid: issues.length === 0,
      issues,
      strength: issues.length === 0 ? 'strong' : 
                issues.length <= 2 ? 'medium' : 'weak'
    };
  },

  // Generate secure password
  generatePassword: (length = 12) => {
    const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const lowercase = 'abcdefghijklmnopqrstuvwxyz';
    const numbers = '0123456789';
    const symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?';
    
    const allChars = uppercase + lowercase + numbers + symbols;
    let password = '';
    
    // Ensure at least one character from each category
    password += uppercase[Math.floor(Math.random() * uppercase.length)];
    password += lowercase[Math.floor(Math.random() * lowercase.length)];
    password += numbers[Math.floor(Math.random() * numbers.length)];
    password += symbols[Math.floor(Math.random() * symbols.length)];
    
    // Fill remaining length with random characters
    for (let i = password.length; i < length; i++) {
      password += allChars[Math.floor(Math.random() * allChars.length)];
    }
    
    // Shuffle the password
    return password.split('').sort(() => Math.random() - 0.5).join('');
  },
};