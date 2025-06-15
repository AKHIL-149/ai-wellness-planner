// frontend/src/pages/Dashboard.jsx

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  ChartBarIcon, 
  FireIcon, 
  HeartIcon,
  TrophyIcon,
  ClockIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';
import NutritionCard from '../components/meals/NutritionCard';
import { useAuth } from '../hooks/useAuth';
import { useApi } from '../hooks/useApi';
import { nutritionAPI, fitnessAPI } from '../services/api';
import { formatters, helpers } from '../utils';

const Dashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const [nutritionDash, fitnessDash] = await Promise.all([
          nutritionAPI.getDashboard(),
          fitnessAPI.getDashboard(),
        ]);
        
        setDashboardData({
          nutrition: nutritionDash,
          fitness: fitnessDash,
        });
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return <LoadingSpinner size="lg" text="Loading dashboard..." />;
  }

  const quickStats = [
    {
      name: "Today's Calories",
      value: dashboardData?.nutrition?.daily_calories_consumed || 0,
      target: dashboardData?.nutrition?.daily_calorie_target || 2000,
      unit: 'kcal',
      icon: FireIcon,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      link: '/meals',
    },
    {
      name: 'Workouts This Week',
      value: dashboardData?.fitness?.weekly_workouts || 0,
      target: dashboardData?.fitness?.weekly_workout_target || 5,
      unit: 'workouts',
      icon: ChartBarIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      link: '/workouts',
    },
    {
      name: 'Active Goals',
      value: dashboardData?.fitness?.active_goals || 0,
      target: null,
      unit: 'goals',
      icon: TrophyIcon,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      link: '/profile',
    },
    {
      name: 'Streak Days',
      value: dashboardData?.nutrition?.nutrition_streak || 0,
      target: null,
      unit: 'days',
      icon: HeartIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      link: '/meals',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">
          Welcome back, {user?.first_name || 'there'}! 👋
        </h1>
        <p className="text-blue-100">
          Here's your wellness summary for today. Keep up the great work!
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {quickStats.map((stat) => {
          const percentage = stat.target ? helpers.calculateProgress(stat.value, stat.target) : null;
          const Icon = stat.icon;
          
          return (
            <Link key={stat.name} to={stat.link}>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <div className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-600">
                        {stat.name}
                      </p>
                      <div className="flex items-baseline mt-1">
                        <p className="text-2xl font-semibold text-gray-900">
                          {formatters.number(stat.value)}
                        </p>
                        {stat.target && (
                          <p className="ml-1 text-sm text-gray-500">
                            / {formatters.number(stat.target)} {stat.unit}
                          </p>
                        )}
                      </div>
                      {percentage !== null && (
                        <div className="mt-2">
                          <div className="flex items-center">
                            <div className="w-full bg-gray-200 rounded-full h-1.5 mr-2">
                              <div
                                className={`h-1.5 rounded-full ${
                                  percentage >= 100 ? 'bg-green-500' : 
                                  percentage >= 70 ? 'bg-blue-500' : 'bg-yellow-500'
                                }`}
                                style={{ width: `${Math.min(percentage, 100)}%` }}
                              />
                            </div>
                            <span className="text-xs text-gray-500">
                              {formatters.percentage(percentage, 0)}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                    <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                      <Icon className={`w-6 h-6 ${stat.color}`} />
                    </div>
                  </div>
                </div>
              </Card>
            </Link>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Nutrition Overview */}
        <div className="lg:col-span-2">
          <NutritionCard
            title="Today's Nutrition"
            current={dashboardData?.nutrition?.daily_nutrition || {}}
            target={dashboardData?.nutrition?.nutrition_targets || {}}
            className="h-full"
          />
        </div>

        {/* Quick Actions */}
        <Card title="Quick Actions" className="h-fit">
          <div className="space-y-3">
            <Button
              fullWidth
              variant="outline"
              as={Link}
              to="/chat"
              icon={HeartIcon}
            >
              Ask AI Coach
            </Button>
            <Button
              fullWidth
              variant="outline"
              as={Link}
              to="/meals/generate"
              icon={FireIcon}
            >
              Generate Meal Plan
            </Button>
            <Button
              fullWidth
              variant="outline"
              as={Link}
              to="/workouts/generate"
              icon={ChartBarIcon}
            >
              Create Workout
            </Button>
            <Button
              fullWidth
              variant="outline"
              as={Link}
              to="/profile"
              icon={TrophyIcon}
            >
              Set New Goal
            </Button>
          </div>
        </Card>
      </div>

      {/* Recent Activity & Upcoming */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Meals */}
        <Card title="Recent Meals" className="h-96">
          <div className="space-y-3 h-full overflow-y-auto">
            {dashboardData?.nutrition?.recent_meals?.length > 0 ? (
              dashboardData.nutrition.recent_meals.map((meal, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{meal.name}</h4>
                    <p className="text-sm text-gray-500">
                      {formatters.relativeTime(meal.consumed_at)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {formatters.calories(meal.calories)}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <FireIcon className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                  <p>No meals logged today</p>
                  <Button size="sm" as={Link} to="/meals" className="mt-2">
                    Log Your First Meal
                  </Button>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Upcoming Workouts */}
        <Card title="Upcoming Workouts" className="h-96">
          <div className="space-y-3 h-full overflow-y-auto">
            {dashboardData?.fitness?.upcoming_workouts?.length > 0 ? (
              dashboardData.fitness.upcoming_workouts.map((workout, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{workout.name}</h4>
                    <p className="text-sm text-gray-500">
                      {formatters.date(workout.scheduled_date)} at {formatters.time(workout.scheduled_time)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {formatters.duration(workout.estimated_duration)}
                    </p>
                    <Button size="sm" as={Link} to={`/workouts/${workout.id}`}>
                      Start
                    </Button>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <ClockIcon className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                  <p>No workouts scheduled</p>
                  <Button size="sm" as={Link} to="/workouts" className="mt-2">
                    Schedule Workout
                  </Button>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Progress Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Weekly Progress" className="h-80">
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <ArrowTrendingUpIcon className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p>Progress charts coming soon!</p>
              <p className="text-sm mt-1">Continue logging your meals and workouts</p>
            </div>
          </div>
        </Card>

        <Card title="Goal Progress" className="h-80">
          <div className="space-y-4">
            {dashboardData?.fitness?.active_goals?.slice(0, 3).map((goal, index) => (
              <div key={index} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="font-medium text-gray-900">{goal.title}</span>
                  <span className="text-gray-500">
                    {formatters.percentage(goal.progress_percentage)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${goal.progress_percentage}%` }}
                  />
                </div>
              </div>
            )) || (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <TrophyIcon className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                  <p>Set your first goal!</p>
                  <Button size="sm" as={Link} to="/profile" className="mt-2">
                    Create Goal
                  </Button>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;