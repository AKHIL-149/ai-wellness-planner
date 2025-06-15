// frontend/src/components/meals/MealCard.jsx

import React, { useState } from 'react';
import { 
 ClockIcon, 
 FireIcon, 
 UserGroupIcon,
 ChefHatIcon,
 HeartIcon,
 ShareIcon
} from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolid } from '@heroicons/react/24/solid';
import Card from '../common/Card';
import Button from '../common/Button';
import Modal from '../common/Modal';

const MealCard = ({ meal, showNutrition = true, onFavorite, onShare }) => {
 const [showDetails, setShowDetails] = useState(false);
 const [isFavorited, setIsFavorited] = useState(meal.is_favorited || false);

 const handleFavorite = () => {
   setIsFavorited(!isFavorited);
   onFavorite?.(meal.id, !isFavorited);
 };

 const formatTime = (minutes) => {
   if (minutes < 60) return `${minutes}m`;
   const hours = Math.floor(minutes / 60);
   const mins = minutes % 60;
   return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
 };

 return (
   <>
     <Card className="hover:shadow-lg transition-shadow duration-200">
       {/* Meal Image */}
       {meal.image_url && (
         <div className="relative h-48 bg-gray-200 rounded-t-lg overflow-hidden">
           <img
             src={meal.image_url}
             alt={meal.name}
             className="w-full h-full object-cover"
           />
           <div className="absolute top-3 right-3 flex space-x-2">
             <button
               onClick={handleFavorite}
               className="p-2 bg-white bg-opacity-90 rounded-full shadow-sm hover:bg-opacity-100 transition-all"
             >
               {isFavorited ? (
                 <HeartSolid className="w-5 h-5 text-red-500" />
               ) : (
                 <HeartIcon className="w-5 h-5 text-gray-600" />
               )}
             </button>
             <button
               onClick={() => onShare?.(meal)}
               className="p-2 bg-white bg-opacity-90 rounded-full shadow-sm hover:bg-opacity-100 transition-all"
             >
               <ShareIcon className="w-5 h-5 text-gray-600" />
             </button>
           </div>
         </div>
       )}

       <div className="p-4">
         {/* Meal Name and Description */}
         <h3 className="text-lg font-semibold text-gray-900 mb-2">
           {meal.name}
         </h3>
         
         {meal.description && (
           <p className="text-gray-600 text-sm mb-3 line-clamp-2">
             {meal.description}
           </p>
         )}

         {/* Quick Stats */}
         <div className="flex items-center justify-between mb-4">
           <div className="flex items-center space-x-4 text-sm text-gray-500">
             {meal.prep_time && (
               <div className="flex items-center space-x-1">
                 <ClockIcon className="w-4 h-4" />
                 <span>{formatTime(meal.prep_time)}</span>
               </div>
             )}
             
             {meal.calories && (
               <div className="flex items-center space-x-1">
                 <FireIcon className="w-4 h-4" />
                 <span>{meal.calories} cal</span>
               </div>
             )}
             
             {meal.servings && (
               <div className="flex items-center space-x-1">
                 <UserGroupIcon className="w-4 h-4" />
                 <span>{meal.servings} servings</span>
               </div>
             )}
           </div>
           
           {meal.difficulty && (
             <span className={`px-2 py-1 rounded-full text-xs font-medium ${
               meal.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
               meal.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
               'bg-red-100 text-red-800'
             }`}>
               {meal.difficulty}
             </span>
           )}
         </div>

         {/* Nutrition Summary */}
         {showNutrition && meal.nutrition && (
           <div className="grid grid-cols-3 gap-2 mb-4 p-3 bg-gray-50 rounded-lg">
             <div className="text-center">
               <div className="text-sm font-semibold text-gray-900">
                 {Math.round(meal.nutrition.protein || 0)}g
               </div>
               <div className="text-xs text-gray-500">Protein</div>
             </div>
             <div className="text-center">
               <div className="text-sm font-semibold text-gray-900">
                 {Math.round(meal.nutrition.carbs || 0)}g
               </div>
               <div className="text-xs text-gray-500">Carbs</div>
             </div>
             <div className="text-center">
               <div className="text-sm font-semibold text-gray-900">
                 {Math.round(meal.nutrition.fat || 0)}g
               </div>
               <div className="text-xs text-gray-500">Fat</div>
             </div>
           </div>
         )}

         {/* Tags */}
         {meal.tags && meal.tags.length > 0 && (
           <div className="flex flex-wrap gap-1 mb-4">
             {meal.tags.slice(0, 3).map((tag, index) => (
               <span
                 key={index}
                 className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
               >
                 {tag}
               </span>
             ))}
             {meal.tags.length > 3 && (
               <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                 +{meal.tags.length - 3} more
               </span>
             )}
           </div>
         )}

         {/* Actions */}
         <div className="flex space-x-2">
           <Button
             variant="outline"
             size="sm"
             fullWidth
             onClick={() => setShowDetails(true)}
           >
             View Recipe
           </Button>
           <Button
             size="sm"
             fullWidth
             icon={ChefHatIcon}
           >
             Start Cooking
           </Button>
         </div>
       </div>
     </Card>

     {/* Recipe Details Modal */}
     <Modal
       isOpen={showDetails}
       onClose={() => setShowDetails(false)}
       title={meal.name}
       size="lg"
     >
       <div className="space-y-6">
         {/* Recipe Image */}
         {meal.image_url && (
           <img
             src={meal.image_url}
             alt={meal.name}
             className="w-full h-64 object-cover rounded-lg"
           />
         )}

         {/* Recipe Info */}
         <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
           {meal.prep_time && (
             <div className="text-center p-3 bg-gray-50 rounded-lg">
               <ClockIcon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
               <div className="text-sm font-medium">{formatTime(meal.prep_time)}</div>
               <div className="text-xs text-gray-500">Prep Time</div>
             </div>
           )}
           {meal.cook_time && (
             <div className="text-center p-3 bg-gray-50 rounded-lg">
               <ChefHatIcon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
               <div className="text-sm font-medium">{formatTime(meal.cook_time)}</div>
               <div className="text-xs text-gray-500">Cook Time</div>
             </div>
           )}
           {meal.servings && (
             <div className="text-center p-3 bg-gray-50 rounded-lg">
               <UserGroupIcon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
               <div className="text-sm font-medium">{meal.servings}</div>
               <div className="text-xs text-gray-500">Servings</div>
             </div>
           )}
           {meal.calories && (
             <div className="text-center p-3 bg-gray-50 rounded-lg">
               <FireIcon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
               <div className="text-sm font-medium">{meal.calories}</div>
               <div className="text-xs text-gray-500">Calories</div>
             </div>
           )}
         </div>

         {/* Ingredients */}
         {meal.ingredients && (
           <div>
             <h4 className="text-lg font-semibold mb-3">Ingredients</h4>
             <ul className="space-y-2">
               {meal.ingredients.map((ingredient, index) => (
                 <li key={index} className="flex items-center">
                   <span className="w-2 h-2 bg-blue-500 rounded-full mr-3 flex-shrink-0" />
                   <span className="text-gray-700">{ingredient}</span>
                 </li>
               ))}
             </ul>
           </div>
         )}

         {/* Instructions */}
         {meal.instructions && (
           <div>
             <h4 className="text-lg font-semibold mb-3">Instructions</h4>
             <ol className="space-y-3">
               {meal.instructions.map((step, index) => (
                 <li key={index} className="flex">
                   <span className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white text-sm font-medium rounded-full flex items-center justify-center mr-3 mt-0.5">
                     {index + 1}
                   </span>
                   <span className="text-gray-700">{step}</span>
                 </li>
               ))}
             </ol>
           </div>
         )}

         {/* Nutrition Facts */}
         {meal.nutrition && (
           <div>
             <h4 className="text-lg font-semibold mb-3">Nutrition Facts</h4>
             <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
               {Object.entries(meal.nutrition).map(([key, value]) => (
                 <div key={key} className="text-center p-3 border border-gray-200 rounded-lg">
                   <div className="text-lg font-semibold text-gray-900">
                     {Math.round(value)}{key === 'calories' ? '' : 'g'}
                   </div>
                   <div className="text-sm text-gray-500 capitalize">
                     {key.replace('_', ' ')}
                   </div>
                 </div>
               ))}
             </div>
           </div>
         )}
       </div>
     </Modal>
   </>
 );
};

export default MealCard;