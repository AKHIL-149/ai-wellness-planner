// frontend/src/components/common/Toast.jsx

import React, { useState, useEffect } from 'react';
import {
 CheckCircleIcon,
 ExclamationTriangleIcon,
 InformationCircleIcon,
 XCircleIcon,
 XMarkIcon,
} from '@heroicons/react/24/outline';

const Toast = ({
 type = 'info',
 title,
 message,
 duration = 5000,
 onClose,
 showCloseButton = true,
}) => {
 const [isVisible, setIsVisible] = useState(true);

 useEffect(() => {
   if (duration > 0) {
     const timer = setTimeout(() => {
       setIsVisible(false);
       setTimeout(onClose, 300); // Wait for fade out animation
     }, duration);

     return () => clearTimeout(timer);
   }
 }, [duration, onClose]);

 const handleClose = () => {
   setIsVisible(false);
   setTimeout(onClose, 300);
 };

 const typeConfig = {
   success: {
     icon: CheckCircleIcon,
     bgColor: 'bg-green-50',
     borderColor: 'border-green-200',
     iconColor: 'text-green-400',
     titleColor: 'text-green-800',
     messageColor: 'text-green-700',
   },
   error: {
     icon: XCircleIcon,
     bgColor: 'bg-red-50',
     borderColor: 'border-red-200',
     iconColor: 'text-red-400',
     titleColor: 'text-red-800',
     messageColor: 'text-red-700',
   },
   warning: {
     icon: ExclamationTriangleIcon,
     bgColor: 'bg-yellow-50',
     borderColor: 'border-yellow-200',
     iconColor: 'text-yellow-400',
     titleColor: 'text-yellow-800',
     messageColor: 'text-yellow-700',
   },
   info: {
     icon: InformationCircleIcon,
     bgColor: 'bg-blue-50',
     borderColor: 'border-blue-200',
     iconColor: 'text-blue-400',
     titleColor: 'text-blue-800',
     messageColor: 'text-blue-700',
   },
 };

 const config = typeConfig[type];
 const Icon = config.icon;

 return (
   <div
     className={`
       max-w-sm w-full shadow-lg rounded-lg pointer-events-auto border
       ${config.bgColor} ${config.borderColor}
       transition-all duration-300 ease-in-out transform
       ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
     `}
   >
     <div className="p-4">
       <div className="flex items-start">
         <div className="flex-shrink-0">
           <Icon className={`h-6 w-6 ${config.iconColor}`} />
         </div>
         <div className="ml-3 w-0 flex-1 pt-0.5">
           {title && (
             <p className={`text-sm font-medium ${config.titleColor}`}>
               {title}
             </p>
           )}
           {message && (
             <p className={`text-sm ${config.messageColor} ${title ? 'mt-1' : ''}`}>
               {message}
             </p>
           )}
         </div>
         {showCloseButton && (
           <div className="ml-4 flex-shrink-0 flex">
             <button
               onClick={handleClose}
               className={`
                 rounded-md inline-flex text-gray-400 hover:text-gray-500
                 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
               `}
             >
               <XMarkIcon className="h-5 w-5" />
             </button>
           </div>
         )}
       </div>
     </div>
   </div>
 );
};

// Toast Container
export const ToastContainer = ({ toasts = [] }) => {
 return (
   <div className="fixed top-0 right-0 z-50 p-6 space-y-4">
     {toasts.map((toast) => (
       <Toast key={toast.id} {...toast} />
     ))}
   </div>
 );
};

export default Toast;