// frontend/src/components/common/Select.jsx

import React, { forwardRef } from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/outline';

const Select = forwardRef(({
 label,
 error,
 helpText,
 required = false,
 disabled = false,
 placeholder = 'Select an option',
 options = [],
 className = '',
 containerClassName = '',
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
       <select
         ref={ref}
         className={`
           block w-full rounded-md border-gray-300 shadow-sm
           focus:border-blue-500 focus:ring-blue-500
           pr-10 pl-3 py-2 text-base
           ${hasError ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}
           ${disabled ? 'bg-gray-50 text-gray-500 cursor-not-allowed' : ''}
           ${className}
         `}
         disabled={disabled}
         {...props}
       >
         {placeholder && (
           <option value="" disabled>
             {placeholder}
           </option>
         )}
         {options.map((option) => (
           <option key={option.value} value={option.value}>
             {option.label}
           </option>
         ))}
       </select>
       
       <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
         <ChevronDownIcon className="h-5 w-5 text-gray-400" />
       </div>
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

Select.displayName = 'Select';

export default Select;