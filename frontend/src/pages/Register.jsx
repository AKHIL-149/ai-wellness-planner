// frontend/src/pages/Register.jsx

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from '../hooks/useForm';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Select from '../components/common/Select';
import Card from '../components/common/Card';
import { validators } from '../utils';
import { 
  EyeIcon, 
  EyeSlashIcon, 
  UserIcon, 
  EnvelopeIcon,
  LockClosedIcon,
  CalendarDaysIcon
} from '@heroicons/react/24/outline';

const Register = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [step, setStep] = useState(1); // Multi-step registration
  const { register, loading, error, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const validationRules = {
    // Step 1: Basic Info
    first_name: [validators.required, validators.minLength(2)],
    last_name: [validators.required, validators.minLength(2)],
    email: [validators.required, validators.email],
    password: [validators.required, validators.password],
    confirm_password: [
      validators.required,
      (value, formValues) => validators.confirmPassword(value, formValues.password)
    ],
    
    // Step 2: Health Info
    date_of_birth: [validators.required, validators.pastDate],
    gender: [validators.required],
    height_cm: [validators.required, validators.range(100, 250)],
    weight_kg: [validators.required, validators.range(30, 300)],
    activity_level: [validators.required],
    
    // Terms
    terms_accepted: [
      (value) => value ? '' : 'You must accept the terms and conditions'
    ],
  };

  const {
    values,
    errors,
    handleChange,
    handleSubmit,
    getFieldProps,
    getFieldState,
    validate,
  } = useForm({
    // Step 1
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm_password: '',
    
    // Step 2
    date_of_birth: '',
    gender: '',
    height_cm: '',
    weight_kg: '',
    activity_level: '',
    health_goals: [],
    
    // Terms
    terms_accepted: false,
    newsletter_opt_in: true,
  }, validationRules);

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
    'General Wellness',
  ];

  const handleNextStep = () => {
    // Validate current step
    const step1Fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password'];
    const hasStep1Errors = step1Fields.some(field => {
      const error = validate(field, values[field]);
      return error !== '';
    });

    if (!hasStep1Errors) {
      setStep(2);
    }
  };

  const handleRegister = handleSubmit(async (formData) => {
    const result = await register(formData);
    if (result.success) {
      navigate('/dashboard', { replace: true });
    }
  });

  const toggleHealthGoal = (goal) => {
    const currentGoals = values.health_goals || [];
    const updatedGoals = currentGoals.includes(goal)
      ? currentGoals.filter(g => g !== goal)
      : [...currentGoals, goal];
    setValue('health_goals', updatedGoals);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Logo and Header */}
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-blue-600 rounded-xl mx-auto mb-4 flex items-center justify-center">
            <span className="text-white font-bold text-2xl">AW</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">Create your account</h2>
          <p className="mt-2 text-gray-600">
            Join AI Wellness and start your health journey
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="flex items-center justify-center space-x-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
           step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
         }`}>
           1
         </div>
         <div className={`w-8 h-1 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`} />
         <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
           step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
         }`}>
           2
         </div>
       </div>

       {/* Registration Form */}
       <Card className="mt-8">
         <form className="space-y-6" onSubmit={step === 1 ? (e) => { e.preventDefault(); handleNextStep(); } : handleRegister}>
           {error && (
             <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
               <p className="text-sm text-red-600">{error}</p>
             </div>
           )}

           {step === 1 && (
             <>
               <div className="grid grid-cols-2 gap-4">
                 <Input
                   label="First Name"
                   leftIcon={UserIcon}
                   {...getFieldProps('first_name')}
                   {...getFieldState('first_name')}
                 />
                 <Input
                   label="Last Name"
                   {...getFieldProps('last_name')}
                   {...getFieldState('last_name')}
                 />
               </div>

               <Input
                 label="Email address"
                 type="email"
                 leftIcon={EnvelopeIcon}
                 {...getFieldProps('email')}
                 {...getFieldState('email')}
               />

               <div className="relative">
                 <Input
                   label="Password"
                   type={showPassword ? 'text' : 'password'}
                   leftIcon={LockClosedIcon}
                   {...getFieldProps('password')}
                   {...getFieldState('password')}
                 />
                 <button
                   type="button"
                   className="absolute right-3 top-9 text-gray-400 hover:text-gray-600"
                   onClick={() => setShowPassword(!showPassword)}
                 >
                   {showPassword ? <EyeSlashIcon className="w-5 h-5" /> : <EyeIcon className="w-5 h-5" />}
                 </button>
               </div>

               <div className="relative">
                 <Input
                   label="Confirm Password"
                   type={showConfirmPassword ? 'text' : 'password'}
                   leftIcon={LockClosedIcon}
                   {...getFieldProps('confirm_password')}
                   {...getFieldState('confirm_password')}
                 />
                 <button
                   type="button"
                   className="absolute right-3 top-9 text-gray-400 hover:text-gray-600"
                   onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                 >
                   {showConfirmPassword ? <EyeSlashIcon className="w-5 h-5" /> : <EyeIcon className="w-5 h-5" />}
                 </button>
               </div>

               <Button type="submit" fullWidth size="lg">
                 Continue
               </Button>
             </>
           )}

           {step === 2 && (
             <>
               <div className="grid grid-cols-2 gap-4">
                 <Input
                   label="Date of Birth"
                   type="date"
                   leftIcon={CalendarDaysIcon}
                   {...getFieldProps('date_of_birth')}
                   {...getFieldState('date_of_birth')}
                 />
                 <Select
                   label="Gender"
                   options={genderOptions}
                   {...getFieldProps('gender')}
                   {...getFieldState('gender')}
                 />
               </div>

               <div className="grid grid-cols-2 gap-4">
                 <Input
                   label="Height (cm)"
                   type="number"
                   min="100"
                   max="250"
                   {...getFieldProps('height_cm')}
                   {...getFieldState('height_cm')}
                 />
                 <Input
                   label="Weight (kg)"
                   type="number"
                   min="30"
                   max="300"
                   step="0.1"
                   {...getFieldProps('weight_kg')}
                   {...getFieldState('weight_kg')}
                 />
               </div>

               <Select
                 label="Activity Level"
                 options={activityLevelOptions}
                 {...getFieldProps('activity_level')}
                 {...getFieldState('activity_level')}
               />

               <div>
                 <label className="block text-sm font-medium text-gray-700 mb-3">
                   Health Goals (Optional)
                 </label>
                 <div className="grid grid-cols-2 gap-2">
                   {healthGoalOptions.map((goal) => (
                     <button
                       key={goal}
                       type="button"
                       onClick={() => toggleHealthGoal(goal)}
                       className={`p-2 text-sm rounded-lg border transition-colors ${
                         (values.health_goals || []).includes(goal)
                           ? 'bg-blue-50 border-blue-500 text-blue-700'
                           : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                       }`}
                     >
                       {goal}
                     </button>
                   ))}
                 </div>
               </div>

               <div className="space-y-3">
                 <div className="flex items-center">
                   <input
                     id="terms"
                     name="terms_accepted"
                     type="checkbox"
                     checked={values.terms_accepted}
                     onChange={handleChange}
                     className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                   />
                   <label htmlFor="terms" className="ml-2 block text-sm text-gray-900">
                     I accept the{' '}
                     <Link to="/terms" className="text-blue-600 hover:text-blue-500">
                       Terms and Conditions
                     </Link>
                   </label>
                 </div>
                 {errors.terms_accepted && (
                   <p className="text-sm text-red-600">{errors.terms_accepted}</p>
                 )}

                 <div className="flex items-center">
                   <input
                     id="newsletter"
                     name="newsletter_opt_in"
                     type="checkbox"
                     checked={values.newsletter_opt_in}
                     onChange={handleChange}
                     className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                   />
                   <label htmlFor="newsletter" className="ml-2 block text-sm text-gray-900">
                     Send me wellness tips and updates
                   </label>
                 </div>
               </div>

               <div className="flex space-x-3">
                 <Button
                   type="button"
                   variant="outline"
                   fullWidth
                   onClick={() => setStep(1)}
                 >
                   Back
                 </Button>
                 <Button
                   type="submit"
                   fullWidth
                   loading={loading}
                   size="lg"
                 >
                   Create Account
                 </Button>
               </div>
             </>
           )}

           <div className="text-center">
             <span className="text-sm text-gray-600">
               Already have an account?{' '}
               <Link
                 to="/login"
                 className="font-medium text-blue-600 hover:text-blue-500"
               >
                 Sign in
               </Link>
             </span>
           </div>
         </form>
       </Card>
     </div>
   </div>
 );
};

export default Register;