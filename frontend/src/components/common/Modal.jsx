// frontend/src/components/common/Modal.jsx

import React, { useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useClickOutside } from '../../hooks/useClickOutside';
import { useKeyPress } from '../../hooks/useKeyPress';

const Modal = ({
 isOpen,
 onClose,
 title,
 children,
 size = 'md',
 showCloseButton = true,
 closeOnBackdrop = true,
 closeOnEscape = true,
 className = '',
}) => {
 const escPressed = useKeyPress('Escape');
 const modalRef = useClickOutside(() => {
   if (closeOnBackdrop) onClose();
 });

 useEffect(() => {
   if (escPressed && closeOnEscape && isOpen) {
     onClose();
   }
 }, [escPressed, closeOnEscape, isOpen, onClose]);

 useEffect(() => {
   if (isOpen) {
     document.body.style.overflow = 'hidden';
   } else {
     document.body.style.overflow = 'unset';
   }

   return () => {
     document.body.style.overflow = 'unset';
   };
 }, [isOpen]);

 if (!isOpen) return null;

 const sizeClasses = {
   sm: 'max-w-md',
   md: 'max-w-lg',
   lg: 'max-w-2xl',
   xl: 'max-w-4xl',
   full: 'max-w-full mx-4',
 };

 return (
   <div className="fixed inset-0 z-50 overflow-y-auto">
     <div className="flex min-h-screen items-center justify-center p-4">
       {/* Backdrop */}
       <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" />
       
       {/* Modal */}
       <div
         ref={modalRef}
         className={`
           relative bg-white rounded-lg shadow-xl transform transition-all
           ${sizeClasses[size]}
           ${className}
         `}
       >
         {/* Header */}
         {(title || showCloseButton) && (
           <div className="flex items-center justify-between p-6 border-b border-gray-200">
             {title && (
               <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
             )}
             {showCloseButton && (
               <button
                 onClick={onClose}
                 className="text-gray-400 hover:text-gray-600 transition-colors"
               >
                 <XMarkIcon className="w-6 h-6" />
               </button>
             )}
           </div>
         )}

         {/* Content */}
         <div className="p-6">
           {children}
         </div>
       </div>
     </div>
   </div>
 );
};

export default Modal;