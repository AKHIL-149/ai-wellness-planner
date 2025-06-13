# backend/apps/nutrition/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

User = get_user_model()

class FoodItem(models.Model):
    """
    Food items from USDA database or custom entries
    """
    fdc_id = models.IntegerField(unique=True, null=True, blank=True, help_text="USDA Food Data Central ID")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    brand = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=50, blank=True)
    
    # Nutritional data per 100g
    calories_per_100g = models.FloatField(default=0)
    protein_per_100g = models.FloatField(default=0)
    fat_per_100g = models.FloatField(default=0)
    carbs_per_100g = models.FloatField(default=0)
    fiber_per_100g = models.FloatField(default=0)
    sugar_per_100g = models.FloatField(default=0)
    sodium_per_100g = models.FloatField(default=0)
    
    # Additional nutrients (stored as JSON for flexibility)
    nutrients_data = models.JSONField(default=dict, blank=True)
    
    # Serving information
    serving_size = models.FloatField(null=True, blank=True, help_text="Standard serving size in grams")
    serving_description = models.CharField(max_length=100, blank=True, help_text="e.g., '1 cup', '1 medium apple'")
    
    # Metadata
    data_source = models.CharField(max_length=20, choices=[
        ('usda', 'USDA Database'),
        ('user', 'User Created'),
        ('admin', 'Admin Created')
    ], default='usda')
    
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'food_items'
        ordering = ['name']
        indexes = [
            models.Index(fields=['fdc_id']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_nutrition_per_serving(self):
        """Get nutrition data for one standard serving"""
        if not self.serving_size:
            return None
        
        multiplier = self.serving_size / 100  # Convert from per 100g
        
        return {
            'calories': round(self.calories_per_100g * multiplier, 1),
            'protein': round(self.protein_per_100g * multiplier, 1),
            'fat': round(self.fat_per_100g * multiplier, 1),
            'carbs': round(self.carbs_per_100g * multiplier, 1),
            'fiber': round(self.fiber_per_100g * multiplier, 1),
            'sugar': round(self.sugar_per_100g * multiplier, 1),
            'sodium': round(self.sodium_per_100g * multiplier, 1)
        }

class Recipe(models.Model):
    """
    User recipes with nutritional analysis
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField()
    
    # Recipe metadata
    prep_time = models.PositiveIntegerField(help_text="Preparation time in minutes")
    cook_time = models.PositiveIntegerField(help_text="Cooking time in minutes")
    servings = models.PositiveIntegerField(default=1)
    difficulty = models.CharField(max_length=20, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ], default='medium')
    
    # Nutritional data (calculated from ingredients)
    calories_per_serving = models.FloatField(default=0)
    protein_per_serving = models.FloatField(default=0)
    fat_per_serving = models.FloatField(default=0)
    carbs_per_serving = models.FloatField(default=0)
    fiber_per_serving = models.FloatField(default=0)
    
    # Tags and categories
    tags = models.JSONField(default=list, blank=True, help_text="List of tags like ['breakfast', 'high-protein']")
    cuisine_type = models.CharField(max_length=50, blank=True)
    dietary_restrictions = models.JSONField(default=list, blank=True, help_text="e.g., ['vegetarian', 'gluten-free']")
    
    # AI analysis
    ai_nutrition_analysis = models.JSONField(default=dict, blank=True)
    health_score = models.IntegerField(default=50, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Status and sharing
    is_public = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'recipes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_public', 'health_score']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def total_time(self):
        return self.prep_time + self.cook_time
    
    def calculate_nutrition_from_ingredients(self):
        """Calculate nutrition from recipe ingredients"""
        total_nutrition = {
            'calories': 0, 'protein': 0, 'fat': 0, 
            'carbs': 0, 'fiber': 0, 'sodium': 0
        }
        
        for ingredient in self.ingredients.all():
            food_nutrition = ingredient.food_item.get_nutrition_per_serving()
            if food_nutrition:
                quantity_multiplier = ingredient.quantity / 100  # Assuming quantity in grams
                
                for nutrient in total_nutrition.keys():
                    if nutrient in food_nutrition:
                        total_nutrition[nutrient] += food_nutrition[nutrient] * quantity_multiplier
        
        # Update per serving values
        if self.servings > 0:
            self.calories_per_serving = total_nutrition['calories'] / self.servings
            self.protein_per_serving = total_nutrition['protein'] / self.servings
            self.fat_per_serving = total_nutrition['fat'] / self.servings
            self.carbs_per_serving = total_nutrition['carbs'] / self.servings
            self.fiber_per_serving = total_nutrition['fiber'] / self.servings
        
        self.save()
        return total_nutrition

class RecipeIngredient(models.Model):
    """
    Ingredients for recipes with quantities
    """
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    
    quantity = models.FloatField(help_text="Quantity in grams")
    unit = models.CharField(max_length=20, default='g')
    notes = models.CharField(max_length=100, blank=True, help_text="e.g., 'chopped', 'diced'")
    
    class Meta:
        db_table = 'recipe_ingredients'
        unique_together = ['recipe', 'food_item']
    
    def __str__(self):
        return f"{self.quantity}{self.unit} {self.food_item.name}"

class MealPlan(models.Model):
    """
    AI-generated or user-created meal plans
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plans')
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Plan details
    start_date = models.DateField()
    end_date = models.DateField()
    daily_calorie_target = models.IntegerField()
    
    # Macronutrient targets (percentages)
    protein_target_percent = models.FloatField(default=20)
    fat_target_percent = models.FloatField(default=30)
    carb_target_percent = models.FloatField(default=50)
    
    # AI generation data
    generated_by_ai = models.BooleanField(default=False)
    ai_generation_prompt = models.TextField(blank=True)
    ai_confidence_score = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Plan status
    is_active = models.BooleanField(default=False)
    is_template = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'meal_plans'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.user.full_name})"
    
    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1
    
    def get_daily_nutrition_average(self):
        """Calculate average daily nutrition for this meal plan"""
        total_days = self.duration_days
        if total_days == 0:
            return {}
        
        total_nutrition = {'calories': 0, 'protein': 0, 'fat': 0, 'carbs': 0, 'fiber': 0}
        
        for meal in self.meals.all():
            total_nutrition['calories'] += meal.calories
            total_nutrition['protein'] += meal.protein
            total_nutrition['fat'] += meal.fat
            total_nutrition['carbs'] += meal.carbs
            total_nutrition['fiber'] += meal.fiber
        
        # Calculate averages
        return {k: round(v / total_days, 1) for k, v in total_nutrition.items()}

