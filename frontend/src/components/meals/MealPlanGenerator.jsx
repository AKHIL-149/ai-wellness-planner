// frontend/src/components/meals/MealPlanGenerator.jsx

import React, { useState } from 'react';
import { useForm } from '../../hooks/useForm';
import { useAI } from '../../hooks/useAI';
import Button from '../common/Button';
import Input from '../common/Input';
import Select from '../common/Select';
import Card from '../common/Card';
import LoadingSpinner from '../common/LoadingSpinner';
import { SparklesIcon, CalendarDaysIcon } from '@heroicons/react/24/outline';

const MealPlanGenerator = ({ onPlanGenerated }) => {
  const [generationStep, setGenerationStep] = useState(null);
  const [generatedPlan, setGeneratedPlan] = useState(null);
  const { generateMealPlan, loading, error } = useAI();

  const validationRules = {
    daily_calories: [
      (value) => {
        const num = Number(value);
        if (!value || isNaN(num)) return 'Daily calories is required';
        if (num < 1000 || num > 5000) return 'Daily calories must be between 1000-5000';
        return '';
      }
    ],
    duration_days: [
      (value) => {
        const num = Number(value);
        if (!value || isNaN(num)) return 'Duration is required';
        if (num < 1 || num > 14) return 'Duration must be between 1-14 days';
        return '';
      }
    ],
    meals_per_day: [
      (value) => {
        const num = Number(value);
        if (!value || isNaN(num)) return 'Meals per day is required';
        if (num < 2 || num > 6) return 'Must be between 2-6 meals per day';
        return '';
      }
    ]
  };

  const {
    values,
    errors,
    handleChange,
    handleSubmit,
    getFieldProps,
    getFieldState
  } = useForm({
    daily_calories: '2000',
    duration_days: '7',
    meals_per_day: '3',
    dietary_preferences: 'balanced',
    dietary_restrictions: '',
    fitness_goal: 'maintain',
    activity_level: 'moderate',
    cuisine_preferences: '',
    exclude_ingredients: '',
    budget_level: 'medium'
  }, validationRules);

  const dietaryOptions = [
    { value: 'balanced', label: 'Balanced Diet' },
    { value: 'low_carb', label: 'Low Carb' },
    { value: 'high_protein', label: 'High Protein' },
    { value: 'mediterranean', label: 'Mediterranean' },
    { value: 'vegetarian', label: 'Vegetarian' },
    { value: 'vegan', label: 'Vegan' },
    { value: 'keto', label: 'Ketogenic' },
    { value: 'paleo', label: 'Paleo' }
  ];

  const fitnessGoalOptions = [
    { value: 'lose_weight', label: 'Lose Weight' },
    { value: 'maintain', label: 'Maintain Weight' },
    { value: 'gain_weight', label: 'Gain Weight' },
    { value: 'build_muscle', label: 'Build Muscle' },
    { value: 'improve_health', label: 'Improve Health' }
  ];

  const activityLevelOptions = [
    { value: 'sedentary', label: 'Sedentary (little/no exercise)' },
    { value: 'light', label: 'Light (light exercise 1-3 days/week)' },
    { value: 'moderate', label: 'Moderate (moderate exercise 3-5 days/week)' },
    { value: 'active', label: 'Active (hard exercise 6-7 days/week)' },
    { value: 'very_active', label: 'Very Active (very hard exercise, physical job)' }
  ];

  const budgetOptions = [
    { value: 'low', label: 'Budget-Friendly' },
    { value: 'medium', label: 'Moderate' },
    { value: 'high', label: 'Premium' }
  ];

  const handleGeneratePlan = handleSubmit(async (formData) => {
    setGenerationStep('analyzing');
    
    try {
      const result = await generateMealPlan({
        ...formData,
        daily_calories: Number(formData.daily_calories),
        duration_days: Number(formData.duration_days),
        meals_per_day: Number(formData.meals_per_day)
      });

      if (result.success) {
        setGeneratedPlan(result.mealPlan);
        setGenerationStep('complete');
        onPlanGenerated?.(result);
      }
    } catch (error) {
      console.error('Meal plan generation failed:', error);
      setGenerationStep(null);
    }
  });

  const generationSteps = {
    analyzing: { message: 'Analyzing your preferences...', progress: 20 },
    calculating: { message: 'Calculating nutritional requirements...', progress: 40 },
    searching: { message: 'Finding suitable recipes...', progress: 60 },
    optimizing: { message: 'Optimizing meal combinations...', progress: 80 },
    generating: { message: 'Generating your personalized plan...', progress: 95 },
    complete: { message: 'Plan generated successfully!', progress: 100 }
  };

  if (generationStep && generationStep !== 'complete') {
    const step = generationSteps[generationStep];
    return (
      <Card className="text-center py-12">
        <div className="max-w-md mx-auto">
          <div className="w-16 h-16 bg-gradient-to-r from-green-400 to-blue-500 rounded-full mx-auto mb-6 flex items-center justify-center">
            <SparklesIcon className="w-8 h-8 text-white animate-spin" />
          </div>
          
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Creating Your Meal Plan
          </h3>
          
          <p className="text-gray-600 mb-6">{step.message}</p>
          
          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <div
              className="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${step.progress}%` }}
            />
          </div>
          
          <p className="text-sm text-gray-500">{step.progress}% complete</p>
        </div>
      </Card>
    );
  }

  return (
    <Card
      title="Generate AI Meal Plan"
      subtitle="Create a personalized meal plan tailored to your goals and preferences"
    >
      <form onSubmit={handleGeneratePlan} className="space-y-6">
        {/* Basic Requirements */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Input
            label="Daily Calories"
            type="number"
            min="1000"
            max="5000"
            {...getFieldProps('daily_calories')}
            {...getFieldState('daily_calories')}
            helpText="Target calories per day"
          />
          
          <Input
            label="Plan Duration"
            type="number"
            min="1"
            max="14"
            {...getFieldProps('duration_days')}
            {...getFieldState('duration_days')}
            helpText="Number of days"
          />
          
          <Select
            label="Meals Per Day"
            options={[
              { value: '2', label: '2 meals' },
              { value: '3', label: '3 meals' },
              { value: '4', label: '4 meals' },
              { value: '5', label: '5 meals' },
              { value: '6', label: '6 meals' }
            ]}
            {...getFieldProps('meals_per_day')}
            {...getFieldState('meals_per_day')}
          />
        </div>

        {/* Dietary Preferences */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select
            label="Dietary Preference"
            options={dietaryOptions}
            {...getFieldProps('dietary_preferences')}
            {...getFieldState('dietary_preferences')}
          />
          
          <Input
           label="Dietary Restrictions"
           placeholder="e.g., gluten-free, nut allergies, lactose intolerant"
           {...getFieldProps('dietary_restrictions')}
           {...getFieldState('dietary_restrictions')}
           helpText="Any allergies or restrictions"
         />
       </div>

       {/* Goals and Activity */}
       <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
         <Select
           label="Fitness Goal"
           options={fitnessGoalOptions}
           {...getFieldProps('fitness_goal')}
           {...getFieldState('fitness_goal')}
         />
         
         <Select
           label="Activity Level"
           options={activityLevelOptions}
           {...getFieldProps('activity_level')}
           {...getFieldState('activity_level')}
         />
       </div>

       {/* Preferences */}
       <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
         <Input
           label="Cuisine Preferences"
           placeholder="e.g., Italian, Asian, Mexican"
           {...getFieldProps('cuisine_preferences')}
           {...getFieldState('cuisine_preferences')}
           helpText="Preferred cooking styles (optional)"
         />
         
         <Input
           label="Exclude Ingredients"
           placeholder="e.g., mushrooms, cilantro, spicy food"
           {...getFieldProps('exclude_ingredients')}
           {...getFieldState('exclude_ingredients')}
           helpText="Ingredients to avoid (optional)"
         />
       </div>

       {/* Budget Level */}
       <Select
         label="Budget Level"
         options={budgetOptions}
         {...getFieldProps('budget_level')}
         {...getFieldState('budget_level')}
         helpText="This affects ingredient selection and meal complexity"
       />

       {error && (
         <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
           <p className="text-sm text-red-600">{error}</p>
         </div>
       )}

       <Button
         type="submit"
         fullWidth
         loading={loading}
         icon={SparklesIcon}
         size="lg"
       >
         Generate My Meal Plan
       </Button>
     </form>
   </Card>
 );
};

export default MealPlanGenerator;