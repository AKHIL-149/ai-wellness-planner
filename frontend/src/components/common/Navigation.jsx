// frontend/src/components/common/Navigation.jsx

import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  ChartBarIcon,
  ChatBubbleLeftRightIcon,
  UserIcon,
  Cog6ToothIcon,
  HeartIcon,
} from '@heroicons/react/24/outline';

const Navigation = ({ className = '' }) => {
  const navigationItems = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: HomeIcon,
      description: 'Overview and insights',
    },
    {
      name: 'Meal Planning',
      href: '/meals',
      icon: HeartIcon,
      description: 'AI-powered nutrition plans',
    },
    {
      name: 'Workouts',
      href: '/workouts',
      icon: ChartBarIcon,
      description: 'Fitness plans and tracking',
    },
    {
      name: 'AI Chat',
      href: '/chat',
      icon: ChatBubbleLeftRightIcon,
      description: 'Personal wellness coach',
    },
    {
      name: 'Profile',
      href: '/profile',
      icon: UserIcon,
      description: 'Your health profile',
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Cog6ToothIcon,
      description: 'App preferences',
    },
  ];

  return (
    <nav className={`space-y-2 ${className}`}>
      {navigationItems.map((item) => (
        <NavLink
          key={item.name}
          to={item.href}
          className={({ isActive }) =>
            `group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
              isActive
                ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                : 'text-gray-700 hover:text-blue-700 hover:bg-gray-50'
            }`
          }
        >
          <item.icon
            className="mr-3 h-5 w-5 flex-shrink-0"
            aria-hidden="true"
          />
          <div className="flex-1">
            <div className="font-medium">{item.name}</div>
            <div className="text-xs text-gray-500 group-hover:text-gray-700">
              {item.description}
            </div>
          </div>
        </NavLink>
      ))}
    </nav>
  );
};

export default Navigation;