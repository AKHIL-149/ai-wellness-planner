# backend/apps/nutrition/services.py

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from django.utils import timezone

from core.ai_client import AIClient
from core.nutrition_api import NutritionAPI
from .models import MealPlan, Meal, Recipe, FoodItem, NutritionLog, GroceryList

logger = logging.getLogger(__name__)

class MealPlanningService:
    """
    Service for AI-powered meal planning and nutrition optimization
    """
    
    def __init__(self):
        self.ai_client = AIClient()
        self.nutrition_api = NutritionAPI()
    
    def generate_personalized_meal_plan(
        self, 
        user_profile, 
        duration_days: int = 7,
        start_date=None,
        preferences: Dict = None
    ) -> Dict:
        """
        Generate a personalized meal plan using AI
        """
        try:
            if start_date is None:
                start_date = timezone.now().date()
            
            # Prepare user profile data for AI
            profile_data = self._prepare_profile_data(user_profile, preferences or {})
            
            # Generate meal plan with AI
            meal_plan_data = self.ai_client.generate_meal_plan(profile_data)
            
            if not meal_plan_data or 'error' in meal_plan_data:
                logger.error("AI meal plan generation failed")
                return {'error': 'AI generation failed'}
            
            # Enhance with nutrition data
            enhanced_plan = self._enhance_with_nutrition_data(meal_plan_data)
            
            # Validate and optimize
            validated_plan = self._validate_meal_plan(enhanced_plan, profile_data)
            
            return validated_plan
            
        except Exception as e:
            logger.error(f"Meal plan generation failed: {str(e)}")
            return {'error': str(e)}
    
    def save_meal_plan_to_db(self, user, meal_plan_data: Dict) -> MealPlan:
        """
        Save AI-generated meal plan to database
        """
        try:
            # Create meal plan
            meal_plan = MealPlan.objects.create(
                user=user,
                name=meal_plan_data.get('plan_name', f"AI Meal Plan - {datetime.now().strftime('%Y-%m-%d')}"),
                description=meal_plan_data.get('description', 'AI-generated personalized meal plan'),
                start_date=meal_plan_data.get('start_date', timezone.now().date()),
                end_date=meal_plan_data.get('end_date', timezone.now().date() + timedelta(days=6)),
                daily_calorie_target=meal_plan_data.get('daily_calories', 2000),
                protein_target_percent=meal_plan_data.get('protein_percent', 20),
                fat_target_percent=meal_plan_data.get('fat_percent', 30),
                carb_target_percent=meal_plan_data.get('carb_percent', 50),
                generated_by_ai=True,
                ai_confidence_score=meal_plan_data.get('confidence_score', 85)
            )
            
            # Create meals
            for day_data in meal_plan_data.get('days', []):
                day_number = day_data.get('day_number', 1)
                
                for meal_type, meal_data in day_data.get('meals', {}).items():
                    meal = Meal.objects.create(
                        meal_plan=meal_plan,
                        name=meal_data.get('name', f'{meal_type.title()} - Day {day_number}'),
                        meal_type=meal_type,
                        day_number=day_number,
                        calories=meal_data.get('calories', 0),
                        protein=meal_data.get('protein', 0),
                        fat=meal_data.get('fat', 0),
                        carbs=meal_data.get('carbs', 0),
                        fiber=meal_data.get('fiber', 0),
                        ai_rationale=meal_data.get('ai_rationale', ''),
                        preparation_notes=meal_data.get('preparation_notes', '')
                    )
                    
                    # Add food items to meal if available
                    for ingredient in meal_data.get('ingredients', []):
                        food_item = self._find_or_create_food_item(ingredient)
                        if food_item:
                            meal.foods.create(
                                food_item=food_item,
                                quantity=ingredient.get('quantity', 100),
                                unit=ingredient.get('unit', 'g')
                            )
            
            logger.info(f"Meal plan saved for user {user.email}: {meal_plan.name}")
            return meal_plan
            
        except Exception as e:
            logger.error(f"Failed to save meal plan: {str(e)}")
            raise e
    
    def generate_grocery_list(self, meal_plan: MealPlan) -> Dict:
        """
        Generate optimized grocery list from meal plan
        """
        try:
            grocery_items = {}
            categories = {}
            
            # Collect all ingredients from meal plan
            for meal in meal_plan.meals.all():
                for meal_food in meal.foods.all():
                    food_name = meal_food.food_item.name
                    quantity = meal_food.quantity
                    category = meal_food.food_item.category or 'Other'
                    
                    if food_name in grocery_items:
                        grocery_items[food_name]['quantity'] += quantity
                    else:
                        grocery_items[food_name] = {
                            'name': food_name,
                            'quantity': quantity,
                            'unit': meal_food.unit,
                            'category': category,
                            'estimated_cost': self._estimate_item_cost(food_name, quantity)
                        }
                    
                    # Group by category
                    if category not in categories:
                        categories[category] = []
                    if food_name not in [item['name'] for item in categories[category]]:
                        categories[category].append(grocery_items[food_name])
            
            # Calculate totals
            total_items = len(grocery_items)
            estimated_total_cost = sum(item.get('estimated_cost', 0) for item in grocery_items.values())
            
            return {
                'items': list(grocery_items.values()),
                'categories': categories,
                'total_items': total_items,
                'estimated_cost': round(estimated_total_cost, 2),
                'shopping_tips': self._generate_shopping_tips(categories)
            }
            
        except Exception as e:
            logger.error(f"Grocery list generation failed: {str(e)}")
            return {'error': str(e)}
    
    def _prepare_profile_data(self, user_profile, preferences: Dict) -> Dict:
        """
        Prepare user profile data for AI consumption
        """
        profile_data = {
            'age': user_profile.age,
            'gender': user_profile.gender,
            'height': user_profile.height,
            'weight': user_profile.weight,
            'target_weight': user_profile.target_weight,
            'activity_level': user_profile.activity_level,
            'fitness_level': user_profile.fitness_level,
            'goals': user_profile.primary_goal,
            'dietary_restrictions': user_profile.dietary_restrictions,
            'food_preferences': user_profile.food_preferences,
            'food_dislikes': user_profile.food_dislikes,
            'cooking_time_available': user_profile.cooking_time_available,
            'preferred_meal_count': user_profile.preferred_meal_count,
            'kitchen_equipment': user_profile.kitchen_equipment,
            'calorie_target': user_profile.calorie_goal,
            'protein_target': user_profile.protein_goal,
            'macro_targets': user_profile.get_macro_targets()
        }
        
        # Add preferences
        profile_data.update(preferences)
        
        return profile_data
    
    def _enhance_with_nutrition_data(self, meal_plan_data: Dict) -> Dict:
        """
        Enhance meal plan with detailed nutrition data from APIs
        """
        try:
            for day_data in meal_plan_data.get('days', []):
                for meal_type, meal_data in day_data.get('meals', {}).items():
                    ingredients = meal_data.get('ingredients', [])
                    
                    if ingredients:
                        # Analyze nutrition for this meal
                        ingredient_strings = [
                            f"{ing.get('quantity', 100)}g {ing.get('name', '')}"
                            for ing in ingredients
                        ]
                        
                        nutrition_analysis = self.nutrition_api.analyze_recipe(
                            ingredient_strings,
                            meal_data.get('name', meal_type)
                        )
                        
                        # Update meal data with detailed nutrition
                        if nutrition_analysis and 'error' not in nutrition_analysis:
                            meal_data.update({
                                'detailed_nutrition': nutrition_analysis.get('nutrients', {}),
                                'health_score': nutrition_analysis.get('health_score', 50),
                                'nutrition_analysis': nutrition_analysis.get('analysis', {})
                            })
            
            return meal_plan_data
            
        except Exception as e:
            logger.warning(f"Nutrition enhancement failed: {str(e)}")
            return meal_plan_data  # Return original data if enhancement fails
    
    def _validate_meal_plan(self, meal_plan_data: Dict, profile_data: Dict) -> Dict:
        """
        Validate and optimize meal plan against user requirements
        """
        try:
            # Calculate daily totals
            for day_data in meal_plan_data.get('days', []):
                daily_totals = {'calories': 0, 'protein': 0, 'fat': 0, 'carbs': 0, 'fiber': 0}
                
                for meal_data in day_data.get('meals', {}).values():
                    daily_totals['calories'] += meal_data.get('calories', 0)
                    daily_totals['protein'] += meal_data.get('protein', 0)
                    daily_totals['fat'] += meal_data.get('fat', 0)
                    daily_totals['carbs'] += meal_data.get('carbs', 0)
                    daily_totals['fiber'] += meal_data.get('fiber', 0)
                
                day_data['daily_totals'] = daily_totals
                
                # Check against targets
                calorie_target = profile_data.get('calorie_target', 2000)
                calorie_variance = abs(daily_totals['calories'] - calorie_target) / calorie_target
                
                day_data['target_adherence'] = {
                    'calorie_variance_percent': round(calorie_variance * 100, 1),
                    'within_target': calorie_variance <= 0.1  # Within 10%
                }
            
            return meal_plan_data
            
        except Exception as e:
            logger.error(f"Meal plan validation failed: {str(e)}")
            return meal_plan_data
    
    def _find_or_create_food_item(self, ingredient_data: Dict) -> Optional[FoodItem]:
        """
        Find existing food item or create new one from ingredient data
        """
        try:
            name = ingredient_data.get('name', '').strip()
            if not name:
                return None
            
            # Try to find existing food item
            food_item = FoodItem.objects.filter(name__iexact=name).first()
            
            if not food_item:
                # Create new food item with basic data
                food_item = FoodItem.objects.create(
                    name=name,
                    calories_per_100g=ingredient_data.get('calories_per_100g', 0),
                    protein_per_100g=ingredient_data.get('protein_per_100g', 0),
                    fat_per_100g=ingredient_data.get('fat_per_100g', 0),
                    carbs_per_100g=ingredient_data.get('carbs_per_100g', 0),
                    fiber_per_100g=ingredient_data.get('fiber_per_100g', 0),
                    data_source='ai_generated'
                )
            
            return food_item
            
        except Exception as e:
            logger.error(f"Food item creation failed: {str(e)}")
            return None
    
    def _estimate_item_cost(self, food_name: str, quantity: float) -> float:
        """
        Estimate cost of grocery item (placeholder implementation)
        """
        # This would integrate with grocery pricing APIs or databases
        # For now, using rough estimates
        
        cost_per_100g = {
            'chicken': 3.00,
            'beef': 5.00,
            'salmon': 8.00,
            'rice': 0.50,
            'pasta': 0.75,
            'bread': 1.50,
            'milk': 1.00,
            'eggs': 2.50,
            'cheese': 4.00,
            'yogurt': 1.50,
            'apple': 1.00,
            'banana': 0.60,
            'broccoli': 1.20,
            'spinach': 2.00,
            'olive oil': 3.00
        }
        
        # Simple matching
        for item, cost in cost_per_100g.items():
            if item.lower() in food_name.lower():
                return round((quantity / 100) * cost, 2)
        
        # Default estimate
        return round((quantity / 100) * 1.50, 2)
    
    def _generate_shopping_tips(self, categories: Dict) -> List[str]:
        """
        Generate helpful shopping tips based on grocery list
        """
        tips = []
        
        if 'Fruits' in categories and len(categories['Fruits']) > 3:
            tips.append("Buy fruits at varying ripeness levels to last the whole week")
        
        if 'Vegetables' in categories:
            tips.append("Shop for vegetables 2-3 times per week for maximum freshness")
        
        if 'Proteins' in categories and len(categories['Proteins']) > 2:
            tips.append("Consider buying proteins in bulk and freezing portions")
        
        tips.append("Check store flyers for weekly specials on your list items")
        tips.append("Bring reusable bags and stick to your list to avoid impulse purchases")
        
        return tips

