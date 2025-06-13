# backend/apps/users/serializers.py

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserProfile, UserGoal, UserPreference

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password', 'password_confirm')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for user details"""
    
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'full_name', 
                 'date_joined', 'is_email_verified')
        read_only_fields = ('id', 'date_joined', 'is_email_verified')

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    bmi = serializers.ReadOnlyField()
    bmi_category = serializers.ReadOnlyField()
    bmr = serializers.ReadOnlyField()
    tdee = serializers.ReadOnlyField()
    calorie_goal = serializers.ReadOnlyField()
    protein_goal = serializers.ReadOnlyField()
    macro_targets = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def get_macro_targets(self, obj):
        return obj.get_macro_targets()
    
    def validate_age(self, value):
        if value < 13 or value > 120:
            raise serializers.ValidationError("Age must be between 13 and 120")
        return value
    
    def validate_height(self, value):
        if value < 100 or value > 250:
            raise serializers.ValidationError("Height must be between 100 and 250 cm")
        return value
    
    def validate_weight(self, value):
        if value < 30 or value > 300:
            raise serializers.ValidationError("Weight must be between 30 and 300 kg")
        return value
    
    def validate_target_weight(self, value):
        if value and (value < 30 or value > 300):
            raise serializers.ValidationError("Target weight must be between 30 and 300 kg")
        return value
    
    def validate_sleep_hours(self, value):
        if value < 3 or value > 12:
            raise serializers.ValidationError("Sleep hours must be between 3 and 12")
        return value
    
    def validate_stress_level(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("Stress level must be between 1 and 10")
        return value
    
    def validate_water_intake(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError("Water intake must be between 0 and 10 liters")
        return value

class UserGoalSerializer(serializers.ModelSerializer):
    """Serializer for user goals"""
    
    progress_percentage = serializers.ReadOnlyField()
    goal_type_display = serializers.CharField(source='get_goal_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = UserGoal
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at', 'completed_at')
    
    def validate_target_value(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Target value must be positive")
        return value
    
    def validate_current_value(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Current value cannot be negative")
        return value
    
    def validate(self, attrs):
        # Ensure target_date is in the future for new goals
        if not self.instance and attrs.get('target_date'):
            from django.utils import timezone
            if attrs['target_date'] <= timezone.now().date():
                raise serializers.ValidationError({
                    'target_date': 'Target date must be in the future'
                })
        return attrs

class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user preferences"""
    
    class Meta:
        model = UserPreference
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

class UserGoalCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating goals"""
    
    class Meta:
        model = UserGoal
        fields = ('goal_type', 'title', 'description', 'target_value', 'unit', 'target_date')
    
    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Goal title must be at least 3 characters long")
        return value.strip()

class UserGoalProgressSerializer(serializers.ModelSerializer):
    """Serializer for updating goal progress"""
    
    class Meta:
        model = UserGoal
        fields = ('current_value', 'status')
    
    def validate_current_value(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Progress value cannot be negative")
        return value

class UserHealthMetricsSerializer(serializers.Serializer):
    """Serializer for health metrics dashboard"""
    
    bmi = serializers.DictField(read_only=True)
    daily_calories = serializers.DictField(read_only=True)
    macro_targets = serializers.DictField(read_only=True)
    health_score = serializers.IntegerField(read_only=True)

class UserDashboardSerializer(serializers.Serializer):
    """Serializer for dashboard data"""
    
    user = UserDetailSerializer(read_only=True)
    profile = serializers.DictField(read_only=True)
    health_metrics = UserHealthMetricsSerializer(read_only=True)
    macro_targets = serializers.DictField(read_only=True)
    active_goals = serializers.ListField(read_only=True)
    recent_activity = serializers.DictField(read_only=True)
    recommendations = serializers.ListField(read_only=True)

class UserInsightSerializer(serializers.Serializer):
    """Serializer for health insights"""
    
    type = serializers.CharField(read_only=True)
    priority = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)
    action = serializers.CharField(read_only=True)

class UserRecommendationSerializer(serializers.Serializer):
    """Serializer for user recommendations"""
    
    type = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    priority = serializers.CharField(read_only=True)

class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics"""
    
    total_goals = serializers.IntegerField(read_only=True)
    completed_goals = serializers.IntegerField(read_only=True)
    active_goals = serializers.IntegerField(read_only=True)
    goal_completion_rate = serializers.FloatField(read_only=True)
    days_since_registration = serializers.IntegerField(read_only=True)
    profile_completion = serializers.FloatField(read_only=True)

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Simplified serializer for profile updates"""
    
    class Meta:
        model = UserProfile
        fields = (
            'age', 'gender', 'height', 'weight', 'target_weight',
            'activity_level', 'fitness_level', 'primary_goal',
            'dietary_restrictions', 'food_preferences', 'food_dislikes',
            'sleep_hours', 'stress_level', 'water_intake',
            'preferred_meal_count', 'cooking_time_available', 'workout_time_available'
        )
    
    def validate(self, attrs):
        # Custom validation for weight vs target weight
        weight = attrs.get('weight', self.instance.weight if self.instance else None)
        target_weight = attrs.get('target_weight')
        
        if weight and target_weight:
            if abs(weight - target_weight) > 50:
                raise serializers.ValidationError({
                    'target_weight': 'Target weight should be within 50kg of current weight for realistic goals'
                })
        
        return attrs

class UserQuickStatsSerializer(serializers.Serializer):
    """Serializer for quick user stats"""
    
    current_weight = serializers.FloatField(source='profile.weight', read_only=True)
    target_weight = serializers.FloatField(source='profile.target_weight', read_only=True)
    bmi = serializers.FloatField(source='profile.bmi', read_only=True)
    daily_calorie_goal = serializers.IntegerField(source='profile.calorie_goal', read_only=True)
    active_goals_count = serializers.SerializerMethodField()
    
    def get_active_goals_count(self, obj):
        return obj.goals.filter(status='active').count()

class UserProfileCompletionSerializer(serializers.Serializer):
    """Serializer to check profile completion status"""
    
    completion_percentage = serializers.SerializerMethodField()
    missing_fields = serializers.SerializerMethodField()
    completed_sections = serializers.SerializerMethodField()
    
    def get_completion_percentage(self, obj):
        profile = obj.profile
        required_fields = [
            'age', 'gender', 'height', 'weight', 'activity_level',
            'fitness_level', 'primary_goal'
        ]
        
        completed = sum(1 for field in required_fields if getattr(profile, field, None))
        return round((completed / len(required_fields)) * 100, 1)
    
    def get_missing_fields(self, obj):
        profile = obj.profile
        required_fields = {
            'age': 'Age',
            'gender': 'Gender',
            'height': 'Height',
            'weight': 'Weight',
            'activity_level': 'Activity Level',
            'fitness_level': 'Fitness Level',
            'primary_goal': 'Primary Goal'
        }
        
        missing = []
        for field, label in required_fields.items():
            if not getattr(profile, field, None):
                missing.append({'field': field, 'label': label})
        
        return missing
    
    def get_completed_sections(self, obj):
        profile = obj.profile
        sections = {
            'basic_info': ['age', 'gender', 'height', 'weight'],
            'goals': ['primary_goal', 'target_weight'],
            'activity': ['activity_level', 'fitness_level'],
            'preferences': ['dietary_restrictions', 'food_preferences']
        }
        
        completed_sections = {}
        for section, fields in sections.items():
            completed = sum(1 for field in fields if getattr(profile, field, None))
            completed_sections[section] = {
                'completed': completed,
                'total': len(fields),
                'percentage': round((completed / len(fields)) * 100, 1)
            }
        
        return completed_sections