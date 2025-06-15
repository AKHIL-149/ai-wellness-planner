// frontend/src/components/workouts/WorkoutGenerator.jsx

import React, { useState } from 'react';
import { useForm } from '../../hooks/useForm';
import { useAI } from '../../hooks/useAI';
import Button from '../common/Button';
import Input from '../common/Input';
import Select from '../common/Select';
import Card from '../common/Card';
import { SparklesIcon, BoltIcon } from '@heroicons/react/24/outline';

const WorkoutGenerator = ({ onWorkoutGenerated }) => {
  const [generationStep, setGenerationStep] = useState(null);
  const { generateWorkoutPlan, loading, error } = useAI();

  const validationRules = {
    duration_weeks: [
      (value) => {
        const num = Number(value);
        if (!value || isNaN(num)) return 'Duration is required';
        if (num < 1 || num > 52) return 'Duration must be between 1-52 weeks';
        return '';
      }
    ],
    workouts_per_week: [
      (value) => {
        const num = Number(value);
        if (!value || isNaN(num)) return 'Workouts per week is required';
        if (num < 1 || num > 7) return 'Must be between 1-7 workouts per week';
       return '';
     }
   ],
   workout_duration: [
     (value) => {
       const num = Number(value);
       if (!value || isNaN(num)) return 'Workout duration is required';
       if (num < 15 || num > 180) return 'Duration must be between 15-180 minutes';
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
   duration_weeks: '12',
   workouts_per_week: '3',
   workout_duration: '45',
   fitness_level: 'beginner',
   primary_goal: 'general_fitness',
   available_equipment: 'bodyweight',
   preferred_workout_types: '',
   time_availability: 'flexible',
   injuries_limitations: '',
   intensity_preference: 'moderate'
 }, validationRules);

 const fitnessLevelOptions = [
   { value: 'beginner', label: 'Beginner (0-6 months)' },
   { value: 'intermediate', label: 'Intermediate (6 months - 2 years)' },
   { value: 'advanced', label: 'Advanced (2+ years)' },
   { value: 'expert', label: 'Expert/Athlete' }
 ];

 const primaryGoalOptions = [
   { value: 'weight_loss', label: 'Weight Loss' },
   { value: 'muscle_gain', label: 'Muscle Gain' },
   { value: 'strength', label: 'Build Strength' },
   { value: 'endurance', label: 'Improve Endurance' },
   { value: 'general_fitness', label: 'General Fitness' },
   { value: 'sports_performance', label: 'Sports Performance' },
   { value: 'rehabilitation', label: 'Rehabilitation/Recovery' }
 ];

 const equipmentOptions = [
   { value: 'bodyweight', label: 'Bodyweight Only' },
   { value: 'basic_home', label: 'Basic Home Gym (dumbbells, resistance bands)' },
   { value: 'full_home', label: 'Full Home Gym' },
   { value: 'commercial_gym', label: 'Commercial Gym Access' },
   { value: 'outdoor', label: 'Outdoor/Running' }
 ];

 const intensityOptions = [
   { value: 'low', label: 'Low - Gentle, recovery-focused' },
   { value: 'moderate', label: 'Moderate - Challenging but sustainable' },
   { value: 'high', label: 'High - Intense, pushing limits' },
   { value: 'variable', label: 'Variable - Mix of intensities' }
 ];

 const handleGenerateWorkout = handleSubmit(async (formData) => {
   setGenerationStep('assessing');
   
   try {
     const result = await generateWorkoutPlan({
       ...formData,
       duration_weeks: Number(formData.duration_weeks),
       workouts_per_week: Number(formData.workouts_per_week),
       workout_duration: Number(formData.workout_duration)
     });

     if (result.success) {
       setGenerationStep('complete');
       onWorkoutGenerated?.(result);
     }
   } catch (error) {
     console.error('Workout plan generation failed:', error);
     setGenerationStep(null);
   }
 });

 const generationSteps = {
   assessing: { message: 'Assessing your fitness level...', progress: 20 },
   planning: { message: 'Creating workout structure...', progress: 40 },
   selecting: { message: 'Selecting appropriate exercises...', progress: 60 },
   balancing: { message: 'Balancing muscle groups...', progress: 80 },
   finalizing: { message: 'Finalizing your workout plan...', progress: 95 },
   complete: { message: 'Workout plan generated!', progress: 100 }
 };

 if (generationStep && generationStep !== 'complete') {
   const step = generationSteps[generationStep];
   return (
     <Card className="text-center py-12">
       <div className="max-w-md mx-auto">
         <div className="w-16 h-16 bg-gradient-to-r from-orange-400 to-red-500 rounded-full mx-auto mb-6 flex items-center justify-center">
           <BoltIcon className="w-8 h-8 text-white animate-pulse" />
         </div>
         
         <h3 className="text-lg font-semibold text-gray-900 mb-2">
           Creating Your Workout Plan
         </h3>
         
         <p className="text-gray-600 mb-6">{step.message}</p>
         
         <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
           <div
             className="bg-gradient-to-r from-orange-400 to-red-500 h-2 rounded-full transition-all duration-500"
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
     title="Generate AI Workout Plan"
     subtitle="Create a personalized workout plan based on your fitness goals and preferences"
   >
     <form onSubmit={handleGenerateWorkout} className="space-y-6">
       {/* Basic Plan Settings */}
       <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
         <Input
           label="Plan Duration (weeks)"
           type="number"
           min="1"
           max="52"
           {...getFieldProps('duration_weeks')}
           {...getFieldState('duration_weeks')}
         />
         
         <Input
           label="Workouts Per Week"
           type="number"
           min="1"
           max="7"
           {...getFieldProps('workouts_per_week')}
           {...getFieldState('workouts_per_week')}
         />
         
         <Input
           label="Workout Duration (minutes)"
           type="number"
           min="15"
           max="180"
           {...getFieldProps('workout_duration')}
           {...getFieldState('workout_duration')}
         />
       </div>

       {/* Fitness Profile */}
       <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
         <Select
           label="Fitness Level"
           options={fitnessLevelOptions}
           {...getFieldProps('fitness_level')}
           {...getFieldState('fitness_level')}
         />
         
         <Select
           label="Primary Goal"
           options={primaryGoalOptions}
           {...getFieldProps('primary_goal')}
           {...getFieldState('primary_goal')}
         />
       </div>

       {/* Equipment and Preferences */}
       <div className="space-y-4">
         <Select
           label="Available Equipment"
           options={equipmentOptions}
           {...getFieldProps('available_equipment')}
           {...getFieldState('available_equipment')}
         />
         
         <Input
           label="Preferred Workout Types"
           placeholder="e.g., strength training, HIIT, yoga, running"
           {...getFieldProps('preferred_workout_types')}
           {...getFieldState('preferred_workout_types')}
           helpText="Optional: specify types you enjoy"
         />
         
         <Select
           label="Intensity Preference"
           options={intensityOptions}
           {...getFieldProps('intensity_preference')}
           {...getFieldState('intensity_preference')}
         />
       </div>

       {/* Limitations and Notes */}
       <Input
         label="Injuries or Limitations"
         placeholder="e.g., knee injury, lower back issues, time constraints"
         {...getFieldProps('injuries_limitations')}
         {...getFieldState('injuries_limitations')}
         helpText="Help us customize your plan safely"
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
         Generate My Workout Plan
       </Button>
     </form>
   </Card>
 );
};

export default WorkoutGenerator;