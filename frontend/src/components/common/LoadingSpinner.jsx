// frontend/src/components/common/LoadingSpinner.jsx

import React from 'react';

const LoadingSpinner = ({ 
  size = 'md', 
  color = 'blue', 
  text = '', 
  className = '',
  fullScreen = false 
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  };

  const colorClasses = {
    blue: 'text-blue-600',
    purple: 'text-purple-600',
    green: 'text-green-600',
    red: 'text-red-600',
    gray: 'text-gray-600',
  };

  const spinnerComponent = (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div className="relative">
        {/* Main spinner */}
        <div
          className={`${sizeClasses[size]} ${colorClasses[color]} animate-spin`}
        >
          <svg
            className="w-full h-full"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>

        {/* Pulse effect for larger sizes */}
        {(size === 'lg' || size === 'xl') && (
          <div
            className={`absolute inset-0 ${sizeClasses[size]} ${colorClasses[color]} opacity-20 animate-ping rounded-full`}
          />
        )}
      </div>

      {/* Loading text */}
      {text && (
        <p className={`mt-3 text-sm font-medium ${colorClasses[color]}`}>
          {text}
        </p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white bg-opacity-90 flex items-center justify-center z-50">
        {spinnerComponent}
      </div>
    );
  }

  return spinnerComponent;
};

// Specialized loading components
export const ButtonSpinner = ({ className = '' }) => (
  <LoadingSpinner size="sm" color="white" className={`mr-2 ${className}`} />
);

export const PageSpinner = ({ text = 'Loading...' }) => (
  <div className="flex items-center justify-center min-h-64">
    <LoadingSpinner size="lg" color="blue" text={text} />
  </div>
);

export const OverlaySpinner = ({ text = 'Loading...' }) => (
  <LoadingSpinner size="xl" color="blue" text={text} fullScreen />
);

export const InlineSpinner = ({ text = '' }) => (
  <div className="flex items-center space-x-2">
    <LoadingSpinner size="sm" color="blue" />
    {text && <span className="text-sm text-gray-600">{text}</span>}
  </div>
);

export default LoadingSpinner;