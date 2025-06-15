// frontend/src/components/meals/GroceryList.jsx

import React, { useState } from 'react';
import { 
 CheckIcon,
 ShoppingCartIcon,
 PrinterIcon,
 ShareIcon,
 TrashIcon
} from '@heroicons/react/24/outline';
import Card from '../common/Card';
import Button from '../common/Button';

const GroceryList = ({ items = [], onItemToggle, onRemoveItem, onShare, onPrint }) => {
 const [filter, setFilter] = useState('all'); // all, pending, completed
 const [sortBy, setSortBy] = useState('category'); // category, name, store

 const groupedItems = items.reduce((groups, item) => {
   const key = sortBy === 'category' ? item.category || 'Other' : 
               sortBy === 'store' ? item.store_section || 'General' : 
               item.name.charAt(0).toUpperCase();
   
   if (!groups[key]) groups[key] = [];
   groups[key].push(item);
   return groups;
 }, {});

 const filteredGroups = Object.keys(groupedItems).reduce((filtered, key) => {
   const groupItems = groupedItems[key].filter(item => {
     if (filter === 'pending') return !item.is_completed;
     if (filter === 'completed') return item.is_completed;
     return true;
   });
   
   if (groupItems.length > 0) {
     filtered[key] = groupItems.sort((a, b) => a.name.localeCompare(b.name));
   }
   return filtered;
 }, {});

 const totalItems = items.length;
 const completedItems = items.filter(item => item.is_completed).length;
 const totalEstimatedCost = items.reduce((sum, item) => sum + (item.estimated_cost || 0), 0);

 const handleItemToggle = (itemId) => {
   onItemToggle?.(itemId);
 };

 const handleRemoveItem = (itemId) => {
   onRemoveItem?.(itemId);
 };

 return (
   <Card>
     {/* Header */}
     <div className="flex items-center justify-between p-4 border-b border-gray-200">
       <div>
         <h3 className="text-lg font-semibold text-gray-900">Grocery List</h3>
         <p className="text-sm text-gray-500">
           {completedItems} of {totalItems} items completed
           {totalEstimatedCost > 0 && (
             <span className="ml-2">• Est. ${totalEstimatedCost.toFixed(2)}</span>
           )}
         </p>
       </div>
       <div className="flex space-x-2">
         <Button
           variant="outline"
           size="sm"
           icon={PrinterIcon}
           onClick={onPrint}
         >
           Print
         </Button>
         <Button
           variant="outline"
           size="sm"
           icon={ShareIcon}
           onClick={onShare}
         >
           Share
         </Button>
       </div>
     </div>

     {/* Progress Bar */}
     <div className="p-4 border-b border-gray-200">
       <div className="w-full bg-gray-200 rounded-full h-2">
         <div
           className="bg-green-500 h-2 rounded-full transition-all duration-300"
           style={{ width: totalItems > 0 ? `${(completedItems / totalItems) * 100}%` : '0%' }}
         />
       </div>
     </div>

     {/* Filters and Sort */}
     <div className="p-4 border-b border-gray-200">
       <div className="flex items-center justify-between">
         <div className="flex space-x-2">
           {['all', 'pending', 'completed'].map((filterOption) => (
             <button
               key={filterOption}
               onClick={() => setFilter(filterOption)}
               className={`px-3 py-1 rounded-full text-sm font-medium ${
                 filter === filterOption
                   ? 'bg-blue-100 text-blue-700'
                   : 'text-gray-500 hover:text-gray-700'
               }`}
             >
               {filterOption === 'all' ? 'All Items' :
                filterOption === 'pending' ? 'To Buy' : 'Completed'}
             </button>
           ))}
         </div>
         
         <select
           value={sortBy}
           onChange={(e) => setSortBy(e.target.value)}
           className="text-sm border border-gray-300 rounded px-2 py-1"
         >
           <option value="category">Sort by Category</option>
           <option value="name">Sort by Name</option>
           <option value="store">Sort by Store Section</option>
         </select>
       </div>
     </div>

     {/* Items List */}
     <div className="max-h-96 overflow-y-auto">
       {Object.keys(filteredGroups).length === 0 ? (
         <div className="p-8 text-center text-gray-500">
           <ShoppingCartIcon className="w-12 h-12 mx-auto mb-3 text-gray-400" />
           <p>No items match your filter</p>
         </div>
       ) : (
         Object.entries(filteredGroups).map(([groupName, groupItems]) => (
           <div key={groupName} className="border-b border-gray-100 last:border-b-0">
             <div className="px-4 py-2 bg-gray-50 border-b border-gray-100">
               <h4 className="text-sm font-medium text-gray-700">{groupName}</h4>
             </div>
             <div className="divide-y divide-gray-100">
               {groupItems.map((item) => (
                 <div
                   key={item.id}
                   className={`flex items-center justify-between p-4 hover:bg-gray-50 ${
                     item.is_completed ? 'opacity-60' : ''
                   }`}
                 >
                   <div className="flex items-center space-x-3">
                     <button
                       onClick={() => handleItemToggle(item.id)}
                       className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                         item.is_completed
                           ? 'bg-green-500 border-green-500'
                           : 'border-gray-300 hover:border-green-500'
                       }`}
                     >
                       {item.is_completed && (
                         <CheckIcon className="w-3 h-3 text-white" />
                       )}
                     </button>
                     
                     <div className="flex-1">
                       <div className={`text-sm font-medium ${
                         item.is_completed ? 'line-through text-gray-500' : 'text-gray-900'
                       }`}>
                         {item.name}
                       </div>
                       <div className="text-xs text-gray-500">
                         {item.quantity && <span>{item.quantity}</span>}
                         {item.unit && <span> {item.unit}</span>}
                         {item.brand && <span> • {item.brand}</span>}
                       </div>
                     </div>
                   </div>
                   
                   <div className="flex items-center space-x-2">
                     {item.estimated_cost && (
                       <span className="text-sm text-gray-600">
                         ${item.estimated_cost.toFixed(2)}
                       </span>
                     )}
                     <button
                       onClick={() => handleRemoveItem(item.id)}
                       className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                     >
                       <TrashIcon className="w-4 h-4" />
                     </button>
                   </div>
                 </div>
               ))}
             </div>
           </div>
         ))
       )}
     </div>

     {/* Footer */}
     {items.length > 0 && (
       <div className="p-4 border-t border-gray-200 bg-gray-50">
         <div className="flex items-center justify-between text-sm">
           <span className="text-gray-600">
             {completedItems} of {totalItems} items completed
           </span>
           {totalEstimatedCost > 0 && (
             <span className="font-medium text-gray-900">
               Total: ${totalEstimatedCost.toFixed(2)}
             </span>
           )}
         </div>
       </div>
     )}
   </Card>
 );
};

export default GroceryList;