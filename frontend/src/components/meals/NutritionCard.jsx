// frontend/src/components/meals/NutritionCard.jsx

import React from 'react';
import { 
 FireIcon, 
 ChartBarIcon,
 TrophyIcon,
 ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import Card from '../common/Card';

const NutritionCard = ({ 
 title = "Daily Nutrition", 
 current = {}, 
 target = {}, 
 showProgress = true,
 className = "" 
}) => {
 const calculatePercentage = (current, target) => {
   if (!target || target === 0) return 0;
   return Math.min((current / target) * 100, 100);
 };

 const getProgressColor = (percentage) => {
   if (percentage >= 90) return 'bg-green-500';
   if (percentage >= 70) return 'bg-yellow-500';
   if (percentage >= 50) return 'bg-orange-500';
   return 'bg-red-500';
 };

 const getStatusIcon = (percentage) => {
   if (percentage >= 90) return <TrophyIcon className="w-5 h-5 text-green-600" />;
   if (percentage < 50) return <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />;
   return <ChartBarIcon className="w-5 h-5 text-orange-600" />;
 };

 const nutrients = [
   { 
     key: 'calories', 
     label: 'Calories', 
     unit: 'kcal',
     icon: FireIcon,
     color: 'text-red-600'
   },
   { 
     key: 'protein', 
     label: 'Protein', 
     unit: 'g',
     color: 'text-blue-600'
   },
   { 
     key: 'carbs', 
     label: 'Carbs', 
     unit: 'g',
     color: 'text-green-600'
   },
   { 
     key: 'fat', 
     label: 'Fat', 
     unit: 'g',
     color: 'text-purple-600'
   }
 ];

 const overallProgress = nutrients.reduce((sum, nutrient) => {
   return sum + calculatePercentage(current[nutrient.key] || 0, target[nutrient.key] || 0);
 }, 0) / nutrients.length;

 return (
   <Card title={title} className={className}>
     {/* Overall Progress */}
     {showProgress && (
       <div className="mb-6 p-4 bg-gray-50 rounded-lg">
         <div className="flex items-center justify-between mb-2">
           <span className="text-sm font-medium text-gray-700">Overall Progress</span>
           <div className="flex items-center space-x-2">
             {getStatusIcon(overallProgress)}
             <span className="text-sm font-semibold text-gray-900">
               {Math.round(overallProgress)}%
             </span>
           </div>
         </div>
         <div className="w-full bg-gray-200 rounded-full h-2">
           <div
             className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(overallProgress)}`}
             style={{ width: `${overallProgress}%` }}
           />
         </div>
       </div>
     )}

     {/* Nutrient Breakdown */}
     <div className="space-y-4">
       {nutrients.map((nutrient) => {
         const currentValue = current[nutrient.key] || 0;
         const targetValue = target[nutrient.key] || 0;
         const percentage = calculatePercentage(currentValue, targetValue);
         const Icon = nutrient.icon;

         return (
           <div key={nutrient.key} className="space-y-2">
             <div className="flex items-center justify-between">
               <div className="flex items-center space-x-2">
                 {Icon && <Icon className={`w-4 h-4 ${nutrient.color}`} />}
                 <span className="text-sm font-medium text-gray-700">
                   {nutrient.label}
                 </span>
               </div>
               <div className="text-sm text-gray-900">
                 <span className="font-semibold">{Math.round(currentValue)}</span>
                 <span className="text-gray-500 mx-1">/</span>
                 <span className="text-gray-600">{Math.round(targetValue)}</span>
                 <span className="text-gray-500 ml-1">{nutrient.unit}</span>
               </div>
             </div>
             
             {showProgress && targetValue > 0 && (
               <div className="w-full bg-gray-200 rounded-full h-1.5">
                 <div
                   className={`h-1.5 rounded-full transition-all duration-300 ${getProgressColor(percentage)}`}
                   style={{ width: `${percentage}%` }}
                 />
               </div>
             )}
           </div>
         );
       })}
     </div>

     {/* Macronutrient Distribution */}
     {current.protein && current.carbs && current.fat && (
       <div className="mt-6 pt-4 border-t border-gray-200">
         <h4 className="text-sm font-medium text-gray-700 mb-3">
           Macronutrient Distribution
         </h4>
         <div className="flex space-x-1 h-3 bg-gray-200 rounded-full overflow-hidden">
           <div
             className="bg-blue-500 transition-all duration-300"
             style={{ 
               width: `${((current.protein * 4) / (current.calories || 1)) * 100}%` 
             }}
             title={`Protein: ${Math.round(((current.protein * 4) / (current.calories || 1)) * 100)}%`}
           />
           <div
             className="bg-green-500 transition-all duration-300"
             style={{ 
               width: `${((current.carbs * 4) / (current.calories || 1)) * 100}%` 
             }}
             title={`Carbs: ${Math.round(((current.carbs * 4) / (current.calories || 1)) * 100)}%`}
           />
           <div
             className="bg-purple-500 transition-all duration-300"
             style={{ 
               width: `${((current.fat * 9) / (current.calories || 1)) * 100}%` 
             }}
             title={`Fat: ${Math.round(((current.fat * 9) / (current.calories || 1)) * 100)}%`}
           />
         </div>
         <div className="flex justify-between mt-2 text-xs text-gray-500">
           <span>Protein ({Math.round(((current.protein * 4) / (current.calories || 1)) * 100)}%)</span>
           <span>Carbs ({Math.round(((current.carbs * 4) / (current.calories || 1)) * 100)}%)</span>
           <span>Fat ({Math.round(((current.fat * 9) / (current.calories || 1)) * 100)}%)</span>
         </div>
       </div>
     )}
   </Card>
 );
};

export default NutritionCard;