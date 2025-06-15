// frontend/src/components/workouts/WorkoutCard.jsx

import React, { useState } from 'react';
import { 
 ClockIcon, 
 FireIcon, 
 BoltIcon,
 PlayIcon,
 PauseIcon,
 CheckIcon,
 ChartBarIcon
} from '@heroicons/react/24/outline';
import Card from '../common/Card';
import Button from '../common/Button';
import Modal from '../common/Modal';

const WorkoutCard = ({ workout, onStart, onComplete, showProgress = true }) => {
 const [showDetails, setShowDetails] = useState(false);
 const [isStarted, setIsStarted] = useState(workout.status === 'in_progress');

 const handleStart = () => {
   setIsStarted(true);
   onStart?.(workout.id);
 };

 const handleComplete = () => {
   setIsStarted(false);
   onComplete?.(workout.id);
 };

 const formatDuration = (minutes) => {
   if (minutes < 60) return `${minutes}m`;
   const hours = Math.floor(minutes / 60);
   const mins = minutes % 60;
   return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
 };

 const getDifficultyColor = (difficulty) => {
   switch (difficulty?.toLowerCase()) {
     case 'easy': return 'bg-green-100 text-green-800';
     case 'moderate': return 'bg-yellow-100 text-yellow-800';
     case 'hard': return 'bg-red-100 text-red-800';
     default: return 'bg-gray-100 text-gray-800';
   }
 };

 const getStatusColor = (status) => {
   switch (status) {
     case 'completed': return 'bg-green-100 text-green-800';
     case 'in_progress': return 'bg-blue-100 text-blue-800';
     case 'scheduled': return 'bg-gray-100 text-gray-800';
     case 'skipped': return 'bg-red-100 text-red-800';
     default: return 'bg-gray-100 text-gray-800';
   }
 };

 return (
   <>
     <Card className="hover:shadow-lg transition-shadow duration-200">
       <div className="p-4">
         {/* Header */}
         <div className="flex items-start justify-between mb-3">
           <div className="flex-1">
             <h3 className="text-lg font-semibold text-gray-900 mb-1">
               {workout.name}
             </h3>
             <p className="text-sm text-gray-600">
               {workout.workout_type?.replace('_', ' ')?.toUpperCase()}
             </p>
           </div>
           <div className="flex flex-col items-end space-y-1">
             <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(workout.status)}`}>
               {workout.status?.replace('_', ' ')?.toUpperCase()}
             </span>
             {workout.difficulty && (
               <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(workout.difficulty)}`}>
                 {workout.difficulty}
               </span>
             )}
           </div>
         </div>

         {/* Description */}
         {workout.description && (
           <p className="text-gray-600 text-sm mb-4 line-clamp-2">
             {workout.description}
           </p>
         )}

         {/* Quick Stats */}
         <div className="grid grid-cols-3 gap-3 mb-4">
           <div className="text-center p-2 bg-gray-50 rounded-lg">
             <ClockIcon className="w-4 h-4 mx-auto mb-1 text-gray-600" />
             <div className="text-xs font-medium text-gray-900">
               {formatDuration(workout.estimated_duration || workout.actual_duration || 30)}
             </div>
             <div className="text-xs text-gray-500">Duration</div>
           </div>
           
           <div className="text-center p-2 bg-gray-50 rounded-lg">
             <FireIcon className="w-4 h-4 mx-auto mb-1 text-gray-600" />
             <div className="text-xs font-medium text-gray-900">
               {workout.estimated_calories || workout.total_calories_burned || '~200'}
             </div>
             <div className="text-xs text-gray-500">Calories</div>
           </div>
           
           <div className="text-center p-2 bg-gray-50 rounded-lg">
             <BoltIcon className="w-4 h-4 mx-auto mb-1 text-gray-600" />
             <div className="text-xs font-medium text-gray-900">
               {workout.exercises?.length || workout.total_exercises || 6}
             </div>
             <div className="text-xs text-gray-500">Exercises</div>
           </div>
         </div>

         {/* Progress Bar */}
         {showProgress && workout.exercises && (
           <div className="mb-4">
             <div className="flex justify-between text-xs text-gray-500 mb-1">
               <span>Progress</span>
               <span>{workout.completed_exercises || 0} / {workout.exercises.length}</span>
             </div>
             <div className="w-full bg-gray-200 rounded-full h-1.5">
               <div
                 className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                 style={{ 
                   width: `${workout.exercises.length > 0 ? ((workout.completed_exercises || 0) / workout.exercises.length) * 100 : 0}%` 
                 }}
               />
             </div>
           </div>
         )}

         {/* Exercise Preview */}
         {workout.exercises && workout.exercises.length > 0 && (
           <div className="mb-4">
             <h4 className="text-sm font-medium text-gray-700 mb-2">Exercises</h4>
             <div className="space-y-1">
               {workout.exercises.slice(0, 3).map((exercise, index) => (
                 <div key={index} className="flex items-center text-xs text-gray-600">
                   <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mr-2 flex-shrink-0" />
                   <span className="truncate">
                     {exercise.exercise_name || exercise.name} - 
                     {exercise.sets_planned && ` ${exercise.sets_planned} sets`}
                     {exercise.reps_planned && ` × ${exercise.reps_planned} reps`}
                     {exercise.duration_planned && ` × ${exercise.duration_planned}s`}
                   </span>
                 </div>
               ))}
               {workout.exercises.length > 3 && (
                 <div className="text-xs text-gray-500">
                   +{workout.exercises.length - 3} more exercises
                 </div>
               )}
             </div>
           </div>
         )}

         {/* Action Buttons */}
         <div className="flex space-x-2">
           <Button
             variant="outline"
             size="sm"
             fullWidth
             onClick={() => setShowDetails(true)}
           >
             View Details
           </Button>
           
           {workout.status === 'scheduled' && (
             <Button
               size="sm"
               fullWidth
               icon={PlayIcon}
               onClick={handleStart}
             >
               Start Workout
             </Button>
           )}
           
           {workout.status === 'in_progress' && (
             <Button
               size="sm"
               fullWidth
               icon={CheckIcon}
               onClick={handleComplete}
             >
               Complete
             </Button>
           )}
           
           {workout.status === 'completed' && (
             <Button
               variant="outline"
               size="sm"
               fullWidth
               icon={ChartBarIcon}
             >
               View Results
             </Button>
           )}
         </div>
       </div>
     </Card>

     {/* Workout Details Modal */}
     <Modal
       isOpen={showDetails}
       onClose={() => setShowDetails(false)}
       title={workout.name}
       size="lg"
     >
       <div className="space-y-6">
         {/* Workout Overview */}
         <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
           <div className="text-center p-3 bg-gray-50 rounded-lg">
             <ClockIcon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
             <div className="text-sm font-medium">
               {formatDuration(workout.estimated_duration || 30)}
             </div>
             <div className="text-xs text-gray-500">Duration</div>
           </div>
           <div className="text-center p-3 bg-gray-50 rounded-lg">
             <FireIcon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
             <div className="text-sm font-medium">
               {workout.estimated_calories || '~200'}
             </div>
             <div className="text-xs text-gray-500">Calories</div>
           </div>
           <div className="text-center p-3 bg-gray-50 rounded-lg">
             <BoltIcon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
             <div className="text-sm font-medium">
               {workout.exercises?.length || 6}
             </div>
             <div className="text-xs text-gray-500">Exercises</div>
           </div>
           <div className="text-center p-3 bg-gray-50 rounded-lg">
             <ChartBarIcon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
             <div className="text-sm font-medium">{workout.difficulty || 'Moderate'}</div>
             <div className="text-xs text-gray-500">Difficulty</div>
           </div>
         </div>

         {/* Description */}
         {workout.description && (
           <div>
             <h4 className="text-lg font-semibold mb-2">Description</h4>
             <p className="text-gray-700">{workout.description}</p>
           </div>
         )}

         {/* Exercise List */}
         {workout.exercises && workout.exercises.length > 0 && (
           <div>
             <h4 className="text-lg font-semibold mb-3">Exercises</h4>
             <div className="space-y-3">
               {workout.exercises.map((exercise, index) => (
                 <div
                   key={index}
                   className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                 >
                   <div className="flex items-center space-x-3">
                     <span className="w-6 h-6 bg-blue-500 text-white text-sm font-medium rounded-full flex items-center justify-center">
                       {index + 1}
                     </span>
                     <div>
                       <div className="font-medium text-gray-900">
                         {exercise.exercise_name || exercise.name}
                       </div>
                       {exercise.description && (
                         <div className="text-sm text-gray-600">
                           {exercise.description}
                         </div>
                       )}
                     </div>
                   </div>
                   <div className="text-sm text-gray-600 text-right">
                     {exercise.sets_planned && <div>{exercise.sets_planned} sets</div>}
                     {exercise.reps_planned && <div>{exercise.reps_planned} reps</div>}
                     {exercise.duration_planned && <div>{exercise.duration_planned}s</div>}
                     {exercise.weight_planned && <div>{exercise.weight_planned}kg</div>}
                   </div>
                 </div>
               ))}
             </div>
           </div>
         )}

         {/* Workout Notes */}
         {workout.notes && (
           <div>
             <h4 className="text-lg font-semibold mb-2">Notes</h4>
             <p className="text-gray-700">{workout.notes}</p>
           </div>
         )}
       </div>
     </Modal>
   </>
 );
};

export default WorkoutCard;