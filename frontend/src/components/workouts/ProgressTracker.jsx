// frontend/src/components/workouts/ProgressTracker.jsx

import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  ClockIcon, 
  FireIcon,
  TrophyIcon,
  CalendarDaysIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon
} from '@heroicons/react/24/outline';
import Card from '../common/Card';
import Button from '../common/Button';
import Select from '../common/Select';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { formatters, helpers } from '../../utils';

const ProgressTracker = ({ 
  workoutData = [], 
  metricsData = [], 
  goals = [],
  timeRange = '30',
  onTimeRangeChange 
}) => {
  const [selectedMetric, setSelectedMetric] = useState('weight');
  const [chartType, setChartType] = useState('line');
  const [progressSummary, setProgressSummary] = useState({});

  const timeRangeOptions = [
    { value: '7', label: 'Last 7 days' },
    { value: '30', label: 'Last 30 days' },
    { value: '90', label: 'Last 3 months' },
    { value: '365', label: 'Last year' },
  ];

  const metricOptions = [
    { value: 'weight', label: 'Weight', unit: 'kg', color: '#3B82F6' },
    { value: 'body_fat', label: 'Body Fat %', unit: '%', color: '#EF4444' },
    { value: 'muscle_mass', label: 'Muscle Mass', unit: 'kg', color: '#10B981' },
    { value: 'strength_1rm', label: '1RM Strength', unit: 'kg', color: '#8B5CF6' },
    { value: 'endurance_time', label: 'Endurance', unit: 'min', color: '#F59E0B' },
    { value: 'resting_heart_rate', label: 'Resting HR', unit: 'bpm', color: '#EF4444' },
  ];

  const chartTypeOptions = [
    { value: 'line', label: 'Line Chart' },
    { value: 'bar', label: 'Bar Chart' },
  ];

  // Calculate progress summary
  useEffect(() => {
    if (metricsData.length > 0) {
      const currentMetricData = metricsData.filter(m => m.metric_type === selectedMetric);
      
      if (currentMetricData.length >= 2) {
        const sortedData = currentMetricData.sort((a, b) => new Date(a.recorded_date) - new Date(b.recorded_date));
        const firstValue = sortedData[0].value;
        const lastValue = sortedData[sortedData.length - 1].value;
        const change = lastValue - firstValue;
        const changePercent = ((change / firstValue) * 100);
        
        setProgressSummary({
          firstValue,
          lastValue,
          change,
          changePercent,
          trend: change > 0 ? 'up' : change < 0 ? 'down' : 'stable',
          dataPoints: sortedData.length
        });
      }
    }
  }, [metricsData, selectedMetric]);

  // Prepare chart data
  const chartData = metricsData
    .filter(m => m.metric_type === selectedMetric)
    .sort((a, b) => new Date(a.recorded_date) - new Date(b.recorded_date))
    .map(item => ({
      date: formatters.date(item.recorded_date, 'MMM dd'),
      value: item.value,
      fullDate: item.recorded_date
    }));

  // Workout statistics
  const workoutStats = {
    totalWorkouts: workoutData.length,
    completedWorkouts: workoutData.filter(w => w.status === 'completed').length,
    totalDuration: workoutData.reduce((sum, w) => sum + (w.actual_duration || 0), 0),
    avgDuration: workoutData.length > 0 ? 
      workoutData.reduce((sum, w) => sum + (w.actual_duration || 0), 0) / workoutData.length : 0,
    totalCalories: workoutData.reduce((sum, w) => sum + (w.total_calories_burned || 0), 0),
    streak: calculateWorkoutStreak(workoutData),
  };

  function calculateWorkoutStreak(workouts) {
    const completedWorkouts = workouts
      .filter(w => w.status === 'completed')
      .sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at));
    
    if (completedWorkouts.length === 0) return 0;
    
    let streak = 0;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    for (const workout of completedWorkouts) {
      const workoutDate = new Date(workout.completed_at);
      workoutDate.setHours(0, 0, 0, 0);
      
      const daysDiff = Math.floor((today - workoutDate) / (1000 * 60 * 60 * 24));
      
      if (daysDiff === streak) {
        streak++;
      } else {
        break;
      }
    }
    
    return streak;
  }

  const selectedMetricInfo = metricOptions.find(m => m.value === selectedMetric);

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up':
        return <ArrowTrendingUpIcon className="w-4 h-4 text-green-600" />;
      case 'down':
        return <ArrowTrendingDownIcon className="w-4 h-4 text-red-600" />;
      default:
        return <MinusIcon className="w-4 h-4 text-gray-600" />;
    }
  };

  const getTrendColor = (trend, metricType) => {
    // For weight and body fat, down is good; for strength and muscle mass, up is good
    const downIsGood = ['weight', 'body_fat', 'resting_heart_rate'].includes(metricType);
    
    if (trend === 'up') {
      return downIsGood ? 'text-red-600' : 'text-green-600';
    } else if (trend === 'down') {
      return downIsGood ? 'text-green-600' : 'text-red-600';
    }
    return 'text-gray-600';
  };

  return (
    <div className="space-y-6">
      {/* Workout Overview Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card padding="sm">
          <div className="text-center">
            <ChartBarIcon className="w-8 h-8 mx-auto mb-2 text-blue-600" />
            <div className="text-2xl font-bold text-gray-900">{workoutStats.completedWorkouts}</div>
            <div className="text-sm text-gray-500">Workouts Completed</div>
            <div className="text-xs text-gray-400">
              {workoutStats.totalWorkouts} scheduled
            </div>
          </div>
        </Card>

        <Card padding="sm">
          <div className="text-center">
            <ClockIcon className="w-8 h-8 mx-auto mb-2 text-green-600" />
            <div className="text-2xl font-bold text-gray-900">
              {formatters.duration(workoutStats.totalDuration)}
            </div>
            <div className="text-sm text-gray-500">Total Duration</div>
            <div className="text-xs text-gray-400">
              Avg: {formatters.duration(workoutStats.avgDuration)}
            </div>
          </div>
        </Card>

        <Card padding="sm">
          <div className="text-center">
            <FireIcon className="w-8 h-8 mx-auto mb-2 text-red-600" />
            <div className="text-2xl font-bold text-gray-900">
              {formatters.calories(workoutStats.totalCalories)}
            </div>
            <div className="text-sm text-gray-500">Calories Burned</div>
            <div className="text-xs text-gray-400">
              This period
            </div>
          </div>
        </Card>

        <Card padding="sm">
          <div className="text-center">
            <TrophyIcon className="w-8 h-8 mx-auto mb-2 text-yellow-600" />
            <div className="text-2xl font-bold text-gray-900">{workoutStats.streak}</div>
            <div className="text-sm text-gray-500">Day Streak</div>
            <div className="text-xs text-gray-400">
              Keep it up!
            </div>
          </div>
        </Card>
      </div>

      {/* Metrics Progress Chart */}
      <Card
        title="Progress Metrics"
        subtitle="Track your body composition and fitness metrics over time"
      >
        {/* Chart Controls */}
        <div className="flex flex-wrap items-center justify-between mb-6 gap-4">
          <div className="flex items-center space-x-4">
            <Select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              options={[
                { value: '', label: 'Select metric to track' },
                ...metricOptions.map(m => ({ value: m.value, label: m.label }))
              ]}
              className="min-w-48"
            />
            
            <Select
              value={chartType}
              onChange={(e) => setChartType(e.target.value)}
              options={chartTypeOptions}
              className="min-w-32"
            />
          </div>

          <div className="flex items-center space-x-2">
            <Select
              value={timeRange}
              onChange={(e) => onTimeRangeChange?.(e.target.value)}
              options={timeRangeOptions}
              className="min-w-32"
            />
          </div>
        </div>

        {/* Progress Summary */}
        {progressSummary.dataPoints > 1 && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-lg font-semibold text-gray-900">
                  {formatters.number(progressSummary.firstValue, 1)} {selectedMetricInfo?.unit}
                </div>
                <div className="text-sm text-gray-500">Starting Value</div>
              </div>
              
              <div className="text-center">
                <div className="text-lg font-semibold text-gray-900">
                  {formatters.number(progressSummary.lastValue, 1)} {selectedMetricInfo?.unit}
                </div>
                <div className="text-sm text-gray-500">Current Value</div>
              </div>
              
              <div className="text-center">
                <div className={`text-lg font-semibold flex items-center justify-center space-x-1 ${
                  getTrendColor(progressSummary.trend, selectedMetric)
                }`}>
                  {getTrendIcon(progressSummary.trend)}
                  <span>
                    {progressSummary.change > 0 ? '+' : ''}
                    {formatters.number(progressSummary.change, 1)} {selectedMetricInfo?.unit}
                  </span>
                </div>
                <div className="text-sm text-gray-500">Change</div>
              </div>
              
              <div className="text-center">
                <div className={`text-lg font-semibold ${
                  getTrendColor(progressSummary.trend, selectedMetric)
                }`}>
                  {progressSummary.changePercent > 0 ? '+' : ''}
                  {formatters.percentage(progressSummary.changePercent, 1)}
                </div>
                <div className="text-sm text-gray-500">% Change</div>
              </div>
            </div>
          </div>
        )}

        {/* Chart */}
        {chartData.length > 0 ? (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              {chartType === 'line' ? (
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => [
                      `${formatters.number(value, 1)} ${selectedMetricInfo?.unit}`,
                      selectedMetricInfo?.label
                    ]}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke={selectedMetricInfo?.color || '#3B82F6'}
                    strokeWidth={2}
                    dot={{ fill: selectedMetricInfo?.color || '#3B82F6', strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              ) : (
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => [
                      `${formatters.number(value, 1)} ${selectedMetricInfo?.unit}`,
                      selectedMetricInfo?.label
                    ]}
                  />
                  <Bar 
                    dataKey="value" 
                    fill={selectedMetricInfo?.color || '#3B82F6'}
                  />
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-80 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <ChartBarIcon className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <p>No data available for {selectedMetricInfo?.label || 'selected metric'}</p>
              <p className="text-sm mt-1">Start tracking this metric to see your progress</p>
              <Button size="sm" className="mt-3">
                Log {selectedMetricInfo?.label}
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Goals Progress */}
      {goals.length > 0 && (
        <Card
          title="Goal Progress"
          subtitle="Track your progress towards your fitness goals"
        >
          <div className="space-y-4">
            {goals.map((goal) => {
              const progress = (goal.current_value / goal.target_value) * 100;
              const daysRemaining = Math.ceil(
                (new Date(goal.target_date) - new Date()) / (1000 * 60 * 60 * 24)
              );

              return (
                <div key={goal.id} className="p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">{goal.title}</h4>
                    <span className={`text-sm px-2 py-1 rounded-full ${
                      progress >= 100 ? 'bg-green-100 text-green-800' :
                      progress >= 75 ? 'bg-blue-100 text-blue-800' :
                      progress >= 50 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {Math.round(progress)}%
                    </span>
                  </div>
                  
                  <div className="mb-2">
                    <div className="flex justify-between text-sm text-gray-600 mb-1">
                      <span>{goal.current_value} / {goal.target_value} {goal.unit}</span>
                      <span>
                        {daysRemaining > 0 ? `${daysRemaining} days left` : 'Overdue'}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          progress >= 100 ? 'bg-green-500' :
                          progress >= 75 ? 'bg-blue-500' :
                          progress >= 50 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(progress, 100)}%` }}
                      />
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-500">
                    Target: {formatters.date(goal.target_date)}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Weekly Activity Calendar */}
      <Card
        title="Weekly Activity"
        subtitle="Your workout consistency over the past weeks"
      >
        <div className="grid grid-cols-7 gap-1 mb-4">
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
            <div key={day} className="text-center text-sm font-medium text-gray-500 p-2">
              {day}
            </div>
          ))}
        </div>
        
        <div className="grid grid-cols-7 gap-1">
          {/* Generate calendar grid for the past 4 weeks */}
          {Array.from({ length: 28 }, (_, i) => {
            const date = new Date();
            date.setDate(date.getDate() - (27 - i));
            
            const workoutsOnDay = workoutData.filter(w => {
              const workoutDate = new Date(w.completed_at || w.scheduled_date);
              return workoutDate.toDateString() === date.toDateString() && w.status === 'completed';
            });
            
            return (
              <div
                key={i}
                className={`aspect-square p-1 rounded text-xs flex items-center justify-center ${
                  workoutsOnDay.length > 0
                    ? 'bg-green-500 text-white'
                    : date.toDateString() === new Date().toDateString()
                    ? 'bg-blue-100 text-blue-800 border-2 border-blue-500'
                    : 'bg-gray-100 text-gray-600'
                }`}
                title={`${date.toDateString()}: ${workoutsOnDay.length} workout(s)`}
              >
                {date.getDate()}
              </div>
            );
          })}
        </div>
        
        <div className="flex items-center justify-between mt-4 text-sm">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-gray-100 rounded"></div>
              <span className="text-gray-600">No workout</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-green-500 rounded"></div>
              <span className="text-gray-600">Workout completed</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-blue-100 border-2 border-blue-500 rounded"></div>
              <span className="text-gray-600">Today</span>
            </div>
          </div>
          
          <div className="text-gray-500">
            {workoutData.filter(w => w.status === 'completed').length} workouts completed
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ProgressTracker;