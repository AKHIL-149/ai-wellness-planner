// frontend/src/components/common/Card.jsx

import React from 'react';

const Card = ({
  children,
  title,
  subtitle,
  footer,
  padding = 'default',
  shadow = 'default',
  border = true,
  className = '',
  headerClassName = '',
  bodyClassName = '',
  footerClassName = '',
  ...props
}) => {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    default: 'p-6',
    lg: 'p-8',
  };

  const shadowClasses = {
    none: '',
    sm: 'shadow-sm',
    default: 'shadow-md',
    lg: 'shadow-lg',
    xl: 'shadow-xl',
  };

  const borderClasses = border ? 'border border-gray-200' : '';

  return (
    <div
      className={`
        bg-white rounded-lg
        ${borderClasses}
        ${shadowClasses[shadow]}
        ${className}
      `}
      {...props}
    >
      {(title || subtitle) && (
        <div className={`border-b border-gray-200 px-6 py-4 ${headerClassName}`}>
          {title && (
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          )}
          {subtitle && (
            <p className="mt-1 text-sm text-gray-600">{subtitle}</p>
          )}
        </div>
      )}

      <div className={`${paddingClasses[padding]} ${bodyClassName}`}>
        {children}
      </div>

      {footer && (
        <div className={`border-t border-gray-200 px-6 py-4 ${footerClassName}`}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;