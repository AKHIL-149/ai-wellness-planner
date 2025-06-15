// frontend/src/pages/Profile.jsx

import React, { useState, useEffect } from 'react';
import { Tab } from '@headlessui/react';
import ProfileForm from '../components/profile/ProfileForm';
import GoalsSetup from '../components/profile/GoalsSetup';
import { useAuth } from '../hooks/useAuth';
import { useApi } from '../hooks/useApi';
import { fitnessAPI } from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner';

const Profile = () => {
 const { user } = useAuth();
 const [goals, setGoals] = useState([]);
 const [activeTab, setActiveTab] = useState(0);

 const {
   data: goalsData,
   loading: goalsLoading,
   execute: fetchGoals,
 } = useApi(fitnessAPI.getFitnessGoals, [], { autoFetch: true });

 useEffect(() => {
   if (goalsData) {
     setGoals(goalsData);
   }
 }, [goalsData]);

 const handleGoalCreate = async (goalData) => {
   try {
     const newGoal = await fitnessAPI.createFitnessGoal(goalData);
     setGoals(prev => [...prev, newGoal]);
   } catch (error) {
     console.error('Failed to create goal:', error);
   }
 };

 const handleGoalUpdate = async (goalId, updates) => {
   try {
     // Update goal via API
     await fitnessAPI.updateGoalProgress(goalId, updates);
     
     // Update local state
     setGoals(prev => prev.map(goal => 
       goal.id === goalId ? { ...goal, ...updates } : goal
     ));
   } catch (error) {
     console.error('Failed to update goal:', error);
   }
 };

 const handleGoalDelete = async (goalId) => {
   try {
     // Delete via API (you'll need to implement this endpoint)
     // await fitnessAPI.deleteGoal(goalId);
     
     // Update local state
     setGoals(prev => prev.filter(goal => goal.id !== goalId));
   } catch (error) {
     console.error('Failed to delete goal:', error);
   }
 };

 const tabs = [
   { name: 'Profile Information', component: ProfileForm },
   { name: 'Goals & Objectives', component: GoalsSetup },
 ];

 if (goalsLoading) {
   return <LoadingSpinner size="lg" text="Loading profile..." />;
 }

 return (
   <div className="space-y-6">
     {/* Page Header */}
     <div>
       <h1 className="text-2xl font-bold text-gray-900">Profile Settings</h1>
       <p className="mt-1 text-gray-600">
         Manage your personal information and health goals
       </p>
     </div>

     {/* Tab Navigation */}
     <Tab.Group selectedIndex={activeTab} onChange={setActiveTab}>
       <Tab.List className="flex space-x-1 rounded-xl bg-blue-900/20 p-1">
         {tabs.map((tab, index) => (
           <Tab
             key={tab.name}
             className={({ selected }) =>
               `w-full rounded-lg py-2.5 text-sm font-medium leading-5 text-blue-700 ${
                 selected
                   ? 'bg-white shadow'
                   : 'text-blue-100 hover:bg-white/[0.12] hover:text-white'
               }`
             }
           >
             {tab.name}
           </Tab>
         ))}
       </Tab.List>

       <Tab.Panels className="mt-6">
         <Tab.Panel>
           <ProfileForm showHealthMetrics={true} />
         </Tab.Panel>
         
         <Tab.Panel>
           <GoalsSetup
             goals={goals}
             onGoalCreate={handleGoalCreate}
             onGoalUpdate={handleGoalUpdate}
             onGoalDelete={handleGoalDelete}
           />
         </Tab.Panel>
       </Tab.Panels>
     </Tab.Group>
   </div>
 );
};

export default Profile;