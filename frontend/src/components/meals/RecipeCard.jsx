// frontend/src/components/meals/RecipeCard.jsx

import React, { useState } from 'react';
import { 
 ClockIcon, 
 FireIcon, 
 UserGroupIcon,
 ChefHatIcon,
 HeartIcon,
 ShareIcon,
 StarIcon,
 BookmarkIcon
} from '@heroicons/react/24/outline';
import { 
 HeartIcon as HeartSolid,
 StarIcon as StarSolid,
 BookmarkIcon as BookmarkSolid
} from '@heroicons/react/24/solid';
import Card from '../common/Card';
import Button from '../common/Button';
import Modal from '../common/Modal';

const RecipeCard = ({ 
 recipe, 
 onFavorite, 
 onBookmark, 
 onShare, 
 onStartCooking,
 showRating = true,
 showNutrition = true 
}) => {
 const [showDetails, setShowDetails] = useState(false);
 const [isFavorited, setIsFavorited] = useState(recipe.is_favorited || false);
 const [isBookmarked, setIsBookmarked] = useState(recipe.is_bookmarked || false);
 const [userRating, setUserRating] = useState(recipe.user_rating || 0);

 const handleFavorite = (e) => {
   e.stopPropagation();
   setIsFavorited(!isFavorited);
   onFavorite?.(recipe.id, !isFavorited);
 };

 const handleBookmark = (e) => {
   e.stopPropagation();
   setIsBookmarked(!isBookmarked);
   onBookmark?.(recipe.id, !isBookmarked);
 };

 const handleShare = (e) => {
   e.stopPropagation();
   onShare?.(recipe);
 };

 const handleRating = (rating) => {
   setUserRating(rating);
   // You would typically call an API here to save the rating
 };

 const formatTime = (minutes) => {
   if (!minutes) return 'N/A';
   if (minutes < 60) return `${minutes}m`;
   const hours = Math.floor(minutes / 60);
   const mins = minutes % 60;
   return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
 };

 const getDifficultyColor = (difficulty) => {
   switch (difficulty?.toLowerCase()) {
     case 'easy': return 'bg-green-100 text-green-800';
     case 'medium': return 'bg-yellow-100 text-yellow-800';
     case 'hard': return 'bg-red-100 text-red-800';
     default: return 'bg-gray-100 text-gray-800';
   }
 };

 const totalTime = (recipe.prep_time || 0) + (recipe.cook_time || 0);

 return (
   <>
     <Card className="hover:shadow-lg transition-all duration-200 cursor-pointer group">
       <div onClick={() => setShowDetails(true)}>
         {/* Recipe Image */}
         <div className="relative h-48 bg-gray-200 rounded-t-lg overflow-hidden">
           {recipe.image_url ? (
             <img
               src={recipe.image_url}
               alt={recipe.name}
               className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
             />
           ) : (
             <div className="w-full h-full bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center">
               <ChefHatIcon className="w-16 h-16 text-white opacity-70" />
             </div>
           )}
           
           {/* Overlay Actions */}
           <div className="absolute top-3 right-3 flex flex-col space-y-2 opacity-0 group-hover:opacity-100 transition-opacity">
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
               onClick={handleBookmark}
               className="p-2 bg-white bg-opacity-90 rounded-full shadow-sm hover:bg-opacity-100 transition-all"
             >
               {isBookmarked ? (
                 <BookmarkSolid className="w-5 h-5 text-blue-500" />
               ) : (
                 <BookmarkIcon className="w-5 h-5 text-gray-600" />
               )}
             </button>
             
             <button
               onClick={handleShare}
               className="p-2 bg-white bg-opacity-90 rounded-full shadow-sm hover:bg-opacity-100 transition-all"
             >
               <ShareIcon className="w-5 h-5 text-gray-600" />
             </button>
           </div>

           {/* Difficulty Badge */}
           {recipe.difficulty && (
             <div className="absolute top-3 left-3">
               <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(recipe.difficulty)}`}>
                 {recipe.difficulty}
               </span>
             </div>
           )}

           {/* Quick Stats Overlay */}
           <div className="absolute bottom-3 left-3 right-3">
             <div className="bg-black bg-opacity-60 backdrop-blur-sm rounded-lg p-2">
               <div className="flex items-center justify-between text-white text-xs">
                 <div className="flex items-center space-x-3">
                   {totalTime > 0 && (
                     <div className="flex items-center space-x-1">
                       <ClockIcon className="w-3 h-3" />
                       <span>{formatTime(totalTime)}</span>
                     </div>
                   )}
                   {recipe.servings && (
                     <div className="flex items-center space-x-1">
                       <UserGroupIcon className="w-3 h-3" />
                       <span>{recipe.servings}</span>
                     </div>
                   )}
                 </div>
                 {recipe.calories && (
                   <div className="flex items-center space-x-1">
                     <FireIcon className="w-3 h-3" />
                     <span>{recipe.calories} cal</span>
                   </div>
                 )}
               </div>
             </div>
           </div>
         </div>

         <div className="p-4">
           {/* Recipe Name and Description */}
           <div className="mb-3">
             <h3 className="text-lg font-semibold text-gray-900 mb-1 line-clamp-1">
               {recipe.name}
             </h3>
             {recipe.description && (
               <p className="text-gray-600 text-sm line-clamp-2">
                 {recipe.description}
               </p>
             )}
           </div>

           {/* Rating */}
           {showRating && (
             <div className="flex items-center justify-between mb-3">
               <div className="flex items-center space-x-1">
                 {[1, 2, 3, 4, 5].map((star) => (
                   <button
                     key={star}
                     onClick={(e) => {
                       e.stopPropagation();
                       handleRating(star);
                     }}
                     className="focus:outline-none"
                   >
                     {star <= (userRating || recipe.average_rating || 0) ? (
                       <StarSolid className="w-4 h-4 text-yellow-400" />
                     ) : (
                       <StarIcon className="w-4 h-4 text-gray-300" />
                     )}
                   </button>
                 ))}
                 <span className="text-sm text-gray-500 ml-1">
                   ({recipe.review_count || 0})
                 </span>
               </div>
               
               {recipe.author && (
                 <span className="text-xs text-gray-500">
                   by {recipe.author}
                 </span>
               )}
             </div>
           )}

           {/* Nutrition Summary */}
           {showNutrition && recipe.nutrition && (
             <div className="grid grid-cols-3 gap-2 mb-4 p-3 bg-gray-50 rounded-lg">
               <div className="text-center">
                 <div className="text-sm font-semibold text-gray-900">
                   {Math.round(recipe.nutrition.protein || 0)}g
                 </div>
                 <div className="text-xs text-gray-500">Protein</div>
               </div>
               <div className="text-center">
                 <div className="text-sm font-semibold text-gray-900">
                   {Math.round(recipe.nutrition.carbs || 0)}g
                 </div>
                 <div className="text-xs text-gray-500">Carbs</div>
               </div>
               <div className="text-center">
                 <div className="text-sm font-semibold text-gray-900">
                   {Math.round(recipe.nutrition.fat || 0)}g
                 </div>
                 <div className="text-xs text-gray-500">Fat</div>
               </div>
             </div>
           )}

           {/* Tags */}
           {recipe.tags && recipe.tags.length > 0 && (
             <div className="flex flex-wrap gap-1 mb-4">
               {recipe.tags.slice(0, 3).map((tag, index) => (
                 <span
                   key={index}
                   className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                 >
                   {tag}
                 </span>
               ))}
               {recipe.tags.length > 3 && (
                 <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                   +{recipe.tags.length - 3}
                 </span>
               )}
             </div>
           )}
         </div>
       </div>

       {/* Action Footer */}
       <div className="px-4 pb-4">
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
             onClick={(e) => {
               e.stopPropagation();
               onStartCooking?.(recipe);
             }}
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
       title={recipe.name}
       size="xl"
     >
       <div className="space-y-6">
         {/* Recipe Header */}
         <div className="flex items-start justify-between">
           <div className="flex-1">
             {recipe.description && (
               <p className="text-gray-600 mb-4">{recipe.description}</p>
             )}
             
             {showRating && (
               <div className="flex items-center space-x-2 mb-4">
                 <div className="flex items-center space-x-1">
                   {[1, 2, 3, 4, 5].map((star) => (
                     <button
                       key={star}
                       onClick={() => handleRating(star)}
                       className="focus:outline-none"
                     >
                       {star <= (userRating || recipe.average_rating || 0) ? (
                         <StarSolid className="w-5 h-5 text-yellow-400" />
                       ) : (
                         <StarIcon className="w-5 h-5 text-gray-300" />
                       )}
                     </button>
                   ))}
                 </div>
                 <span className="text-sm text-gray-500">
                   {recipe.average_rating?.toFixed(1) || '0.0'} ({recipe.review_count || 0} reviews)
                 </span>
               </div>
             )}
           </div>

           {recipe.image_url && (
             <img
               src={recipe.image_url}
               alt={recipe.name}
               className="w-32 h-32 object-cover rounded-lg ml-4"
             />
           )}
         </div>

         {/* Recipe Stats */}
         <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
           <div className="text-center p-3 bg-gray-50 rounded-lg">
             <ClockIcon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
             <div className="text-sm font-medium">{formatTime(recipe.prep_time)}</div>
             <div className="text-xs text-gray-500">Prep Time</div>
           </div>
           <div className="text-center p-3 bg-gray-50 rounded-lg">
             <ChefHatIcon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
             <div className="text-sm font-medium">{formatTime(recipe.cook_time)}</div>
             <div className="text-xs text-gray-500">Cook Time</div>
           </div>
           <div className="text-center p-3 bg-gray-50 rounded-lg">
             <UserGroupIcon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
             <div className="text-sm font-medium">{recipe.servings || 'N/A'}</div>
             <div className="text-xs text-gray-500">Servings</div>
           </div>
           <div className="text-center p-3 bg-gray-50 rounded-lg">
             <FireIcon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
             <div className="text-sm font-medium">{recipe.calories || 'N/A'}</div>
             <div className="text-xs text-gray-500">Calories</div>
           </div>
         </div>

         {/* Ingredients */}
         {recipe.ingredients && recipe.ingredients.length > 0 && (
           <div>
             <h4 className="text-lg font-semibold mb-3">Ingredients</h4>
             <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
               {recipe.ingredients.map((ingredient, index) => (
                 <div key={index} className="flex items-center p-2 hover:bg-gray-50 rounded">
                   <input
                     type="checkbox"
                     className="mr-3 rounded"
                     onChange={(e) => {
                       // Handle ingredient checking for shopping list
                     }}
                   />
                   <span className="text-gray-700">{ingredient}</span>
                 </div>
               ))}
             </div>
           </div>
         )}

         {/* Instructions */}
         {recipe.instructions && recipe.instructions.length > 0 && (
           <div>
             <h4 className="text-lg font-semibold mb-3">Instructions</h4>
             <ol className="space-y-3">
               {recipe.instructions.map((step, index) => (
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
         {recipe.nutrition && (
           <div>
             <h4 className="text-lg font-semibold mb-3">Nutrition Facts</h4>
             <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
               {Object.entries(recipe.nutrition).map(([key, value]) => (
                 <div key={key} className="text-center p-3 border border-gray-200 rounded-lg">
                   <div className="text-lg font-semibold text-gray-900">
                     {typeof value === 'number' ? Math.round(value) : value}
                     {key !== 'calories' && typeof value === 'number' ? 'g' : ''}
                   </div>
                   <div className="text-sm text-gray-500 capitalize">
                     {key.replace('_', ' ')}
                   </div>
                 </div>
               ))}
             </div>
           </div>
         )}

         {/* Tags */}
         {recipe.tags && recipe.tags.length > 0 && (
           <div>
             <h4 className="text-lg font-semibold mb-3">Tags</h4>
             <div className="flex flex-wrap gap-2">
               {recipe.tags.map((tag, index) => (
                 <span
                   key={index}
                   className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                 >
                   {tag}
                 </span>
               ))}
             </div>
           </div>
         )}

         {/* Action Buttons */}
         <div className="flex space-x-3 pt-4 border-t border-gray-200">
           <Button
             fullWidth
             icon={ChefHatIcon}
             onClick={() => {
               onStartCooking?.(recipe);
               setShowDetails(false);
             }}
           >
             Start Cooking
           </Button>
           <Button
             variant="outline"
             onClick={handleFavorite}
             icon={isFavorited ? HeartSolid : HeartIcon}
           >
             {isFavorited ? 'Favorited' : 'Favorite'}
           </Button>
           <Button
             variant="outline"
             onClick={handleBookmark}
             icon={isBookmarked ? BookmarkSolid : BookmarkIcon}
           >
             Save
           </Button>
           <Button
             variant="outline"
             onClick={handleShare}
             icon={ShareIcon}
           >
             Share
           </Button>
         </div>
       </div>
     </Modal>
   </>
 );
};

export default RecipeCard;