class NutritionAnalysisService:
    """
    Service for analyzing nutrition patterns and generating insights
    """
    
    def __init__(self):
        self.ai_client = AIClient()
        self.nutrition_api = NutritionAPI()
    
    def generate_user_insights(self, user, nutrition_logs: List[NutritionLog]) -> List[Dict]:
        """
        Generate personalized nutrition insights from user's logs
        """
        try:
            insights = []
            
            if not nutrition_logs:
                return insights
            
            # Analyze patterns
            patterns = self._analyze_nutrition_patterns(nutrition_logs)
            
            # Generate specific insights
            insights.extend(self._generate_calorie_insights(patterns))
            insights.extend(self._generate_macronutrient_insights(patterns))
            insights.extend(self._generate_adherence_insights(patterns))
            insights.extend(self._generate_energy_insights(patterns))
            
            # Sort by priority
            insights.sort(key=lambda x: self._get_priority_score(x), reverse=True)
            
            return insights[:10]  # Return top 10 insights
            
        except Exception as e:
            logger.error(f"Insight generation failed: {str(e)}")
            return []
    
    def _analyze_nutrition_patterns(self, logs: List[NutritionLog]) -> Dict:
        """
        Analyze patterns in nutrition logs
        """
        if not logs:
            return {}
        
        # Calculate averages
        total_logs = len(logs)
        avg_calories = sum(log.total_calories for log in logs) / total_logs
        avg_protein = sum(log.total_protein for log in logs) / total_logs
        avg_adherence = sum(log.meal_plan_adherence for log in logs) / total_logs
        avg_energy = sum(log.energy_level for log in logs) / total_logs
        
        # Calculate trends (comparing first half vs second half)
        mid_point = total_logs // 2
        recent_logs = logs[:mid_point] if logs else []
        older_logs = logs[mid_point:] if logs else []
        
        calorie_trend = 0
        energy_trend = 0
        
        if recent_logs and older_logs:
            recent_avg_calories = sum(log.total_calories for log in recent_logs) / len(recent_logs)
            older_avg_calories = sum(log.total_calories for log in older_logs) / len(older_logs)
            calorie_trend = recent_avg_calories - older_avg_calories
            
            recent_avg_energy = sum(log.energy_level for log in recent_logs) / len(recent_logs)
            older_avg_energy = sum(log.energy_level for log in older_logs) / len(older_logs)
            energy_trend = recent_avg_energy - older_avg_energy
        
        return {
            'avg_calories': avg_calories,
            'avg_protein': avg_protein,
            'avg_adherence': avg_adherence,
            'avg_energy': avg_energy,
            'calorie_trend': calorie_trend,
            'energy_trend': energy_trend,
            'total_days': total_logs,
            'consistency_score': self._calculate_consistency_score(logs)
        }
    
    def _generate_calorie_insights(self, patterns: Dict) -> List[Dict]:
        """
        Generate insights about calorie intake patterns
        """
        insights = []
        avg_calories = patterns.get('avg_calories', 0)
        calorie_trend = patterns.get('calorie_trend', 0)
        
        if avg_calories < 1200:
            insights.append({
                'type': 'calorie_concern',
                'priority': 'high',
                'title': 'Very Low Calorie Intake',
                'message': f'Your average intake of {avg_calories:.0f} calories may be too low for optimal health.',
                'recommendation': 'Consider increasing your calorie intake with nutrient-dense foods.',
                'action': 'Consult with a healthcare provider about appropriate calorie goals.'
            })
        elif avg_calories > 3000:
            insights.append({
                'type': 'calorie_concern',
                'priority': 'medium',
                'title': 'High Calorie Intake',
                'message': f'Your average intake of {avg_calories:.0f} calories is quite high.',
                'recommendation': 'Review portion sizes and consider more nutrient-dense, lower-calorie options.',
                'action': 'Track your hunger and fullness cues to guide portion sizes.'
            })
        
        if calorie_trend > 200:
            insights.append({
                'type': 'trend',
                'priority': 'medium',
                'title': 'Increasing Calorie Trend',
                'message': f'Your calorie intake has increased by {calorie_trend:.0f} calories recently.',
                'recommendation': 'Monitor this trend and ensure it aligns with your health goals.',
                'action': 'Review recent meal choices and portion sizes.'
            })
        
        return insights
    
    def _generate_macronutrient_insights(self, patterns: Dict) -> List[Dict]:
        """
        Generate insights about macronutrient balance
        """
        insights = []
        avg_protein = patterns.get('avg_protein', 0)
        avg_calories = patterns.get('avg_calories', 0)
        
        if avg_calories > 0:
            protein_percent = (avg_protein * 4) / avg_calories * 100
            
            if protein_percent < 15:
                insights.append({
                    'type': 'macronutrient',
                    'priority': 'medium',
                    'title': 'Low Protein Intake',
                    'message': f'Protein makes up only {protein_percent:.1f}% of your calories.',
                    'recommendation': 'Aim for 15-25% of calories from protein for optimal health.',
                    'action': 'Add lean proteins like chicken, fish, beans, or Greek yogurt to meals.'
                })
            elif protein_percent > 30:
                insights.append({
                    'type': 'macronutrient',
                    'priority': 'low',
                    'title': 'High Protein Intake',
                    'message': f'Protein makes up {protein_percent:.1f}% of your calories.',
                    'recommendation': 'Ensure adequate carbohydrate intake for energy and fiber.',
                    'action': 'Balance meals with whole grains, fruits, and vegetables.'
                })
        
        return insights
    
    def _generate_adherence_insights(self, patterns: Dict) -> List[Dict]:
        """
        Generate insights about meal plan adherence
        """
        insights = []
        avg_adherence = patterns.get('avg_adherence', 100)
        
        if avg_adherence < 70:
            insights.append({
                'type': 'adherence',
                'priority': 'high',
                'title': 'Low Meal Plan Adherence',
                'message': f'Your meal plan adherence is {avg_adherence:.1f}%.',
                'recommendation': 'Identify barriers to following your meal plan.',
                'action': 'Consider adjusting your meal plan to better fit your lifestyle and preferences.'
            })
        elif avg_adherence > 90:
            insights.append({
                'type': 'adherence',
                'priority': 'positive',
                'title': 'Excellent Adherence',
                'message': f'Great job! Your meal plan adherence is {avg_adherence:.1f}%.',
                'recommendation': 'Keep up the excellent work with your nutrition plan.',
                'action': 'Consider sharing your success strategies with others.'
            })
        
        return insights
    
    def _generate_energy_insights(self, patterns: Dict) -> List[Dict]:
        """
        Generate insights about energy levels
        """
        insights = []
        avg_energy = patterns.get('avg_energy', 5)
        energy_trend = patterns.get('energy_trend', 0)
        
        if avg_energy < 4:
            insights.append({
                'type': 'energy',
                'priority': 'high',
                'title': 'Low Energy Levels',
                'message': f'Your average energy level is {avg_energy:.1f}/10.',
                'recommendation': 'Review your nutrition timing and meal balance.',
                'action': 'Ensure adequate calories, regular meal timing, and balanced macronutrients.'
            })
        elif energy_trend < -1:
            insights.append({
                'type': 'energy',
                'priority': 'medium',
                'title': 'Declining Energy Trend',
                'message': 'Your energy levels have been declining recently.',
                'recommendation': 'Evaluate recent changes in diet, sleep, or stress levels.',
                'action': 'Consider adjusting meal timing or adding energizing foods like complex carbs.'
            })
        
        return insights
    
    def _calculate_consistency_score(self, logs: List[NutritionLog]) -> float:
        """
        Calculate consistency score based on calorie variance
        """
        if len(logs) < 2:
            return 100.0
        
        calories = [log.total_calories for log in logs]
        avg_calories = sum(calories) / len(calories)
        
        if avg_calories == 0:
            return 0.0
        
        variance = sum((cal - avg_calories) ** 2 for cal in calories) / len(calories)
        coefficient_of_variation = (variance ** 0.5) / avg_calories
        
        # Convert to consistency score (0-100, higher is more consistent)
        consistency_score = max(0, 100 - (coefficient_of_variation * 100))
        
        return round(consistency_score, 1)
    
    def _get_priority_score(self, insight: Dict) -> int:
        """
        Get numerical priority score for sorting insights
        """
        priority_scores = {
            'high': 3,
            'medium': 2,
            'low': 1,
            'positive': 1
        }
        
        return priority_scores.get(insight.get('priority', 'low'), 1)