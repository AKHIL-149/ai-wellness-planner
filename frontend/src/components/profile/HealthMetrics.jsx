// frontend/src/components/profile/HealthMetrics.jsx

import React, { useState, useEffect } from 'react';
import { useForm } from '../../hooks/useForm';
import { useAuth } from '../../hooks/useAuth';
import Button from '../common/Button';
import Input from '../common/Input';
import Select from '../common/Select';
import Card from '../common/Card';
import Modal from '../common/Modal';
import { validators, formatters, helpers } from '../../utils';
import { 
  ScaleIcon, 
  HeartIcon, 
  ClockIcon,
  PlusIcon,
  ChartBarIcon,
  TrendingUpIcon,
  TrendingDownIcon
} from '@heroicons/react/24/outline';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const HealthMetrics = ({ metrics = [], onMetricAdd, onMetricUpdate, onMetricDelete }) => {
  const { user } = useAuth();
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedMetricType, setSelectedMetricType] = useState('');
  const [chartData, setChartData] = useState({});

  const metricTypes = [
    { 
      value: 'weight', 
      label: 'Weight', 
      unit: 'kg', 
      icon: ScaleIcon,
      color: '#3B82F6',
      description: 'Track your weight changes over time'
    },
    { 
      value: 'body_fat', 
      label: 'Body Fat Percentage', 
      unit: '%', 
      icon: ChartBarIcon,
      color: '#EF4444',
      description: 'Monitor your body composition'
    },
    { 
      value: 'muscle_mass', 
      label: 'Muscle Mass', 
      unit: 'kg', 
      icon: ChartBarIcon,
      color: '#10B981',
      description: 'Track muscle gain and loss'
    },
    { 
      value: 'resting_heart_rate', 
      label: 'Resting Heart Rate', 
      unit: 'bpm', 
      icon: HeartIcon,
      color: '#EF4444',
      description: 'Monitor cardiovascular health'
    },
    { 
      value: 'max_heart_rate', 
      label: 'Max Heart Rate', 
      unit: 'bpm', 
      icon: HeartIcon,
      color: '#F59E0B',
      description: 'Track maximum heart rate during exercise'
    },
    { 
      value: 'vo2_max', 
      label: 'VO2 Max', 
      unit: 'ml/kg/min', 
      icon: ChartBarIcon,
      color: '#8B5CF6',
      description: 'Measure cardiovascular fitness'
    },
    { 
      value: 'flexibility_score', 
      label: 'Flexibility Score', 
      unit: 'cm', 
      icon: ChartBarIcon,
      color: '#06B6D4',
      description: 'Track flexibility improvements'
    },
    { 
      value: 'sleep_hours', 
      label: 'Sleep Duration', 
      unit: 'hours', 
      icon: ClockIcon,
      color: '#6366F1',
      description: 'Monitor sleep patterns'
    },
  ];

  const validationRules = {
    metric_type: [validators.required],
    value: [validators.required, validators.min(0)],
    recorded_date: [validators.required],
  };

  const {
    values,
    errors,
    handleChange,
    handleSubmit,
    getFieldProps,
    getFieldState,
    reset,
    setValue,
  } = useForm({
    metric_type: '',
    value: '',
    unit: '',
    recorded_date: new Date().toISOString().split('T')[0],
    notes: '',
    exercise_name: '',
  }, validationRules);

  // Process metrics data for charts
  useEffect(() => {
    const processedData = {};
    metricTypes.forEach(type => {
      const typeMetrics = metrics
        .filter(m => m.metric_type === type.value)
        .sort((a, b) => new Date(a.recorded_date) - new Date(b.recorded_date))
        .map(m => ({
          date: formatters.date(m.recorded_date, 'MMM dd'),
          value: m.value,
          fullDate: m.recorded_date
        }));
      
      if (typeMetrics.length > 0) {
        processedData[type.value] = typeMetrics;
      }
    });
    setChartData(processedData);
  }, [metrics]);

  const handleAddMetric = handleSubmit(async (formData) => {
    try {
      await onMetricAdd?.({
        ...formData,
        value: Number(formData.value),
      });
      setShowAddModal(false);
      reset();
    } catch (error) {
      console.error('Failed to add metric:', error);
    }
  });

  const getLatestMetric = (metricType) => {
    return metrics
      .filter(m => m.metric_type === metricType)
      .sort((a, b) => new Date(b.recorded_date) - new Date(a.recorded_date))[0];
  };

  const getMetricTrend = (metricType) => {
    const typeMetrics = metrics
      .filter(m => m.metric_type === metricType)
      .sort((a, b) => new Date(a.recorded_date) - new Date(b.recorded_date));
    
    if (typeMetrics.length < 2) return { trend: 'neutral', change: 0 };
    
    const latest = typeMetrics[typeMetrics.length - 1];
    const previous = typeMetrics[typeMetrics.length - 2];
    const change = latest.value - previous.value;
    
    return {
      trend: change > 0 ? 'up' : change < 0 ? 'down' : 'neutral',
      change: Math.abs(change),
      changePercent: ((change / previous.value) * 100)
    };
  };

  const getHealthyRange = (metricType, userGender, userAge) => {
    const ranges = {
      resting_heart_rate: {
        male: { min: 60, max: 100 },
        female: { min: 60, max: 100 }
      },
      body_fat: {
        male: { min: 10, max: 20 },
        female: { min: 16, max: 30 }
      },
      vo2_max: {
        male: userAge < 30 ? { min: 55, max: 70 } : { min: 45, max: 60 },
        female: userAge < 30 ? { min: 45, max: 60 } : { min: 35, max: 50 }
      }
    };
    
    return ranges[metricType]?.[userGender] || null;
  };

  const isInHealthyRange = (metricType, value) => {
    const healthyRange = getHealthyRange(metricType, user?.gender, user?.age);
    if (!healthyRange) return null;
    
    return value >= healthyRange.min && value <= healthyRange.max;
  };

  return (
    <>
      <Card
        title="Health Metrics"
        subtitle="Track your body composition and health indicators"
      >
        <div className="flex justify-between items-center mb-6">
          <div className="text-sm text-gray-600">
            {metrics.length} metric{metrics.length !== 1 ? 's' : ''} recorded
          </div>
          <Button
            icon={PlusIcon}
            onClick={() => setShowAddModal(true)}
          >
            Add Metric
          </Button>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {metricTypes.map((type) => {
            const latest = getLatestMetric(type.value);
            const trend = getMetricTrend(type.value);
            const Icon = type.icon;
            const hasData = chartData[type.value]?.length > 0;
            const inHealthyRange = latest ? isInHealthyRange(type.value, latest.value) : null;

            return (
              <div
                key={type.value}
                className={`p-4 border rounded-lg transition-all cursor-pointer ${
                  selectedMetricType === type.value 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedMetricType(type.value)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Icon className="w-5 h-5 text-gray-600" style={{ color: type.color }} />
                    <span className="font-medium text-gray-900">{type.label}</span>
                  </div>
                  
                  {trend.trend !== 'neutral' && (
                    <div className={`flex items-center space-x-1 ${
                      trend.trend === 'up' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {trend.trend === 'up' ? (
                        <TrendingUpIcon className="w-4 h-4" />
                      ) : (
                        <TrendingDownIcon className="w-4 h-4" />
                      )}
                      <span className="text-xs">
                        {formatters.percentage(Math.abs(trend.changePercent), 1)}
                      </span>
                    </div>
                  )}
                </div>

                {latest ? (
                  <div className="space-y-1">
                    <div className="text-2xl font-bold text-gray-900">
                      {formatters.number(latest.value, 1)} {type.unit}
                    </div>
                    <div className="text-sm text-gray-500">
                      {formatters.relativeTime(latest.recorded_date)}
                    </div>
                    
                    {inHealthyRange !== null && (
                      <div className={`text-xs px-2 py-1 rounded-full inline-block ${
                        inHealthyRange 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {inHealthyRange ? 'Healthy range' : 'Outside range'}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    <p className="text-sm">No data recorded</p>
                    <p className="text-xs mt-1">{type.description}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Chart Display */}
        {selectedMetricType && chartData[selectedMetricType] && (
          <Card
            title={`${metricTypes.find(t => t.value === selectedMetricType)?.label} Trend`}
            subtitle="Your progress over time"
            className="mt-6"
          >
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData[selectedMetricType]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => [
                      `${formatters.number(value, 1)} ${metricTypes.find(t => t.value === selectedMetricType)?.unit}`,
                      metricTypes.find(t => t.value === selectedMetricType)?.label
                    ]}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke={metricTypes.find(t => t.value === selectedMetricType)?.color}
                    strokeWidth={2}
                    dot={{ fill: metricTypes.find(t => t.value === selectedMetricType)?.color, strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        )}

        {/* Recent Entries */}
        {metrics.length > 0 && (
          <Card title="Recent Entries" className="mt-6">
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {metrics
                .sort((a, b) => new Date(b.recorded_date) - new Date(a.recorded_date))
                .slice(0, 10)
                .map((metric, index) => {
                  const metricType = metricTypes.find(t => t.value === metric.metric_type);
                  const Icon = metricType?.icon || ChartBarIcon;

                  return (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        <Icon className="w-5 h-5 text-gray-600" />
                        <div>
                          <div className="font-medium text-gray-900">
                            {metricType?.label || metric.metric_type}
                          </div>
                          <div className="text-sm text-gray-500">
                            {formatters.date(metric.recorded_date)}
                            {metric.exercise_name && ` • ${metric.exercise_name}`}
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="font-semibold text-gray-900">
                          {formatters.number(metric.value, 1)} {metric.unit}
                        </div>
                        {metric.notes && (
                          <div className="text-xs text-gray-500 max-w-32 truncate">
                            {metric.notes}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
            </div>
          </Card>
        )}
      </Card>

      {/* Add Metric Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => {
          setShowAddModal(false);
          reset();
        }}
        title="Add Health Metric"
        size="md"
      >
        <form onSubmit={handleAddMetric} className="space-y-6">
          <Select
            label="Metric Type"
            options={[
              { value: '', label: 'Select metric type' },
              ...metricTypes.map(type => ({
                value: type.value,
                label: type.label
              }))
            ]}
            {...getFieldProps('metric_type')}
            {...getFieldState('metric_type')}
            onChange={(e) => {
              handleChange(e);
              const selectedType = metricTypes.find(type => type.value === e.target.value);
              if (selectedType) {
                setValue('unit', selectedType.unit);
              }
            }}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Value"
              type="number"
              step="0.1"
              min="0"
              {...getFieldProps('value')}
              {...getFieldState('value')}
            />

            <Input
              label="Unit"
              value={metricTypes.find(type => type.value === values.metric_type)?.unit || ''}
              disabled
              className="bg-gray-50"
            />
          </div>

          <Input
            label="Date Recorded"
            type="date"
            {...getFieldProps('recorded_date')}
            {...getFieldState('recorded_date')}
          />

          {(values.metric_type === 'strength_1rm' || values.metric_type === 'endurance_time') && (
            <Input
              label="Exercise Name"
              placeholder="e.g., Bench Press, Running"
              {...getFieldProps('exercise_name')}
              {...getFieldState('exercise_name')}
              helpText="Optional - specify the exercise for strength or endurance metrics"
            />
          )}

          <Input
            label="Notes"
            placeholder="Any additional notes about this measurement"
            {...getFieldProps('notes')}
            {...getFieldState('notes')}
            helpText="Optional"
          />

          <div className="flex justify-end space-x-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setShowAddModal(false);
                reset();
              }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              icon={PlusIcon}
            >
              Add Metric
            </Button>
          </div>
        </form>
      </Modal>
    </>
  );
};

export default HealthMetrics;