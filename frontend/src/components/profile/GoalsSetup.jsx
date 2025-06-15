// frontend/src/components/profile/GoalsSetup.jsx

import React, { useState } from 'react';
import { useForm } from '../../hooks/useForm';
import Button from '../common/Button';
import Input from '../common/Input';
import Select from '../common/Select';
import Card from '../common/Card';
import Modal from '../common/Modal';
import { validators, formatters } from '../../utils';
import { 
  TrophyIcon, 
  PlusIcon, 
  TrashIcon,
  CalendarDaysIcon,
  ChartBarIcon,
  HeartIcon
} from '@heroicons/react/24/outline';

const GoalsSetup = ({ goals = [], onGoalCreate, onGoalUpdate, onGoalDelete }) => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingGoal, setEditingGoal] = useState(null);

  const goalTypes = [
    { value: 'weight_loss', label: 'Weight Loss', icon: '📉', unit: 'kg' },
    { value: 'weight_gain', label: 'Weight Gain', icon: '📈', unit: 'kg' },
    { value: 'muscle_gain', label: 'Muscle Gain', icon: '💪', unit: 'kg' },
    { value: 'strength', label: 'Strength Improvement', icon: '🏋️', unit: 'kg' },
    { value: 'endurance', label: 'Endurance', icon: '🏃', unit: 'minutes' },
    { value: 'flexibility', label: 'Flexibility', icon: '🧘', unit: 'cm' },
    { value: 'body_fat', label: 'Body Fat Reduction', icon: '📊', unit: '%' },
    { value: 'steps', label: 'Daily Steps', icon: '👣', unit: 'steps' },
    { value: 'workouts', label: 'Workout Frequency', icon: '🏋️', unit: 'per week' },
    { value: 'custom', label: 'Custom Goal', icon: '🎯', unit: 'custom' },
  ];

  const validationRules = {
    title: [validators.required, validators.minLength(3)],
    goal_type: [validators.required],
    target_value: [validators.required, validators.min(0.1)],
    target_date: [validators.required, validators.futureDate],
    description: [validators.minLength(10)],
  };

  const {
    values,
    errors,
    handleChange,
    handleSubmit,
    getFieldProps,
    getFieldState,
    reset,
  } = useForm({
    title: '',
    description: '',
    goal_type: '',
    target_value: '',
    unit: '',
    target_date: '',
    current_value: 0,
  }, validationRules);

  const handleCreateGoal = handleSubmit(async (formData) => {
    try {
      const selectedGoalType = goalTypes.find(type => type.value === formData.goal_type);
      const goalData = {
        ...formData,
        unit: selectedGoalType?.unit || formData.unit,
        target_value: Number(formData.target_value),
        current_value: Number(formData.current_value),
      };

      if (editingGoal) {
        await onGoalUpdate?.(editingGoal.id, goalData);
      } else {
        await onGoalCreate?.(goalData);
      }

      setShowCreateModal(false);
      setEditingGoal(null);
      reset();
    } catch (error) {
      console.error('Goal creation/update failed:', error);
    }
  });

  const handleEditGoal = (goal) => {
    setEditingGoal(goal);
    // Populate form with goal data
    Object.keys(goal).forEach(key => {
      if (values.hasOwnProperty(key)) {
        setValue(key, goal[key]);
      }
    });
    setShowCreateModal(true);
  };

  const handleDeleteGoal = async (goalId) => {
    if (window.confirm('Are you sure you want to delete this goal?')) {
      await onGoalDelete?.(goalId);
    }
  };

  const getGoalIcon = (goalType) => {
    const type = goalTypes.find(t => t.value === goalType);
    return type?.icon || '🎯';
  };

  const getProgressColor = (percentage) => {
    if (percentage >= 100) return 'text-green-600 bg-green-100';
    if (percentage >= 75) return 'text-blue-600 bg-blue-100';
    if (percentage >= 50) return 'text-yellow-600 bg-yellow-100';
    if (percentage >= 25) return 'text-orange-600 bg-orange-100';
    return 'text-red-600 bg-red-100';
  };

  const calculateDaysRemaining = (targetDate) => {
    const today = new Date();
    const target = new Date(targetDate);
    const diffTime = target - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  return (
    <>
      <Card
        title="Your Goals"
        subtitle="Track your health and fitness objectives"
        className="mb-6"
      >
        <div className="flex justify-between items-center mb-6">
          <div className="text-sm text-gray-600">
            {goals.length} active goal{goals.length !== 1 ? 's' : ''}
          </div>
          <Button
            icon={PlusIcon}
            onClick={() => setShowCreateModal(true)}
          >
            Add New Goal
          </Button>
        </div>

        {goals.length === 0 ? (
          <div className="text-center py-12">
            <TrophyIcon className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No goals set yet
            </h3>
            <p className="text-gray-600 mb-4">
              Set your first health or fitness goal to start tracking your progress
            </p>
            <Button
              icon={PlusIcon}
              onClick={() => setShowCreateModal(true)}
            >
              Create Your First Goal
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {goals.map((goal) => {
              const progress = (goal.current_value / goal.target_value) * 100;
              const daysRemaining = calculateDaysRemaining(goal.target_date);
              const progressColors = getProgressColor(progress);

              return (
                <div
                  key={goal.id}
                  className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl">{getGoalIcon(goal.goal_type)}</span>
                      <div>
                        <h4 className="font-semibold text-gray-900">{goal.title}</h4>
                        <p className="text-sm text-gray-600">{goal.description}</p>
                      </div>
                    </div>
                    <div className="flex space-x-1">
                      <button
                        onClick={() => handleEditGoal(goal)}
                        className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                      >
                        <ChartBarIcon className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteGoal(goal.id)}
                        className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-3">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Progress</span>
                      <span className="font-medium">
                        {goal.current_value} / {goal.target_value} {goal.unit}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          progress >= 100 ? 'bg-green-500' : 
                          progress >= 75 ? 'bg-blue-500' : 
                          progress >= 50 ? 'bg-yellow-500' : 
                          progress >= 25 ? 'bg-orange-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(progress, 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>{Math.round(progress)}% complete</span>
                      <span>
                        {daysRemaining > 0 ? `${daysRemaining} days left` : 'Overdue'}
                      </span>
                    </div>
                  </div>

                  {/* Goal Stats */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className={`p-2 rounded ${progressColors}`}>
                      <div className="font-medium">{Math.round(progress)}%</div>
                      <div>Complete</div>
                    </div>
                    <div className="p-2 bg-gray-100 rounded">
                      <div className="font-medium">
                        {formatters.date(goal.target_date, 'MMM dd')}
                      </div>
                      <div>Target Date</div>
                    </div>
                  </div>

                  {/* Quick Update */}
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        placeholder="Update progress"
                        className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            const newValue = Number(e.target.value);
                            if (newValue >= 0) {
                              onGoalUpdate?.(goal.id, { current_value: newValue });
                              e.target.value = '';
                            }
                          }
                        }}
                      />
                      <span className="text-xs text-gray-500">{goal.unit}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Create/Edit Goal Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
          setEditingGoal(null);
          reset();
        }}
        title={editingGoal ? 'Edit Goal' : 'Create New Goal'}
        size="lg"
      >
        <form onSubmit={handleCreateGoal} className="space-y-6">
          <Input
            label="Goal Title"
            placeholder="e.g., Lose 10kg for summer"
            {...getFieldProps('title')}
            {...getFieldState('title')}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select
              label="Goal Type"
              options={[
                { value: '', label: 'Select goal type' },
                ...goalTypes.map(type => ({
                  value: type.value,
                  label: `${type.icon} ${type.label}`
                }))
              ]}
              {...getFieldProps('goal_type')}
              {...getFieldState('goal_type')}
              onChange={(e) => {
                handleChange(e);
                const selectedType = goalTypes.find(type => type.value === e.target.value);
                if (selectedType) {
                  setValue('unit', selectedType.unit);
                }
              }}
            />

            <Input
              label="Target Date"
              type="date"
              {...getFieldProps('target_date')}
              {...getFieldState('target_date')}
              leftIcon={CalendarDaysIcon}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Target Value"
              type="number"
              step="0.1"
              min="0.1"
              {...getFieldProps('target_value')}
              {...getFieldState('target_value')}
            />

            <Input
              label="Current Value"
              type="number"
              step="0.1"
              min="0"
              {...getFieldProps('current_value')}
              {...getFieldState('current_value')}
            />

            <Input
              label="Unit"
              value={goalTypes.find(type => type.value === values.goal_type)?.unit || values.unit}
              disabled={values.goal_type !== 'custom'}
              onChange={handleChange}
              name="unit"
            />
          </div>

          <Input
            label="Description"
            placeholder="Describe your goal and motivation"
            {...getFieldProps('description')}
            {...getFieldState('description')}
            helpText="Optional - helps keep you motivated"
          />

          <div className="flex justify-end space-x-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setShowCreateModal(false);
                setEditingGoal(null);
                reset();
              }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              icon={editingGoal ? HeartIcon : TrophyIcon}
            >
              {editingGoal ? 'Update Goal' : 'Create Goal'}
            </Button>
          </div>
        </form>
      </Modal>
    </>
  );
};

export default GoalsSetup;