// frontend/src/components/layout/Sidebar.jsx

import React from 'react';
import Navigation from '../common/Navigation';

const Sidebar = () => {
  return (
    <div className="h-screen pt-6 pb-4 overflow-y-auto">
      <div className="px-3">
        <Navigation />
      </div>
      
      {/* Quick Stats or Recent Activity */}
      <div className="mt-8 px-3">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Quick Stats
        </h3>
        <div className="mt-2 space-y-2">
          <div className="bg-blue-50 rounded-lg p-3">
            <div className="text-sm font-medium text-blue-900">
              Today's Calories
            </div>
            <div className="text-lg font-bold text-blue-600">
              1,847 / 2,200
            </div>
          </div>
          
          <div className="bg-green-50 rounded-lg p-3">
            <div className="text-sm font-medium text-green-900">
              Workouts This Week
            </div>
            <div className="text-lg font-bold text-green-600">
              3 / 5
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;