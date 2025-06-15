# backend/apps/fitness/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Exercise, WorkoutTemplate, WorkoutPlan, Workout, 
    WorkoutExercise, FitnessGoal, FitnessMetric
)
from apps.users.models import UserProfile


class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer for Exercise model"""
    
    class Meta:
        model = Exercise
        fields = [
            'id', 'name', 'category', 'difficulty', 'equipment',
            'description', 'instructions', 'tips', 'primary_muscles',
            'secondary_muscles', 'calories_per_minute', 'image_url',
            'video_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExerciseSearchSerializer(serializers.Serializer):
    """Serializer for exercise search parameters"""
    query = serializers.CharField(max_length=200, required=False)
    category = serializers.ChoiceField(choices=Exercise.CATEGORY_CHOICES, required=False)
    difficulty = serializers.ChoiceField(choices=Exercise.DIFFICULTY_CHOICES, required=False)
    equipment = serializers.ChoiceField(choices=Exercise.EQUIPMENT_CHOICES, required=False)
    muscle_groups = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False
    )
    duration_max = serializers.IntegerField(min_value=1, required=False)


class WorkoutTemplateSerializer(serializers.ModelSerializer):
    """Serializer for WorkoutTemplate model"""
    
    class Meta:
        model = WorkoutTemplate
        fields = [
            'id', 'name', 'description', 'workout_type', 'difficulty',
            'estimated_duration', 'intensity_level', 'equipment_needed',
            'space_required', 'fitness_level', 'target_goals',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    """Serializer for WorkoutExercise model"""
    exercise_details = ExerciseSerializer(source='exercise', read_only=True)
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    completion_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = WorkoutExercise
        fields = [
            'id', 'exercise', 'exercise_details', 'exercise_name', 'order',
            'sets_planned', 'reps_planned', 'weight_planned', 'duration_planned',
            'rest_duration', 'sets_completed', 'performance_data',
            'completion_percentage', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completion_percentage']

    def validate_performance_data(self, value):
        """Validate performance data structure"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Performance data must be a list")
        
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Each performance item must be a dictionary")
            
            required_fields = ['set']
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(f"Performance item must include '{field}' field")
        
        return value


