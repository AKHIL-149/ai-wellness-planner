# backend/apps/users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class User(AbstractUser):
    """Extended User model with additional fields"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

class UserProfile(models.Model):
    """User health and fitness profile"""
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    ACTIVITY_LEVEL_CHOICES = [
        ('sedentary', 'Sedentary (little or no exercise)'),
        ('light', 'Light (light exercise/sports 1-3 days/week)'),
        ('moderate', 'Moderate (moderate exercise/sports 3-5 days/week)'),
        ('active', 'Active (hard exercise/sports 6-7 days/week)'),
        ('very_active', 'Very Active (very hard exercise/sports, physical job)'),
    ]
    
    GOAL_CHOICES = [
        ('weight_loss', 'Weight Loss'),
        ('weight_gain', 'Weight Gain'),
        ('muscle_gain', 'Muscle Gain'),
        ('maintenance', 'Weight Maintenance'),
        ('general_health', 'General Health'),
        ('athletic_performance', 'Athletic Performance'),
        ('disease_management', 'Disease Management'),
    ]
    
    EXPERIENCE_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Basic Demographics
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(13), MaxValueValidator(120)],
        help_text="Age in years"
    )
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    
    # Physical Measurements
    height = models.FloatField(
        validators=[MinValueValidator(100), MaxValueValidator(250)],
        help_text="Height in centimeters"
    )
    weight = models.FloatField(
        validators=[MinValueValidator(30), MaxValueValidator(300)],
        help_text="Current weight in kilograms"
    )
    target_weight = models.FloatField(
        validators=[MinValueValidator(30), MaxValueValidator(300)],
        help_text="Target weight in kilograms",
        null=True,
        blank=True
    )
    
    # Activity and Goals
    activity_level = models.CharField(
        max_length=20,
        choices=ACTIVITY_LEVEL_CHOICES,
        default='moderate'
    )
    fitness_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        default='beginner'
    )
    primary_goal = models.CharField(
        max_length=30,
        choices=GOAL_CHOICES,
        default='general_health'
    )
    
    # Dietary Information
    dietary_restrictions = models.TextField(
        blank=True,
        help_text="Any dietary restrictions, allergies, or special requirements"
    )
    food_preferences = models.TextField(
        blank=True,
        help_text="Preferred foods, cuisines, or eating patterns"
    )
    food_dislikes = models.TextField(
        blank=True,
        help_text="Foods to avoid due to taste preferences"
    )
    
    # Health Information
    medical_conditions = models.TextField(
        blank=True,
        help_text="Any relevant medical conditions or medications"
    )
    previous_injuries = models.TextField(
        blank=True,
        help_text="Previous injuries that might affect exercise"
    )
    
    # Lifestyle Factors
    sleep_hours = models.FloatField(
        validators=[MinValueValidator(3), MaxValueValidator(12)],
        default=7.5,
        help_text="Average hours of sleep per night"
    )
    stress_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="Stress level on a scale of 1-10"
    )
    water_intake = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        default=2.0,
        help_text="Daily water intake in liters"
    )
    
    # Preferences
    preferred_meal_count = models.IntegerField(
        validators=[MinValueValidator(3), MaxValueValidator(6)],
        default=4,
        help_text="Preferred number of meals/snacks per day"
    )
    cooking_time_available = models.IntegerField(
        validators=[MinValueValidator(5), MaxValueValidator(120)],
        default=30,
        help_text="Average time available for meal preparation (minutes)"
    )
    workout_time_available = models.IntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(180)],
        default=45,
        help_text="Preferred workout duration (minutes)"
    )
    
    # Equipment and Environment
    kitchen_equipment = models.TextField(
        blank=True,
        help_text="Available kitchen equipment and appliances"
    )
    workout_equipment = models.TextField(
        blank=True,
        help_text="Available workout equipment or gym access"
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.full_name}'s Profile"
    
    @property
    def bmi(self):
        """Calculate BMI (Body Mass Index)"""
        if self.height and self.weight:
            height_m = self.height / 100  # Convert cm to meters
            return round(self.weight / (height_m ** 2), 1)
        return None
    
    @property
    def bmi_category(self):
        """Get BMI category"""
        bmi = self.bmi
        if not bmi:
            return "Unknown"
        
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal weight"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"
    
    @property
    def bmr(self):
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
        if not all([self.weight, self.height, self.age]):
            return None
        
        # Mifflin-St Jeor Equation
        if self.gender == 'male':
            bmr = (10 * self.weight) + (6.25 * self.height) - (5 * self.age) + 5
        else:
            bmr = (10 * self.weight) + (6.25 * self.height) - (5 * self.age) - 161
        
        return round(bmr)
    
    @property
    def tdee(self):
        """Calculate Total Daily Energy Expenditure"""
        bmr = self.bmr
        if not bmr:
            return None
        
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }
        
        multiplier = activity_multipliers.get(self.activity_level, 1.55)
        return round(bmr * multiplier)
    
    @property
    def calorie_goal(self):
        """Calculate daily calorie goal based on primary goal"""
        tdee = self.tdee
        if not tdee:
            return None
        
        if self.primary_goal == 'weight_loss':
            return tdee - 500  # 500 calorie deficit for ~1 lb/week loss
        elif self.primary_goal == 'weight_gain':
            return tdee + 500  # 500 calorie surplus for weight gain
        elif self.primary_goal == 'muscle_gain':
            return tdee + 300  # Moderate surplus for muscle gain
        else:
            return tdee  # Maintenance
    
    @property
    def protein_goal(self):
        """Calculate daily protein goal in grams"""
        if not self.weight:
            return None
        
        # Protein goals based on activity level and goals
        if self.primary_goal in ['muscle_gain', 'athletic_performance']:
            return round(self.weight * 2.2)  # 2.2g per kg for muscle building
        elif self.primary_goal == 'weight_loss':
            return round(self.weight * 2.0)  # Higher protein for weight loss
        else:
            return round(self.weight * 1.6)  # General health
    
    def get_macro_targets(self):
        """Get macronutrient targets"""
        calories = self.calorie_goal
        protein_g = self.protein_goal
        
        if not calories or not protein_g:
            return None
        
        # Calculate macros based on goals
        if self.primary_goal == 'weight_loss':
            protein_percent = 30
            fat_percent = 25
            carb_percent = 45
        elif self.primary_goal == 'muscle_gain':
            protein_percent = 25
            fat_percent = 20
            carb_percent = 55
        else:  # Maintenance and general health
            protein_percent = 20
            fat_percent = 30
            carb_percent = 50
        
        protein_calories = protein_g * 4
        fat_calories = (calories * fat_percent / 100)
        carb_calories = calories - protein_calories - fat_calories
        
        return {
            'calories': calories,
            'protein': {
                'grams': protein_g,
                'calories': protein_calories,
                'percent': round((protein_calories / calories) * 100, 1)
            },
            'fat': {
                'grams': round(fat_calories / 9, 1),
                'calories': fat_calories,
                'percent': fat_percent
            },
            'carbs': {
                'grams': round(carb_calories / 4, 1),
                'calories': carb_calories,
                'percent': round((carb_calories / calories) * 100, 1)
            }
        }

class UserGoal(models.Model):
    """Specific trackable goals for users"""
    
    GOAL_TYPE_CHOICES = [
        ('weight', 'Weight Goal'),
        ('body_fat', 'Body Fat Percentage'),
        ('muscle_mass', 'Muscle Mass'),
        ('strength', 'Strength Goal'),
        ('endurance', 'Endurance Goal'),
        ('habit', 'Habit Formation'),
        ('custom', 'Custom Goal'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    target_value = models.FloatField(null=True, blank=True)
    current_value = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_goals'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.full_name}: {self.title}"
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.target_value and self.current_value is not None:
            return min(100, max(0, (self.current_value / self.target_value) * 100))
        return 0

class UserPreference(models.Model):
    """User preferences for app behavior and notifications"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Notification Preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    meal_reminders = models.BooleanField(default=True)
    workout_reminders = models.BooleanField(default=True)
    progress_updates = models.BooleanField(default=True)
    
    # App Preferences
    theme = models.CharField(
        max_length=20,
        choices=[('light', 'Light'), ('dark', 'Dark'), ('auto', 'Auto')],
        default='auto'
    )
    units = models.CharField(
        max_length=20,
        choices=[('metric', 'Metric'), ('imperial', 'Imperial')],
        default='metric'
    )
    language = models.CharField(max_length=10, default='en')
    
    # Privacy Settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[('private', 'Private'), ('friends', 'Friends Only'), ('public', 'Public')],
        default='private'
    )
    data_sharing = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'
    
    def __str__(self):
        return f"{self.user.full_name}'s Preferences"