class Meal(models.Model):
    """
    Individual meals within a meal plan
    """
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name='meals')
    
    name = models.CharField(max_length=200)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    day_number = models.PositiveIntegerField(help_text="Day within the meal plan (1-based)")
    
    # Optional recipe reference
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Nutritional data (calculated or manual)
    calories = models.FloatField(default=0)
    protein = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    fiber = models.FloatField(default=0)
    
    # AI insights
    ai_rationale = models.TextField(blank=True, help_text="AI explanation for this meal choice")
    preparation_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'meals'
        ordering = ['day_number', 'meal_type']
        unique_together = ['meal_plan', 'day_number', 'meal_type']
        indexes = [
            models.Index(fields=['meal_plan', 'day_number']),
            models.Index(fields=['meal_type']),
        ]
    
    def __str__(self):
        return f"{self.name} - Day {self.day_number} {self.get_meal_type_display()}"

class MealFood(models.Model):
    """
    Food items within a meal with specific quantities
    """
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='foods')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    
    quantity = models.FloatField(help_text="Quantity in grams")
    unit = models.CharField(max_length=20, default='g')
    
    class Meta:
        db_table = 'meal_foods'
        unique_together = ['meal', 'food_item']
    
    def __str__(self):
        return f"{self.quantity}{self.unit} {self.food_item.name}"

class NutritionLog(models.Model):
    """
    Daily nutrition tracking log
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nutrition_logs')
    date = models.DateField()
    
    # Actual intake (can be different from planned)
    total_calories = models.FloatField(default=0)
    total_protein = models.FloatField(default=0)
    total_fat = models.FloatField(default=0)
    total_carbs = models.FloatField(default=0)
    total_fiber = models.FloatField(default=0)
    total_sodium = models.FloatField(default=0)
    
    # Targets for the day
    calorie_target = models.IntegerField(default=2000)
    protein_target = models.FloatField(default=150)
    
    # Adherence tracking
    meal_plan_adherence = models.FloatField(default=100, help_text="Percentage adherence to meal plan")
    
    # Notes and feedback
    notes = models.TextField(blank=True)
    energy_level = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Energy level (1-10)"
    )
    satisfaction_level = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Meal satisfaction (1-10)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'nutrition_logs'
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.date}"
    
    @property
    def calorie_adherence_percent(self):
        if self.calorie_target > 0:
            return round((self.total_calories / self.calorie_target) * 100, 1)
        return 0
    
    @property
    def protein_adherence_percent(self):
        if self.protein_target > 0:
            return round((self.total_protein / self.protein_target) * 100, 1)
        return 0

class GroceryList(models.Model):
    """
    Auto-generated grocery lists from meal plans
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grocery_lists')
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name='grocery_lists')
    
    name = models.CharField(max_length=200)
    week_start_date = models.DateField()
    
    # List data
    items_data = models.JSONField(default=list, help_text="List of grocery items with quantities")
    estimated_cost = models.FloatField(null=True, blank=True)
    
    # Shopping status
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'grocery_lists'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.week_start_date}"
    
    @property
    def total_items(self):
        return len(self.items_data)
    
    @property
    def completed_items(self):
        return sum(1 for item in self.items_data if item.get('completed', False))