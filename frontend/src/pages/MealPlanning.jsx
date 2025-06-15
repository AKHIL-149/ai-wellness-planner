// frontend/src/pages/MealPlanning.jsx

import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Tab } from '@headlessui/react';
import MealPlanGenerator from '../components/meals/MealPlanGenerator';
import MealCard from '../components/meals/MealCard';
import NutritionCard from '../components/meals/NutritionCard';
import GroceryList from '../components/meals/GroceryList';
import RecipeCard from '../components/meals/RecipeCard';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { 
 PlusIcon, 
 MagnifyingGlassIcon,
 SparklesIcon,
 ListBulletIcon 
} from '@heroicons/react/24/outline';
import { useApi } from '../hooks/useApi';
import { nutritionAPI } from '../services/api';

const MealPlanning = () => {
 const [searchTerm, setSearchTerm] = useState('');
 const [activeMealPlan, setActiveMealPlan] = useState(null);
 const [groceryList, setGroceryList] = useState([]);
 const navigate = useNavigate();
 const location = useLocation();

 const {
   data: dashboardData,
   loading: dashboardLoading,
   execute: fetchDashboard,
 } = useApi(nutritionAPI.getDashboard, [], { autoFetch: true });

 const {
   data: mealPlans,
   loading: plansLoading,
   execute: fetchMealPlans,
 } = useApi(nutritionAPI.getMealPlans, [], { autoFetch: true });

 const {
   data: recipes,
   loading: recipesLoading,
   execute: fetchRecipes,
 } = useApi(nutritionAPI.getRecipes, [], { autoFetch: true });

 useEffect(() => {
   if (mealPlans && mealPlans.length > 0) {
     const active = mealPlans.find(plan => plan.status === 'active');
     setActiveMealPlan(active);
   }
 }, [mealPlans]);

 const handlePlanGenerated = async (result) => {
   if (result.success) {
     await fetchMealPlans();
     await fetchDashboard();
   }
 };

 const handleActivatePlan = async (planId) => {
   try {
     await nutritionAPI.activateMealPlan(planId);
     await fetchMealPlans();
     await fetchDashboard();
   } catch (error) {
     console.error('Failed to activate meal plan:', error);
   }
 };

 const handleGenerateGroceryList = async (mealPlanId) => {
   try {
     const list = await nutritionAPI.generateGroceryList(mealPlanId);
     setGroceryList(list.items || []);
   } catch (error) {
     console.error('Failed to generate grocery list:', error);
   }
 };

 const tabs = [
   { name: 'Overview', path: '' },
   { name: 'Meal Plans', path: '/plans' },
   { name: 'Recipes', path: '/recipes' },
   { name: 'Generate Plan', path: '/generate' },
 ];

 const currentTab = tabs.findIndex(tab => 
   location.pathname.endsWith(tab.path)
 );

 if (dashboardLoading) {
   return <LoadingSpinner size="lg" text="Loading meal planning..." />;
 }

 return (
   <div className="space-y-6">
     {/* Page Header */}
     <div className="flex items-center justify-between">
       <div>
         <h1 className="text-2xl font-bold text-gray-900">Meal Planning</h1>
         <p className="mt-1 text-gray-600">
           AI-powered nutrition planning and recipe management
         </p>
       </div>
       
       <div className="flex space-x-3">
         <Button
           variant="outline"
           icon={ListBulletIcon}
           onClick={() => navigate('/meals/recipes')}
         >
           Browse Recipes
         </Button>
         <Button
           icon={SparklesIcon}
           onClick={() => navigate('/meals/generate')}
         >
           Generate Plan
         </Button>
       </div>
     </div>

     {/* Tab Navigation */}
     <Tab.Group selectedIndex={Math.max(0, currentTab)} onChange={(index) => {
       navigate(`/meals${tabs[index].path}`);
     }}>
       <Tab.List className="flex space-x-1 rounded-xl bg-green-900/20 p-1">
         {tabs.map((tab, index) => (
           <Tab
             key={tab.name}
             className={({ selected }) =>
               `w-full rounded-lg py-2.5 text-sm font-medium leading-5 text-green-700 ${
                 selected
                   ? 'bg-white shadow'
                   : 'text-green-100 hover:bg-white/[0.12] hover:text-white'
               }`
             }
           >
             {tab.name}
           </Tab>
         ))}
       </Tab.List>

       <Tab.Panels className="mt-6">
         {/* Overview Tab */}
         <Tab.Panel>
           <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
             {/* Today's Nutrition */}
             <div className="lg:col-span-2">
               <NutritionCard
                 title="Today's Nutrition"
                 current={dashboardData?.daily_nutrition || {}}
                 target={dashboardData?.nutrition_targets || {}}
               />
             </div>

             {/* Quick Actions */}
             <div className="space-y-4">
               <div className="bg-white p-4 rounded-lg border border-gray-200">
                 <h3 className="font-medium text-gray-900 mb-3">Quick Actions</h3>
                 <div className="space-y-2">
                   <Button
                     variant="outline"
                     size="sm"
                     fullWidth
                     icon={PlusIcon}
                     onClick={() => navigate('/meals/log')}
                   >
                     Log Meal
                   </Button>
                   <Button
                     variant="outline"
                     size="sm"
                     fullWidth
                     icon={SparklesIcon}
                     onClick={() => navigate('/meals/generate')}
                   >
                     Generate Plan
                   </Button>
                   {activeMealPlan && (
                     <Button
                       variant="outline"
                       size="sm"
                       fullWidth
                       icon={ListBulletIcon}
                       onClick={() => handleGenerateGroceryList(activeMealPlan.id)}
                     >
                       Grocery List
                     </Button>
                   )}
                 </div>
               </div>

               {/* Active Meal Plan */}
               {activeMealPlan && (
                 <div className="bg-white p-4 rounded-lg border border-gray-200">
                   <h3 className="font-medium text-gray-900 mb-3">Active Plan</h3>
                   <div className="text-sm text-gray-600">
                     <p className="font-medium">{activeMealPlan.name}</p>
                     <p>{activeMealPlan.daily_calories} calories/day</p>
                     <p>Started {new Date(activeMealPlan.start_date).toLocaleDateString()}</p>
                   </div>
                 </div>
               )}
             </div>
           </div>

           {/* Recent Meals */}
           {dashboardData?.recent_meals && dashboardData.recent_meals.length > 0 && (
             <div className="mt-8">
               <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Meals</h2>
               <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                 {dashboardData.recent_meals.map((meal, index) => (
                   <MealCard key={index} meal={meal} />
                 ))}
               </div>
             </div>
           )}
         </Tab.Panel>

         {/* Meal Plans Tab */}
         <Tab.Panel>
           <div className="space-y-6">
             <div className="flex items-center justify-between">
               <h2 className="text-lg font-semibold text-gray-900">Your Meal Plans</h2>
               <Button
                 icon={SparklesIcon}
                 onClick={() => navigate('/meals/generate')}
               >
                 Generate New Plan
               </Button>
             </div>

             {plansLoading ? (
               <LoadingSpinner size="md" text="Loading meal plans..." />
             ) : mealPlans && mealPlans.length > 0 ? (
               <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                 {mealPlans.map((plan) => (
                   <div key={plan.id} className="bg-white rounded-lg border border-gray-200 p-6">
                     <div className="flex items-start justify-between mb-4">
                       <div>
                         <h3 className="font-semibold text-gray-900">{plan.name}</h3>
                         <p className="text-sm text-gray-600">{plan.description}</p>
                       </div>
                       <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                         plan.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                       }`}>
                         {plan.status}
                       </span>
                     </div>
                     
                     <div className="space-y-2 mb-4">
                       <div className="flex justify-between text-sm">
                         <span className="text-gray-500">Daily Calories:</span>
                         <span className="font-medium">{plan.daily_calories}</span>
                       </div>
                       <div className="flex justify-between text-sm">
                         <span className="text-gray-500">Duration:</span>
                         <span className="font-medium">{plan.total_weeks} weeks</span>
                       </div>
                       <div className="flex justify-between text-sm">
                         <span className="text-gray-500">Progress:</span>
                         <span className="font-medium">{Math.round(plan.completion_percentage)}%</span>
                       </div>
                     </div>

                     <div className="flex space-x-2">
                       {plan.status !== 'active' && (
                         <Button
                           size="sm"
                           fullWidth
                           onClick={() => handleActivatePlan(plan.id)}
                         >
                           Activate
                         </Button>
                       )}
                       <Button
                         variant="outline"
                         size="sm"
                         fullWidth
                         onClick={() => navigate(`/meals/plans/${plan.id}`)}
                       >
                         View Details
                       </Button>
                     </div>
                   </div>
                 ))}
               </div>
             ) : (
               <div className="text-center py-12">
                 <SparklesIcon className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                 <h3 className="text-lg font-medium text-gray-900 mb-2">No meal plans yet</h3>
                 <p className="text-gray-600 mb-4">Generate your first AI-powered meal plan</p>
                 <Button
                   icon={SparklesIcon}
                   onClick={() => navigate('/meals/generate')}
                 >
                   Generate Meal Plan
                 </Button>
               </div>
             )}
           </div>
         </Tab.Panel>

         {/* Recipes Tab */}
         <Tab.Panel>
           <div className="space-y-6">
             <div className="flex items-center justify-between">
               <h2 className="text-lg font-semibold text-gray-900">Recipe Collection</h2>
               <div className="flex items-center space-x-3">
                 <Input
                   placeholder="Search recipes..."
                   value={searchTerm}
                   onChange={(e) => setSearchTerm(e.target.value)}
                   leftIcon={MagnifyingGlassIcon}
                   className="w-64"
                 />
                 <Button
                   icon={PlusIcon}
                   onClick={() => navigate('/meals/recipes/create')}
                 >
                   Add Recipe
                 </Button>
               </div>
             </div>

             {recipesLoading ? (
               <LoadingSpinner size="md" text="Loading recipes..." />
             ) : recipes && recipes.length > 0 ? (
               <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                 {recipes
                   .filter(recipe => 
                     recipe.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                     recipe.description?.toLowerCase().includes(searchTerm.toLowerCase())
                   )
                   .map((recipe) => (
                     <RecipeCard key={recipe.id} recipe={recipe} />
                   ))}
               </div>
             ) : (
               <div className="text-center py-12">
                 <PlusIcon className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                 <h3 className="text-lg font-medium text-gray-900 mb-2">No recipes yet</h3>
                 <p className="text-gray-600 mb-4">Add your first recipe to get started</p>
                 <Button
                   icon={PlusIcon}
                   onClick={() => navigate('/meals/recipes/create')}
                 >
                   Add Recipe
                 </Button>
               </div>
             )}
           </div>
         </Tab.Panel>

         {/* Generate Plan Tab */}
         <Tab.Panel>
           <MealPlanGenerator onPlanGenerated={handlePlanGenerated} />
         </Tab.Panel>
       </Tab.Panels>
     </Tab.Group>

     {/* Grocery List Modal/Sidebar would go here */}
     {groceryList.length > 0 && (
       <div className="fixed inset-y-0 right-0 w-80 bg-white shadow-xl z-50">
         <GroceryList 
           items={groceryList}
           onItemToggle={(itemId) => {
             setGroceryList(prev => prev.map(item => 
               item.id === itemId ? { ...item, is_completed: !item.is_completed } : item
             ));
           }}
           onRemoveItem={(itemId) => {
             setGroceryList(prev => prev.filter(item => item.id !== itemId));
           }}
         />
       </div>
     )}
   </div>
 );
};

export default MealPlanning;