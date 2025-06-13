# backend/apps/nutrition/views.py

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Avg
from datetime import datetime, timedelta
import logging

from .models import FoodItem, Recipe, MealPlan, Meal, NutritionLog, GroceryList
from .serializers import (
    FoodItemSerializer, RecipeSerializer, MealPlanSerializer,
    MealSerializer, NutritionLogSerializer, GroceryListSerializer,
    MealPlanCreateSerializer, RecipeCreateSerializer
)
from .services import MealPlanningService, NutritionAnalysisService
from core.nutrition_api import NutritionAPI

logger = logging.getLogger(__name__)

class FoodSearchView(generics.ListAPIView):
    """
    Search for food items in database and USDA API
    """
    serializer_class = FoodItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if query:
            return FoodItem.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )[:10]
        return FoodItem.objects.none()
    
    def list(self, request, *args, **kwargs):
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({
                'error': 'Query parameter "q" is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Search local database first
            local_results = list(self.get_queryset())
            
            # Search USDA API if needed
            nutrition_api = NutritionAPI()
            usda_results = nutrition_api.search_food(query, page_size=5)
            
            # Combine results
            combined_results = {
                'local_foods': FoodItemSerializer(local_results, many=True).data,
                'usda_foods': usda_results.get('foods', []),
                'total_local': len(local_results),
                'total_usda': usda_results.get('total_results', 0)
            }
            
            return Response(combined_results)
            
        except Exception as e:
            logger.error(f"Food search failed: {str(e)}")
            return Response({
                'error': 'Search temporarily unavailable'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_meal_plan(request):
    """
    Generate AI-powered meal plan based on user profile
    """
    try:
        user = request.user
        profile = user.profile
        
        # Get generation parameters
        duration_days = request.data.get('duration_days', 7)
        start_date = request.data.get('start_date', timezone.now().date())
        preferences = request.data.get('preferences', {})
        
        # Initialize meal planning service
        meal_service = MealPlanningService()
        
        # Generate meal plan
        meal_plan_data = meal_service.generate_personalized_meal_plan(
            user_profile=profile,
            duration_days=duration_days,
            start_date=start_date,
            preferences=preferences
        )
        
        if meal_plan_data.get('error'):
            return Response({
                'error': 'Meal plan generation failed',
                'details': meal_plan_data['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Save meal plan to database
        meal_plan = meal_service.save_meal_plan_to_db(user, meal_plan_data)
        
        serializer = MealPlanSerializer(meal_plan)
        
        logger.info(f"Meal plan generated for user {user.email}")
        
        return Response({
            'message': 'Meal plan generated successfully',
            'meal_plan': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Meal plan generation error: {str(e)}")
        return Response({
            'error': 'Meal plan generation failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MealPlanListCreateView(generics.ListCreateAPIView):
    """
    List user's meal plans and create new ones
    """
    serializer_class = MealPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MealPlan.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MealPlanCreateSerializer
        return MealPlanSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MealPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific meal plan
    """
    serializer_class = MealPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MealPlan.objects.filter(user=self.request.user)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def activate_meal_plan(request, meal_plan_id):
    """
    Activate a meal plan (deactivate others)
    """
    try:
        # Deactivate all current meal plans
        MealPlan.objects.filter(user=request.user, is_active=True).update(is_active=False)
        
        # Activate selected meal plan
        meal_plan = get_object_or_404(MealPlan, id=meal_plan_id, user=request.user)
        meal_plan.is_active = True
        meal_plan.save()
        
        return Response({
            'message': 'Meal plan activated successfully'
        })
        
    except Exception as e:
        logger.error(f"Meal plan activation failed: {str(e)}")
        return Response({
            'error': 'Activation failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RecipeListCreateView(generics.ListCreateAPIView):
    """
    List user's recipes and create new ones
    """
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Recipe.objects.filter(user=self.request.user)
        
        # Filter by tags if provided
        tags = self.request.query_params.get('tags')
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            queryset = queryset.filter(tags__contains=tag_list)
        
        # Filter by cuisine type
        cuisine = self.request.query_params.get('cuisine')
        if cuisine:
            queryset = queryset.filter(cuisine_type=cuisine)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RecipeCreateSerializer
        return RecipeSerializer
    
    def perform_create(self, serializer):
        recipe = serializer.save(user=self.request.user)
        
        # Calculate nutrition if ingredients provided
        if hasattr(recipe, 'ingredients') and recipe.ingredients.exists():
            recipe.calculate_nutrition_from_ingredients()

class RecipeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific recipe
    """
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Recipe.objects.filter(user=self.request.user)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def analyze_recipe_nutrition(request, recipe_id):
    """
    Analyze recipe nutrition using AI
    """
    try:
        recipe = get_object_or_404(Recipe, id=recipe_id, user=request.user)
        
        # Get recipe ingredients as text
        ingredients = []
        for ingredient in recipe.ingredients.all():
            ingredients.append(f"{ingredient.quantity}g {ingredient.food_item.name}")
        
        if not ingredients:
            return Response({
                'error': 'Recipe has no ingredients to analyze'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Analyze with nutrition API
        nutrition_api = NutritionAPI()
        analysis = nutrition_api.analyze_recipe(ingredients, recipe.name)
        
        # Update recipe with analysis
        recipe.ai_nutrition_analysis = analysis
        recipe.health_score = analysis.get('health_score', 50)
        recipe.save()
        
        return Response({
            'message': 'Recipe analysis completed',
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Recipe analysis failed: {str(e)}")
        return Response({
            'error': 'Analysis failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NutritionLogListCreateView(generics.ListCreateAPIView):
    """
    List and create nutrition logs
    """
    serializer_class = NutritionLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = NutritionLog.objects.filter(user=self.request.user)
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def nutrition_dashboard(request):
    """
    Get comprehensive nutrition dashboard data
    """
    try:
        user = request.user
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        # Get today's log
        today_log = NutritionLog.objects.filter(user=user, date=today).first()
        
        # Week summary
        week_logs = NutritionLog.objects.filter(
            user=user,
            date__gte=week_ago,
            date__lte=today
        )
        
        week_avg = week_logs.aggregate(
            avg_calories=Avg('total_calories'),
            avg_protein=Avg('total_protein'),
            avg_adherence=Avg('meal_plan_adherence')
        )
        
        # Active meal plan
        active_meal_plan = MealPlan.objects.filter(
            user=user,
            is_active=True
        ).first()
        
        # Recent recipes
        recent_recipes = Recipe.objects.filter(user=user)[:5]
        
        dashboard_data = {
            'today': {
                'date': today,
                'calories': today_log.total_calories if today_log else 0,
                'protein': today_log.total_protein if today_log else 0,
                'adherence': today_log.meal_plan_adherence if today_log else 100,
                'energy_level': today_log.energy_level if today_log else 5
            },
            'week_average': {
                'calories': round(week_avg['avg_calories'] or 0, 1),
                'protein': round(week_avg['avg_protein'] or 0, 1),
                'adherence': round(week_avg['avg_adherence'] or 100, 1)
            },
            'active_meal_plan': MealPlanSerializer(active_meal_plan).data if active_meal_plan else None,
            'recent_recipes': RecipeSerializer(recent_recipes, many=True).data,
            'stats': {
                'total_recipes': Recipe.objects.filter(user=user).count(),
                'total_meal_plans': MealPlan.objects.filter(user=user).count(),
                'days_logged': NutritionLog.objects.filter(user=user).count()
            }
        }
        
        return Response(dashboard_data)
        
    except Exception as e:
        logger.error(f"Nutrition dashboard error: {str(e)}")
        return Response({
            'error': 'Dashboard data unavailable'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_grocery_list(request, meal_plan_id):
    """
    Generate grocery list from meal plan
    """
    try:
        meal_plan = get_object_or_404(MealPlan, id=meal_plan_id, user=request.user)
        
        # Initialize meal planning service
        meal_service = MealPlanningService()
        
        # Generate grocery list
        grocery_data = meal_service.generate_grocery_list(meal_plan)
        
        # Save to database
        grocery_list = GroceryList.objects.create(
            user=request.user,
            meal_plan=meal_plan,
            name=f"Grocery List - {meal_plan.name}",
            week_start_date=meal_plan.start_date,
            items_data=grocery_data['items'],
            estimated_cost=grocery_data.get('estimated_cost')
        )
       
        serializer = GroceryListSerializer(grocery_list)
        
        return Response({
            'message': 'Grocery list generated successfully',
            'grocery_list': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Grocery list generation failed: {str(e)}")
        return Response({
            'error': 'Grocery list generation failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GroceryListView(generics.ListAPIView):
    """
    List user's grocery lists
    """
    serializer_class = GroceryListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return GroceryList.objects.filter(user=self.request.user)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def nutrition_insights(request):
    """
    Get AI-powered nutrition insights and recommendations
    """
    try:
        user = request.user
        
        # Get recent nutrition data
        recent_logs = NutritionLog.objects.filter(
            user=user,
            date__gte=timezone.now().date() - timedelta(days=30)
        ).order_by('-date')[:30]
        
        if not recent_logs:
            return Response({
                'message': 'Not enough data for insights',
                'insights': []
            })
        
        # Initialize analysis service
        analysis_service = NutritionAnalysisService()
        
        # Generate insights
        insights = analysis_service.generate_user_insights(user, recent_logs)
        
        return Response({
            'insights': insights,
            'data_period': '30 days',
            'total_days_analyzed': len(recent_logs)
        })
        
    except Exception as e:
        logger.error(f"Nutrition insights error: {str(e)}")
        return Response({
            'error': 'Insights generation failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)