class WorkoutSerializer(serializers.ModelSerializer):
    """Serializer for Workout model"""
    exercises = WorkoutExerciseSerializer(many=True, read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    workout_plan_name = serializers.CharField(source='workout_plan.name', read_only=True)
    
    class Meta:
        model = Workout
        fields = [
            'id', 'workout_plan', 'workout_plan_name', 'name', 'description',
            'workout_type', 'scheduled_date', 'scheduled_time', 'status',
            'started_at', 'completed_at', 'duration_minutes', 'actual_duration',
            'total_calories_burned', 'average_heart_rate', 'max_heart_rate',
            'difficulty_rating', 'energy_level_before', 'energy_level_after',
            'notes', 'workout_data', 'exercises', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'duration_minutes']

    def validate(self, data):
        """Validate workout data"""
        if data.get('completed_at') and data.get('started_at'):
            if data['completed_at'] < data['started_at']:
                raise serializers.ValidationError(
                    "Completed time cannot be before start time"
                )
        
        return data


class WorkoutCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating workouts with exercises"""
    exercises = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Workout
        fields = [
            'name', 'description', 'workout_type', 'scheduled_date',
            'scheduled_time', 'workout_data', 'exercises'
        ]

    def create(self, validated_data):
        """Create workout with exercises"""
        exercises_data = validated_data.pop('exercises', [])
        workout = Workout.objects.create(**validated_data)
        
        # Create associated exercises
        for idx, exercise_data in enumerate(exercises_data):
            WorkoutExercise.objects.create(
                workout=workout,
                exercise_id=exercise_data.get('exercise_id'),
                order=idx,
                sets_planned=exercise_data.get('sets_planned', 3),
                reps_planned=exercise_data.get('reps_planned'),
                weight_planned=exercise_data.get('weight_planned'),
                duration_planned=exercise_data.get('duration_planned'),
                rest_duration=exercise_data.get('rest_duration', 60)
            )
        
        return workout


class WorkoutPlanSerializer(serializers.ModelSerializer):
    """Serializer for WorkoutPlan model"""
    workouts = WorkoutSerializer(many=True, read_only=True)
    is_active = serializers.ReadOnlyField()
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = WorkoutPlan
        fields = [
            'id', 'user', 'user_name', 'name', 'description', 'plan_type',
            'status', 'start_date', 'end_date', 'total_weeks', 'ai_generated',
            'generation_prompt', 'ai_confidence_score', 'plan_data',
            'user_modifications', 'completion_percentage', 'total_workouts',
            'completed_workouts', 'is_active', 'workouts', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'completion_percentage',
            'is_active', 'user_name'
        ]

    def validate(self, data):
        """Validate workout plan data"""
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError(
                    "End date must be after start date"
                )
        
        return data


class WorkoutPlanGenerateSerializer(serializers.Serializer):
    """Serializer for workout plan generation request"""
    name = serializers.CharField(max_length=200)
    plan_type = serializers.ChoiceField(choices=WorkoutPlan.PLAN_TYPE_CHOICES)
    duration_weeks = serializers.IntegerField(min_value=1, max_value=52)
    
    # User preferences
    workout_days_per_week = serializers.IntegerField(min_value=1, max_value=7)
    workout_duration = serializers.IntegerField(min_value=15, max_value=180)
    fitness_goals = serializers.ListField(
        child=serializers.CharField(max_length=50)
    )
    preferred_workout_types = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False
    )
    available_equipment = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False
    )
    
    # Schedule preferences
    preferred_times = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False
    )
    
    # Special considerations
    injuries_limitations = serializers.CharField(max_length=500, required=False)
    experience_level = serializers.ChoiceField(
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')]
    )

    def validate_fitness_goals(self, value):
        """Validate fitness goals"""
        valid_goals = [
            'weight_loss', 'muscle_gain', 'strength', 'endurance',
            'flexibility', 'general_fitness', 'sports_performance'
        ]
        
        for goal in value:
            if goal not in valid_goals:
                raise serializers.ValidationError(f"Invalid fitness goal: {goal}")
        
        return value


class FitnessGoalSerializer(serializers.ModelSerializer):
    """Serializer for FitnessGoal model"""
    progress_percentage = serializers.ReadOnlyField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = FitnessGoal
        fields = [
            'id', 'title', 'description', 'goal_type', 'status',
            'target_value', 'current_value', 'unit', 'start_date',
            'target_date', 'completed_date', 'progress_percentage',
            'milestones', 'days_remaining', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'progress_percentage']

    def get_days_remaining(self, obj):
        """Calculate days remaining to target date"""
        from django.utils import timezone
        if obj.target_date:
            today = timezone.now().date()
            if obj.target_date > today:
                return (obj.target_date - today).days
            else:
                return 0
        return None

    def validate(self, data):
        """Validate fitness goal data"""
        if data.get('target_date') and data.get('start_date'):
            if data['target_date'] <= data['start_date']:
                raise serializers.ValidationError(
                    "Target date must be after start date"
                )
        
        if data.get('target_value', 0) <= 0:
            raise serializers.ValidationError(
                "Target value must be positive"
            )
        
        return data


class FitnessMetricSerializer(serializers.ModelSerializer):
    """Serializer for FitnessMetric model"""
    metric_display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FitnessMetric
        fields = [
            'id', 'metric_type', 'custom_name', 'metric_display_name',
            'value', 'unit', 'exercise_name', 'notes', 'recorded_date',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'metric_display_name']

    def get_metric_display_name(self, obj):
        """Get display name for metric"""
        if obj.metric_type == 'custom':
            return obj.custom_name
        return obj.get_metric_type_display()

    def validate(self, data):
        """Validate fitness metric data"""
        if data.get('metric_type') == 'custom' and not data.get('custom_name'):
            raise serializers.ValidationError(
                "Custom name is required for custom metrics"
            )
        
        return data


class FitnessDashboardSerializer(serializers.Serializer):
    """Serializer for fitness dashboard data"""
    active_workout_plan = WorkoutPlanSerializer(read_only=True)
    upcoming_workouts = WorkoutSerializer(many=True, read_only=True)
    recent_workouts = WorkoutSerializer(many=True, read_only=True)
    active_goals = FitnessGoalSerializer(many=True, read_only=True)
    recent_metrics = FitnessMetricSerializer(many=True, read_only=True)
    
    # Statistics
    total_workouts_completed = serializers.IntegerField(read_only=True)
    total_calories_burned = serializers.IntegerField(read_only=True)
    workout_streak = serializers.IntegerField(read_only=True)
    avg_workout_duration = serializers.FloatField(read_only=True)
    goals_completion_rate = serializers.FloatField(read_only=True)
    
    # Weekly summary
    weekly_workout_count = serializers.IntegerField(read_only=True)
    weekly_calories_burned = serializers.IntegerField(read_only=True)
    weekly_exercise_minutes = serializers.IntegerField(read_only=True)


class WorkoutProgressSerializer(serializers.Serializer):
    """Serializer for workout progress tracking"""
    workout_id = serializers.UUIDField()
    exercise_id = serializers.UUIDField()
    set_number = serializers.IntegerField(min_value=1)
    reps_completed = serializers.IntegerField(min_value=0, required=False)
    weight_used = serializers.FloatField(min_value=0, required=False)
    duration_seconds = serializers.IntegerField(min_value=0, required=False)
    notes = serializers.CharField(max_length=500, required=False)

    def validate(self, data):
        """Validate that at least one performance metric is provided"""
        performance_fields = ['reps_completed', 'weight_used', 'duration_seconds']
        if not any(data.get(field) for field in performance_fields):
            raise serializers.ValidationError(
                "At least one performance metric (reps, weight, or duration) must be provided"
            )
        return data


class WorkoutAnalyticsSerializer(serializers.Serializer):
    """Serializer for workout analytics data"""
    period = serializers.ChoiceField(
        choices=[('week', 'Week'), ('month', 'Month'), ('quarter', 'Quarter'), ('year', 'Year')]
    )
    
    # Workout frequency data
    workouts_by_day = serializers.DictField(read_only=True)
    workouts_by_type = serializers.DictField(read_only=True)
    
    # Performance trends
    strength_progression = serializers.DictField(read_only=True)
    endurance_progression = serializers.DictField(read_only=True)
    
    # Volume metrics
    total_volume = serializers.IntegerField(read_only=True)
    average_intensity = serializers.FloatField(read_only=True)
    
    # Goal progress
    goals_achieved = serializers.IntegerField(read_only=True)
    goals_on_track = serializers.IntegerField(read_only=True)
    goals_behind = serializers.IntegerField(read_only=True)