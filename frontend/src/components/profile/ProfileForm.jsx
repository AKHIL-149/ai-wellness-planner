// frontend/src/components/profile/ProfileForm.jsx

import React, { useState, useEffect } from 'react';
import { useForm } from '../../hooks/useForm';
import { useAuth } from '../../hooks/useAuth';
import Button from '../common/Button';
import Input from '../common/Input';
import Select from '../common/Select';
import Card from '../common/Card';
import { validators, helpers } from '../../utils';
import { 
  UserIcon, 
  ScaleIcon, 
  HeartIcon,
  CalendarDaysIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';

const ProfileForm = ({ onSave, showHealthMetrics = true }) => {
  const { user, updateProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [healthMetrics, setHealthMetrics] = useState({});

  const validationRules = {
    first_name: [validators.required, validators.minLength(2)],
    last_name: [validators.required, validators.minLength(2)],
    email: [validators.required, validators.email],
    date_of_birth: [validators.required, validators.pastDate],
    gender: [validators.required],
    height_cm: [validators.required, validators.range(100, 250)],
    weight_kg: [validators.required, validators.range(30, 300)],
    activity_level: [validators.required],
  };

  const {
    values,
    errors,
    handleChange,
    handleSubmit,
    getFieldProps,
    getFieldState,
    setValue,
    reset,
  } = useForm({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    date_of_birth: user?.date_of_birth || '',
    gender: user?.gender || '',
    height_cm: user?.height_cm || '',
    weight_kg: user?.weight_kg || '',
    activity_level: user?.activity_level || '',
    health_goals: user?.health_goals || [],
    dietary_restrictions: user?.dietary_restrictions || '',
    medical_conditions: user?.medical_conditions || '',
    emergency_contact: user?.emergency_contact || '',
    phone: user?.phone || '',
  }, validationRules);

  // Calculate health metrics when relevant values change
  useEffect(() => {
    if (values.weight_kg && values.height_cm && values.date_of_birth && values.gender) {
      const age = new Date().getFullYear() - new Date(values.date_of_birth).getFullYear();
      const bmi = helpers.calculateBMI(values.weight_kg, values.height_cm);
      const bmr = helpers.calculateBMR(values.weight_kg, values.height_cm, age, values.gender);
      const tdee = helpers.calculateTDEE(bmr, values.activity_level);
      
      setHealthMetrics({
        age,
        bmi,
        bmiCategory: helpers.getBMICategory(bmi),
        bmr,
        tdee,
      });
    }
  }, [values.weight_kg, values.height_cm, values.date_of_birth, values.gender, values.activity_level]);

  const genderOptions = [
    { value: '', label: 'Select Gender' },
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' },
    { value: 'other', label: 'Other' },
    { value: 'prefer_not_to_say', label: 'Prefer not to say' },
  ];

  const activityLevelOptions = [
    { value: '', label: 'Select Activity Level' },
    { value: 'sedentary', label: 'Sedentary (little/no exercise)' },
    { value: 'lightly_active', label: 'Lightly Active (light exercise 1-3 days/week)' },
    { value: 'moderately_active', label: 'Moderately Active (moderate exercise 3-5 days/week)' },
    { value: 'very_active', label: 'Very Active (hard exercise 6-7 days/week)' },
    { value: 'extremely_active', label: 'Extremely Active (very hard exercise, physical job)' },
  ];

  const healthGoalOptions = [
    'Weight Loss',
    'Weight Gain',
    'Muscle Building',
    'Improved Endurance',
    'Better Sleep',
    'Stress Management',
    'Heart Health',
    'Diabetes Management',
    'General Wellness',
  ];

  const handleSave = handleSubmit(async (formData) => {
    try {
      const result = await updateProfile(formData);
      if (result.success) {
        setIsEditing(false);
        onSave?.(result.user);
      }
    } catch (error) {
      console.error('Profile update failed:', error);
    }
  });

  const handleCancel = () => {
    reset();
    setIsEditing(false);
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const toggleHealthGoal = (goal) => {
    const currentGoals = values.health_goals || [];
    const updatedGoals = currentGoals.includes(goal)
      ? currentGoals.filter(g => g !== goal)
      : [...currentGoals, goal];
    setValue('health_goals', updatedGoals);
  };

  return (
    <div className="space-y-6">
      {/* Basic Information */}
      <Card
        title="Personal Information"
        subtitle="Your basic profile details"
      >
        <form onSubmit={handleSave} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="First Name"
              {...getFieldProps('first_name')}
              {...getFieldState('first_name')}
              disabled={!isEditing}
              leftIcon={UserIcon}
            />
            
            <Input
              label="Last Name"
              {...getFieldProps('last_name')}
              {...getFieldState('last_name')}
              disabled={!isEditing}
            />
            
            <Input
              label="Email"
              type="email"
              {...getFieldProps('email')}
              {...getFieldState('email')}
              disabled={!isEditing}
            />
            
            <Input
              label="Phone"
              type="tel"
              {...getFieldProps('phone')}
              {...getFieldState('phone')}
              disabled={!isEditing}
              helpText="Optional"
            />
            
            <Input
              label="Date of Birth"
              type="date"
              {...getFieldProps('date_of_birth')}
              {...getFieldState('date_of_birth')}
              disabled={!isEditing}
              leftIcon={CalendarDaysIcon}
            />
            
            <Select
              label="Gender"
              options={genderOptions}
              {...getFieldProps('gender')}
              {...getFieldState('gender')}
              disabled={!isEditing}
            />
          </div>

          {/* Physical Metrics */}
          <div className="border-t border-gray-200 pt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Physical Metrics</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="Height (cm)"
                type="number"
                min="100"
                max="250"
                {...getFieldProps('height_cm')}
                {...getFieldState('height_cm')}
                disabled={!isEditing}
                leftIcon={ScaleIcon}
              />
              
              <Input
                label="Weight (kg)"
                type="number"
                min="30"
                max="300"
                step="0.1"
                {...getFieldProps('weight_kg')}
                {...getFieldState('weight_kg')}
                disabled={!isEditing}
                leftIcon={ScaleIcon}
              />
              
              <Select
                label="Activity Level"
                options={activityLevelOptions}
                {...getFieldProps('activity_level')}
                {...getFieldState('activity_level')}
                disabled={!isEditing}
              />
            </div>
          </div>

          {/* Health Goals */}
          <div className="border-t border-gray-200 pt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Health Goals</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {healthGoalOptions.map((goal) => (
                <button
                  key={goal}
                  type="button"
                  onClick={() => toggleHealthGoal(goal)}
                  disabled={!isEditing}
                  className={`p-3 text-sm rounded-lg border transition-colors ${
                    (values.health_goals || []).includes(goal)
                      ? 'bg-blue-50 border-blue-500 text-blue-700'
                      : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                  } ${!isEditing ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  {goal}
                </button>
              ))}
            </div>
          </div>

          {/* Health Information */}
          <div className="border-t border-gray-200 pt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Health Information</h3>
            <div className="space-y-4">
              <Input
                label="Dietary Restrictions"
                placeholder="e.g., gluten-free, nut allergies, lactose intolerant"
                {...getFieldProps('dietary_restrictions')}
                {...getFieldState('dietary_restrictions')}
                disabled={!isEditing}
                helpText="Any allergies or dietary restrictions"
              />
              
              <Input
                label="Medical Conditions"
                placeholder="e.g., diabetes, hypertension, heart disease"
                {...getFieldProps('medical_conditions')}
                {...getFieldState('medical_conditions')}
                disabled={!isEditing}
                leftIcon={ExclamationTriangleIcon}
                helpText="Optional - helps us provide better recommendations"
              />
              
              <Input
                label="Emergency Contact"
                placeholder="Name and phone number"
                {...getFieldProps('emergency_contact')}
                {...getFieldState('emergency_contact')}
                disabled={!isEditing}
                helpText="Optional - for emergencies during workouts"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            {isEditing ? (
              <>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleCancel}
                >
                  Cancel
                </Button>
                <Button type="submit">
                  Save Changes
                </Button>
              </>
            ) : (
              <Button
                type="button"
                onClick={handleEdit}
                icon={UserIcon}
              >
                Edit Profile
              </Button>
            )}
          </div>
        </form>
      </Card>

      {/* Health Metrics Display */}
      {showHealthMetrics && healthMetrics.bmi && (
        <Card
          title="Health Metrics"
          subtitle="Calculated from your profile information"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {healthMetrics.age}
              </div>
              <div className="text-sm text-gray-500">Age (years)</div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {healthMetrics.bmi.toFixed(1)}
              </div>
              <div className="text-sm text-gray-500">BMI</div>
              <div className={`text-xs mt-1 ${healthMetrics.bmiCategory.color}`}>
                {healthMetrics.bmiCategory.category}
              </div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {Math.round(healthMetrics.bmr)}
              </div>
              <div className="text-sm text-gray-500">BMR (cal/day)</div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {Math.round(healthMetrics.tdee)}
              </div>
              <div className="text-sm text-gray-500">TDEE (cal/day)</div>
            </div>
          </div>
          
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>BMR:</strong> Basal Metabolic Rate - calories burned at rest<br />
              <strong>TDEE:</strong> Total Daily Energy Expenditure - total calories burned per day
            </p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ProfileForm;