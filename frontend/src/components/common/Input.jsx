// frontend/src/components/common/Input.jsx

import React, { forwardRef } from 'react';
import { ExclamationCircleIcon } from '@heroicons/react/24/outline';

const Input = forwardRef(({
 label,
 error,
 helpText,
 required = false,
 disabled = false,
 className = '',
 containerClassName = '',
 leftIcon: LeftIcon,
 rightIcon: RightIcon,
 ...props
}, ref) => {
 const hasError = !!error;

 return (
   <div className={containerClassName}>
     {label && (
       <label className="block text-sm font-medium text-gray-700 mb-1">
         {label}
         {required && <span className="text-red-500 ml-1">*</span>}
       </label>
     )}
     
     <div className="relative">
       {LeftIcon && (
         <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
           <LeftIcon className="h-5 w-5 text-gray-400" />
         </div>
       )}
       
       <input
         ref={ref}
         className={`
           block w-full rounded-md border-gray-300 shadow-sm
           focus:border-blue-500 focus:ring-blue-500
           ${LeftIcon ? 'pl-10' : 'pl-3'}
           ${RightIcon || hasError ? 'pr-10' : 'pr-3'}
           ${hasError ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}
           ${disabled ? 'bg-gray-50 text-gray-500 cursor-not-allowed' : ''}
           ${className}
         `}
         disabled={disabled}
         {...props}
       />
       
       {(RightIcon || hasError) && (
         <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
           {hasError ? (
             <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
           ) : (
             RightIcon && <RightIcon className="h-5 w-5 text-gray-400" />
           )}
         </div>
       )}
     </div>
     
     {(error || helpText) && (
       <div className="mt-1">
         {error && (
           <p className="text-sm text-red-600">{error}</p>
         )}
         {helpText && !error && (
           <p className="text-sm text-gray-500">{helpText}</p>
         )}
       </div>
     )}
   </div>
 );
});

Input.displayName = 'Input';

export default Input;