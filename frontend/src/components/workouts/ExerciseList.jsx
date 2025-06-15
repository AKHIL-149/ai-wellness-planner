// frontend/src/components/workouts/ExerciseList.jsx

import React, { useState } from 'react';
import { 
 MagnifyingGlassIcon,
 AdjustmentsHorizontalIcon,
 PlayIcon,
 InformationCircleIcon
} from '@heroicons/react/24/outline';
import Card from '../common/Card';
import Button from '../common/Button';
import Input from '../common/Input';
import Select from '../common/Select';
import Modal from '../common/Modal';

const ExerciseList = ({ exercises = [], onExerciseSelect, onSubstitute }) => {
 const [searchTerm, setSearchTerm] = useState('');
 const [categoryFilter, setCategoryFilter] = useState('all');
 const [difficultyFilter, setDifficultyFilter] = useState('all');
 const [equipmentFilter, setEquipmentFilter] = useState('all');
 const [selectedExercise, setSelectedExercise] = useState(null);
 const [showFilters, setShowFilters] = useState(false);

 // Get unique categories, difficulties, and equipment
 const categories = [...new Set(exercises.map(ex => ex.category))].filter(Boolean);
 const difficulties = [...new Set(exercises.map(ex => ex.difficulty))].filter(Boolean);
 const equipment = [...new Set(exercises.map(ex => ex.equipment))].filter(Boolean);

 // Filter exercises
 const filteredExercises = exercises.filter(exercise => {
   const matchesSearch = exercise.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        exercise.description?.toLowerCase().includes(searchTerm.toLowerCase());
   
   const matchesCategory = categoryFilter === 'all' || exercise.category === categoryFilter;
   const matchesDifficulty = difficultyFilter === 'all' || exercise.difficulty === difficultyFilter;
   const matchesEquipment = equipmentFilter === 'all' || exercise.equipment === equipmentFilter;
   
   return matchesSearch && matchesCategory && matchesDifficulty && matchesEquipment;
 });

 const getDifficultyColor = (difficulty) => {
   switch (difficulty?.toLowerCase()) {
     case 'beginner': return 'bg-green-100 text-green-800';
     case 'intermediate': return 'bg-yellow-100 text-yellow-800';
     case 'advanced': return 'bg-red-100 text-red-800';
     default: return 'bg-gray-100 text-gray-800';
   }
 };

 const getCategoryColor = (category) => {
   const colors = {
     'strength': 'bg-blue-100 text-blue-800',
     'cardio': 'bg-red-100 text-red-800',
     'flexibility': 'bg-green-100 text-green-800',
     'balance': 'bg-purple-100 text-purple-800',
     'sports': 'bg-orange-100 text-orange-800',
   };
   return colors[category?.toLowerCase()] || 'bg-gray-100 text-gray-800';
 };

 return (
   <>
     <Card title="Exercise Library" className="h-full flex flex-col">
       {/* Search and Filters */}
       <div className="space-y-3 mb-4">
         <div className="flex space-x-2">
           <div className="flex-1">
             <Input
               placeholder="Search exercises..."
               value={searchTerm}
               onChange={(e) => setSearchTerm(e.target.value)}
               leftIcon={MagnifyingGlassIcon}
             />
           </div>
           <Button
             variant="outline"
             icon={AdjustmentsHorizontalIcon}
             onClick={() => setShowFilters(!showFilters)}
           >
             Filters
           </Button>
         </div>

         {showFilters && (
           <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-3 bg-gray-50 rounded-lg">
             <Select
               value={categoryFilter}
               onChange={(e) => setCategoryFilter(e.target.value)}
               options={[
                 { value: 'all', label: 'All Categories' },
                 ...categories.map(cat => ({ value: cat, label: cat.replace('_', ' ').toUpperCase() }))
               ]}
             />
             <Select
               value={difficultyFilter}
               onChange={(e) => setDifficultyFilter(e.target.value)}
               options={[
                 { value: 'all', label: 'All Difficulties' },
                 ...difficulties.map(diff => ({ value: diff, label: diff.toUpperCase() }))
               ]}
             />
             <Select
               value={equipmentFilter}
               onChange={(e) => setEquipmentFilter(e.target.value)}
               options={[
                 { value: 'all', label: 'All Equipment' },
                 ...equipment.map(eq => ({ value: eq, label: eq.replace('_', ' ').toUpperCase() }))
               ]}
             />
           </div>
         )}
       </div>

       {/* Results Count */}
       <div className="text-sm text-gray-600 mb-3">
         {filteredExercises.length} exercise{filteredExercises.length !== 1 ? 's' : ''} found
       </div>

       {/* Exercise List */}
       <div className="flex-1 overflow-y-auto space-y-3">
         {filteredExercises.length === 0 ? (
           <div className="text-center py-8 text-gray-500">
             <MagnifyingGlassIcon className="w-12 h-12 mx-auto mb-3 text-gray-400" />
             <p>No exercises found matching your criteria</p>
           </div>
         ) : (
           filteredExercises.map((exercise) => (
             <div
               key={exercise.id}
               className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
               onClick={() => setSelectedExercise(exercise)}
             >
               <div className="flex items-start justify-between mb-2">
                 <h4 className="font-medium text-gray-900">{exercise.name}</h4>
                 <div className="flex space-x-1">
                   <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(exercise.category)}`}>
                     {exercise.category?.replace('_', ' ')}
                   </span>
                   <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(exercise.difficulty)}`}>
                     {exercise.difficulty}
                   </span>
                 </div>
               </div>

               {exercise.description && (
                 <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                   {exercise.description}
                 </p>
               )}

               <div className="flex items-center justify-between">
                 <div className="flex space-x-3 text-xs text-gray-500">
                   {exercise.equipment && (
                     <span>Equipment: {exercise.equipment.replace('_', ' ')}</span>
                   )}
                   {exercise.primary_muscles && exercise.primary_muscles.length > 0 && (
                     <span>
                       Targets: {exercise.primary_muscles.slice(0, 2).join(', ')}
                       {exercise.primary_muscles.length > 2 && ' +more'}
                     </span>
                   )}
                 </div>
                 
                 <div className="flex space-x-2">
                   <Button
                     size="sm"
                     variant="outline"
                     icon={InformationCircleIcon}
                     onClick={(e) => {
                       e.stopPropagation();
                       setSelectedExercise(exercise);
                     }}
                   >
                     Info
                   </Button>
                   {onExerciseSelect && (
                     <Button
                       size="sm"
                       icon={PlayIcon}
                       onClick={(e) => {
                         e.stopPropagation();
                         onExerciseSelect(exercise);
                       }}
                     >
                       Add
                     </Button>
                   )}
                 </div>
               </div>
             </div>
           ))
         )}
       </div>
     </Card>

     {/* Exercise Details Modal */}
     <Modal
       isOpen={!!selectedExercise}
       onClose={() => setSelectedExercise(null)}
       title={selectedExercise?.name}
       size="lg"
     >
       {selectedExercise && (
         <div className="space-y-6">
           {/* Exercise Image/Video */}
           {selectedExercise.image_url && (
             <img
               src={selectedExercise.image_url}
               alt={selectedExercise.name}
               className="w-full h-64 object-cover rounded-lg"
             />
           )}

           {/* Exercise Info */}
           <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
             <div className="text-center p-3 bg-gray-50 rounded-lg">
               <div className="text-sm font-medium">{selectedExercise.category?.replace('_', ' ')}</div>
               <div className="text-xs text-gray-500">Category</div>
             </div>
             <div className="text-center p-3 bg-gray-50 rounded-lg">
               <div className="text-sm font-medium">{selectedExercise.difficulty}</div>
               <div className="text-xs text-gray-500">Difficulty</div>
             </div>
             <div className="text-center p-3 bg-gray-50 rounded-lg">
               <div className="text-sm font-medium">{selectedExercise.equipment?.replace('_', ' ')}</div>
               <div className="text-xs text-gray-500">Equipment</div>
             </div>
             <div className="text-center p-3 bg-gray-50 rounded-lg">
               <div className="text-sm font-medium">{selectedExercise.calories_per_minute || 'N/A'}</div>
               <div className="text-xs text-gray-500">Cal/min</div>
             </div>
           </div>

           {/* Description */}
           {selectedExercise.description && (
             <div>
               <h4 className="text-lg font-semibold mb-2">Description</h4>
               <p className="text-gray-700">{selectedExercise.description}</p>
             </div>
           )}

           {/* Instructions */}
           {selectedExercise.instructions && (
             <div>
               <h4 className="text-lg font-semibold mb-3">Instructions</h4>
               <div className="prose prose-sm text-gray-700">
                 {selectedExercise.instructions.split('\n').map((instruction, index) => (
                   <p key={index} className="mb-2">{instruction}</p>
                 ))}
               </div>
             </div>
           )}

           {/* Muscle Groups */}
           {(selectedExercise.primary_muscles || selectedExercise.secondary_muscles) && (
             <div>
               <h4 className="text-lg font-semibold mb-3">Muscle Groups</h4>
               <div className="space-y-2">
                 {selectedExercise.primary_muscles && selectedExercise.primary_muscles.length > 0 && (
                   <div>
                     <div className="text-sm font-medium text-gray-700 mb-1">Primary:</div>
                     <div className="flex flex-wrap gap-1">
                       {selectedExercise.primary_muscles.map((muscle, index) => (
                         <span
                           key={index}
                           className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                         >
                           {muscle}
                         </span>
                       ))}
                     </div>
                   </div>
                 )}
                 {selectedExercise.secondary_muscles && selectedExercise.secondary_muscles.length > 0 && (
                   <div>
                     <div className="text-sm font-medium text-gray-700 mb-1">Secondary:</div>
                     <div className="flex flex-wrap gap-1">
                       {selectedExercise.secondary_muscles.map((muscle, index) => (
                         <span
                           key={index}
                           className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                         >
                           {muscle}
                         </span>
                       ))}
                     </div>
                   </div>
                 )}
               </div>
             </div>
           )}

           {/* Tips */}
           {selectedExercise.tips && (
             <div>
               <h4 className="text-lg font-semibold mb-2">Tips</h4>
               <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                 <p className="text-yellow-800 text-sm">{selectedExercise.tips}</p>
               </div>
             </div>
           )}

           {/* Action Buttons */}
           <div className="flex space-x-3">
             {onExerciseSelect && (
               <Button
                 fullWidth
                 icon={PlayIcon}
                 onClick={() => {
                   onExerciseSelect(selectedExercise);
                   setSelectedExercise(null);
                 }}
               >
                 Add to Workout
               </Button>
             )}
             {onSubstitute && (
               <Button
                 variant="outline"
                 fullWidth
                 onClick={() => {
                   onSubstitute(selectedExercise);
                   setSelectedExercise(null);
                 }}
               >
                 Find Substitutes
               </Button>
             )}
           </div>
         </div>
       )}
     </Modal>
   </>
 );
};

export default ExerciseList;