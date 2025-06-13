# backend/apps/nutrition/serializers.py

from rest_framework import serializers
from .models import (
    FoodItem, Recipe, RecipeIngredient, MealPlan, Meal, 
    MealFood, NutritionLog, GroceryList
)

class FoodItemSerializer(serializers.ModelSerializer):
    """Serializer for food items"""
    
    nutrition_per_serving = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodItem
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def get_nutrition_per_serving(self, obj):
        return obj.get_nutrition_per_serving()

class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Serializer for recipe ingredients"""
    
    food_item = FoodItemSerializer(read_only=True)
    food_item_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = RecipeIngredient
        fields = ['id', 'food_item', 'food_item_id', 'quantity', 'unit', 'notes']

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes"""
    
    ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    total_time = serializers.ReadOnlyField()
    
    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

class RecipeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating recipes with ingredients"""
    
    ingredients = RecipeIngredientSerializer(many=True, write_only=True)
    
    class Meta:
        model = Recipe
        fields = [
            'name', 'description', 'instructions', 'prep_time', 'cook_time',
            'servings', 'difficulty', 'tags', 'cuisine_type', 'dietary_restrictions',
            'is_public', 'ingredients'
        ]
    
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(recipe=recipe, **ingredient_data)
        
        # Calculate nutrition from ingredients
        recipe.calculate_nutrition_from_ingredients()
        
        return recipe

class MealFoodSerializer(serializers.ModelSerializer):
    """Serializer for meal foods"""
    
    food_item = FoodItemSerializer(read_only=True)
    
    class Meta:
        model = MealFood
        fields = ['id', 'food_item', 'quantity', 'unit']

class MealSerializer(serializers.ModelSerializer):
    """Serializer for meals"""
    
    foods = MealFoodSerializer(many=True, read_only=True)
    recipe = RecipeSerializer(read_only=True)
    meal_type_display = serializers.CharField(source='get_meal_type_display', read_only=True)
    
    class Meta:
        model = Meal
        fields = '__all__'
        read_only_fields = ('created_at',)

class MealPlanSerializer(serializers.ModelSerializer):
    """Serializer for meal plans"""
    
    meals = MealSerializer(many=True, read_only=True)
    duration_days = serializers.ReadOnlyField()
    daily_nutrition_average = serializers.SerializerMethodField()
    
    class Meta:
        model = MealPlan
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def get_daily_nutrition_average(self, obj):
        return obj.get_daily_nutrition_average()

class MealPlanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating meal plans"""
    
    class Meta:
        model = MealPlan
        fields = [
            'name', 'description', 'start_date', 'end_date',
            'daily_calorie_target', 'protein_target_percent',
            'fat_target_percent', 'carb_target_percent', 'is_template'
        ]
    
    def validate(self, attrs):
        if attrs['end_date'] <= attrs['start_date']:
            raise serializers.ValidationError("End date must be after start date")
        return attrs

class NutritionLogSerializer(serializers.ModelSerializer):
    """Serializer for nutrition logs"""
    
    calorie_adherence_percent = serializers.ReadOnlyField()
    protein_adherence_percent = serializers.ReadOnlyField()
    
    class Meta:
        model = NutritionLog
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def validate_date(self, value):
        # Don't allow future dates
        from django.utils import timezone
        if value > timezone.now().date():
           raise serializers.ValidationError("Cannot log nutrition for future dates")
        return value

class GroceryListSerializer(serializers.ModelSerializer):
   """Serializer for grocery lists"""
   
   total_items = serializers.ReadOnlyField()
   completed_items = serializers.ReadOnlyField()
   meal_plan_name = serializers.CharField(source='meal_plan.name', read_only=True)
   
   class Meta:
       model = GroceryList
       fields = '__all__'
       read_only_fields = ('user', 'created_at', 'updated_at')

class NutritionDashboardSerializer(serializers.Serializer):
   """Serializer for nutrition dashboard data"""
   
   today = serializers.DictField()
   week_average = serializers.DictField()
   active_meal_plan = MealPlanSerializer(allow_null=True)
   recent_recipes = RecipeSerializer(many=True)
   stats = serializers.DictField()

class FoodSearchResultSerializer(serializers.Serializer):
   """Serializer for food search results"""
   
   local_foods = FoodItemSerializer(many=True)
   usda_foods = serializers.ListField()
   total_local = serializers.IntegerField()
   total_usda = serializers.IntegerField()

class NutritionInsightSerializer(serializers.Serializer):
   """Serializer for nutrition insights"""
   
   type = serializers.CharField()
   priority = serializers.CharField()
   title = serializers.CharField()
   message = serializers.CharField()
   recommendation = serializers.CharField()
   action = serializers.CharField()