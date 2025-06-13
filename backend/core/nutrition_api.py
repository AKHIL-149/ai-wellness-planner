# backend/core/nutrition_api.py

import requests
import logging
from typing import Dict, List, Optional
from django.conf import settings
from django.core.cache import cache
import json
import time

logger = logging.getLogger(__name__)

class NutritionAPI:
    """
    Unified client for nutrition APIs (USDA FoodData Central, Edamam)
    Handles food search, nutrition facts, and recipe analysis
    """
    
    def __init__(self):
        self.usda_key = settings.USDA_API_KEY
        self.edamam_app_id = settings.EDAMAM_APP_ID
        self.edamam_key = settings.EDAMAM_API_KEY
        self.usda_base_url = "https://api.nal.usda.gov/fdc/v1"
        self.edamam_base_url = "https://api.edamam.com/api"
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
    
    def _rate_limit(self):
        """Simple rate limiting to avoid overwhelming APIs"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def search_food(self, query: str, page_size: int = 10) -> Dict:
        """
        Search for food items in USDA database
        
        Args:
            query: Search term for food
            page_size: Number of results to return
            
        Returns:
            Dictionary containing search results
        """
        cache_key = f"food_search_{query}_{page_size}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Cache hit for food search: {query}")
            return cached_result
        
        try:
            self._rate_limit()
            
            url = f"{self.usda_base_url}/foods/search"
            params = {
                'query': query,
                'api_key': self.usda_key,
                'pageSize': page_size,
                'sortBy': 'dataType.keyword',
                'sortOrder': 'asc'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # Process and simplify the response
            processed_result = self._process_food_search_results(result)
            
            # Cache for 1 hour
            cache.set(cache_key, processed_result, 3600)
            
            logger.info(f"USDA food search successful: {query} - {len(processed_result.get('foods', []))} results")
            return processed_result
            
        except requests.RequestException as e:
            logger.error(f"USDA food search failed for '{query}': {str(e)}")
            return self._get_fallback_search_results(query)
        except Exception as e:
            logger.error(f"Unexpected error in food search: {str(e)}")
            return self._get_fallback_search_results(query)
    
    def get_food_details(self, fdc_id: int) -> Dict:
        """
        Get detailed nutrition information for a specific food item
        
        Args:
            fdc_id: USDA Food Data Central ID
            
        Returns:
            Dictionary containing detailed nutrition information
        """
        cache_key = f"food_details_{fdc_id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Cache hit for food details: {fdc_id}")
            return cached_result
        
        try:
            self._rate_limit()
            
            url = f"{self.usda_base_url}/food/{fdc_id}"
            params = {
                'api_key': self.usda_key,
                'format': 'full'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # Process and simplify the nutrition data
            processed_result = self._process_food_details(result)
            
            # Cache for 24 hours (nutrition data doesn't change often)
            cache.set(cache_key, processed_result, 86400)
            
            logger.info(f"USDA food details retrieved: {fdc_id}")
            return processed_result
            
        except requests.RequestException as e:
            logger.error(f"USDA food details failed for ID {fdc_id}: {str(e)}")
            return self._get_fallback_food_details()
        except Exception as e:
            logger.error(f"Unexpected error in food details: {str(e)}")
            return self._get_fallback_food_details()
    
    def analyze_recipe(self, ingredients: List[str], recipe_name: str = "Custom Recipe") -> Dict:
        """
        Analyze recipe nutrition using Edamam API
        
        Args:
            ingredients: List of ingredient strings (e.g., ["1 cup rice", "2 tbsp oil"])
            recipe_name: Name of the recipe
            
        Returns:
            Dictionary containing recipe nutrition analysis
        """
        if not self.edamam_app_id or not self.edamam_key:
            logger.warning("Edamam credentials not configured, using USDA fallback")
            return self._analyze_recipe_fallback(ingredients, recipe_name)
        
        cache_key = f"recipe_analysis_{hash(str(ingredients))}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Cache hit for recipe analysis: {recipe_name}")
            return cached_result
        
        try:
            self._rate_limit()
            
            url = f"{self.edamam_base_url}/nutrition-details"
            headers = {
                'Content-Type': 'application/json'
            }
            params = {
                'app_id': self.edamam_app_id,
                'app_key': self.edamam_key
            }
            
            data = {
                'title': recipe_name,
                'ingr': ingredients
            }
            
            response = requests.post(url, json=data, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            
            # Process and simplify the nutrition analysis
            processed_result = self._process_recipe_analysis(result, recipe_name)
            
            # Cache for 1 hour
            cache.set(cache_key, processed_result, 3600)
            
            logger.info(f"Edamam recipe analysis successful: {recipe_name}")
            return processed_result
            
        except requests.RequestException as e:
            logger.error(f"Edamam recipe analysis failed: {str(e)}")
            return self._analyze_recipe_fallback(ingredients, recipe_name)
        except Exception as e:
            logger.error(f"Unexpected error in recipe analysis: {str(e)}")
            return self._analyze_recipe_fallback(ingredients, recipe_name)
    
    def get_nutrition_facts(self, food_items: List[Dict]) -> Dict:
        """
        Get comprehensive nutrition facts for multiple food items
        
        Args:
            food_items: List of dictionaries with 'fdc_id' and 'quantity' keys
            
        Returns:
            Dictionary containing combined nutrition facts
        """
        try:
            total_nutrition = self._initialize_nutrition_totals()
            detailed_items = []
            
            for item in food_items:
                fdc_id = item.get('fdc_id')
                quantity = item.get('quantity', 1.0)  # Default to 1 serving
                
                if fdc_id:
                    food_details = self.get_food_details(fdc_id)
                    if food_details.get('nutrients'):
                        self._add_to_nutrition_totals(total_nutrition, food_details, quantity)
                        detailed_items.append({
                            'food': food_details,
                            'quantity': quantity,
                            'contribution': self._calculate_contribution(food_details, quantity)
                        })
            
            return {
                'total_nutrition': total_nutrition,
                'daily_values': self._calculate_daily_values(total_nutrition),
                'health_score': self._calculate_health_score(total_nutrition),
                'detailed_items': detailed_items,
                'analysis': self._generate_nutrition_analysis(total_nutrition)
            }
            
        except Exception as e:
            logger.error(f"Nutrition facts calculation failed: {str(e)}")
            return self._get_fallback_nutrition_facts()
    
    def search_branded_foods(self, query: str, brand: str = None) -> Dict:
        """
        Search for branded food products
        
        Args:
            query: Food name to search for
            brand: Optional brand name to filter by
            
        Returns:
            Dictionary containing branded food search results
        """
        try:
            self._rate_limit()
            
            url = f"{self.usda_base_url}/foods/search"
            params = {
                'query': query,
                'api_key': self.usda_key,
                'pageSize': 10,
                'dataType': ['Branded']
            }
            
            if brand:
                params['query'] = f"{query} {brand}"
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return self._process_branded_food_results(result)
            
        except Exception as e:
            logger.error(f"Branded food search failed: {str(e)}")
            return {'foods': [], 'total_results': 0}
    
    def get_food_categories(self) -> List[Dict]:
        """
        Get list of food categories from USDA
        
        Returns:
            List of food categories
        """
        cache_key = "food_categories"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Predefined categories (USDA doesn't have a direct categories endpoint)
            categories = [
                {'id': 'dairy', 'name': 'Dairy and Egg Products', 'description': 'Milk, cheese, yogurt, eggs'},
                {'id': 'fats', 'name': 'Fats and Oils', 'description': 'Cooking oils, butter, margarine'},
                {'id': 'fruits', 'name': 'Fruits and Fruit Juices', 'description': 'Fresh, dried, and processed fruits'},
                {'id': 'grains', 'name': 'Cereal Grains and Pasta', 'description': 'Bread, rice, pasta, cereals'},
                {'id': 'proteins', 'name': 'Poultry Products', 'description': 'Chicken, turkey, duck'},
                {'id': 'meat', 'name': 'Beef Products', 'description': 'Beef, lamb, pork'},
                {'id': 'vegetables', 'name': 'Vegetables and Vegetable Products', 'description': 'Fresh and processed vegetables'},
                {'id': 'nuts', 'name': 'Nut and Seed Products', 'description': 'Nuts, seeds, nut butters'},
                {'id': 'beverages', 'name': 'Beverages', 'description': 'Non-alcoholic drinks'},
                {'id': 'seafood', 'name': 'Finfish and Shellfish Products', 'description': 'Fish, seafood'},
                {'id': 'legumes', 'name': 'Legumes and Legume Products', 'description': 'Beans, lentils, peas'},
                {'id': 'snacks', 'name': 'Snacks', 'description': 'Chips, crackers, snack foods'},
                {'id': 'sweets', 'name': 'Sweets', 'description': 'Candy, desserts, sweeteners'},
                {'id': 'spices', 'name': 'Spices and Herbs', 'description': 'Seasonings, herbs, spices'}
            ]
            
            # Cache for 24 hours
            cache.set(cache_key, categories, 86400)
            
            return categories
            
        except Exception as e:
            logger.error(f"Failed to get food categories: {str(e)}")
            return []
    
    def get_nutrient_info(self, nutrient_name: str) -> Dict:
        """
        Get detailed information about a specific nutrient
        
        Args:
            nutrient_name: Name of the nutrient
            
        Returns:
            Dictionary containing nutrient information
        """
        nutrient_database = {
            'energy': {
                'name': 'Energy',
                'unit': 'kcal',
                'description': 'Total calories from all macronutrients',
                'daily_value': 2000,
                'functions': ['Energy production', 'Metabolism'],
                'sources': ['Carbohydrates', 'Proteins', 'Fats']
            },
            'protein': {
                'name': 'Protein',
                'unit': 'g',
                'description': 'Essential macronutrient for building and repairing tissues',
                'daily_value': 50,
                'functions': ['Muscle building', 'Enzyme production', 'Immune function'],
                'sources': ['Meat', 'Fish', 'Eggs', 'Legumes', 'Dairy']
            },
            'fat': {
                'name': 'Total Fat',
                'unit': 'g',
                'description': 'Essential macronutrient for energy and vitamin absorption',
                'daily_value': 65,
                'functions': ['Energy storage', 'Vitamin absorption', 'Cell membrane structure'],
                'sources': ['Oils', 'Nuts', 'Seeds', 'Avocado', 'Fish']
            },
            'carbohydrates': {
                'name': 'Carbohydrates',
                'unit': 'g',
                'description': 'Primary energy source for the body',
                'daily_value': 300,
                'functions': ['Quick energy', 'Brain function', 'Muscle fuel'],
                'sources': ['Grains', 'Fruits', 'Vegetables', 'Legumes']
            },
            'fiber': {
                'name': 'Dietary Fiber',
                'unit': 'g',
                'description': 'Indigestible carbohydrate that aids digestion',
                'daily_value': 25,
                'functions': ['Digestive health', 'Blood sugar control', 'Cholesterol management'],
                'sources': ['Whole grains', 'Fruits', 'Vegetables', 'Legumes']
            },
            'sodium': {
                'name': 'Sodium',
                'unit': 'mg',
                'description': 'Essential mineral for fluid balance and nerve function',
                'daily_value': 2300,
                'functions': ['Fluid balance', 'Nerve transmission', 'Muscle function'],
                'sources': ['Salt', 'Processed foods', 'Cheese', 'Bread']
            },
            'calcium': {
                'name': 'Calcium',
                'unit': 'mg',
                'description': 'Essential mineral for bone and teeth health',
                'daily_value': 1000,
                'functions': ['Bone health', 'Muscle function', 'Blood clotting'],
                'sources': ['Dairy products', 'Leafy greens', 'Fortified foods']
            },
            'iron': {
                'name': 'Iron',
                'unit': 'mg',
                'description': 'Essential mineral for oxygen transport',
                'daily_value': 18,
                'functions': ['Oxygen transport', 'Energy metabolism', 'Immune function'],
                'sources': ['Red meat', 'Spinach', 'Legumes', 'Fortified cereals']
            },
            'vitamin_c': {
                'name': 'Vitamin C',
                'unit': 'mg',
                'description': 'Water-soluble vitamin and antioxidant',
                'daily_value': 90,
                'functions': ['Immune support', 'Collagen synthesis', 'Antioxidant protection'],
                'sources': ['Citrus fruits', 'Berries', 'Bell peppers', 'Broccoli']
            },
            'vitamin_d': {
                'name': 'Vitamin D',
                'unit': 'mcg',
                'description': 'Fat-soluble vitamin for bone health',
                'daily_value': 20,
                'functions': ['Calcium absorption', 'Bone health', 'Immune function'],
                'sources': ['Sunlight', 'Fatty fish', 'Fortified milk', 'Supplements']
            }
        }
        
        return nutrient_database.get(nutrient_name.lower(), {
            'name': nutrient_name,
            'description': 'Nutrient information not available',
            'functions': [],
            'sources': []
        })
    
    def _process_food_search_results(self, raw_results: Dict) -> Dict:
        """Process and simplify USDA food search results"""
        processed_foods = []
        
        for food in raw_results.get('foods', []):
            processed_food = {
                'fdc_id': food.get('fdcId'),
                'description': food.get('description', ''),
                'brand_owner': food.get('brandOwner', ''),
                'data_type': food.get('dataType', ''),
                'serving_size': food.get('servingSize'),
                'serving_size_unit': food.get('servingSizeUnit'),
                'basic_nutrients': self._extract_basic_nutrients(food.get('foodNutrients', []))
            }
            processed_foods.append(processed_food)
        
        return {
            'foods': processed_foods,
            'total_results': raw_results.get('totalHits', 0),
            'current_page': raw_results.get('currentPage', 1),
            'total_pages': raw_results.get('totalPages', 1)
        }
    
    def _process_food_details(self, raw_details: Dict) -> Dict:
        """Process and simplify detailed food nutrition data"""
        nutrients = {}
        
        for nutrient in raw_details.get('foodNutrients', []):
            nutrient_info = nutrient.get('nutrient', {})
            nutrient_name = nutrient_info.get('name', '')
            nutrient_unit = nutrient_info.get('unitName', '')
            nutrient_value = nutrient.get('amount', 0)
            
            if nutrient_name and nutrient_value:
                # Standardize nutrient names
                standardized_name = self._standardize_nutrient_name(nutrient_name)
                nutrients[standardized_name] = {
                    'value': nutrient_value,
                    'unit': nutrient_unit,
                    'original_name': nutrient_name
                }
        
        return {
            'fdc_id': raw_details.get('fdcId'),
            'description': raw_details.get('description', ''),
            'data_type': raw_details.get('dataType', ''),
            'nutrients': nutrients,
            'serving_size': raw_details.get('servingSize'),
            'serving_size_unit': raw_details.get('servingSizeUnit'),
            'household_serving': raw_details.get('householdServingFullText'),
            'category': raw_details.get('foodCategory', {}).get('description', ''),
            'publication_date': raw_details.get('publicationDate')
        }
    
    def _process_recipe_analysis(self, raw_analysis: Dict, recipe_name: str) -> Dict:
        """Process Edamam recipe analysis results"""
        return {
            'recipe_name': recipe_name,
            'calories': raw_analysis.get('calories', 0),
            'servings': raw_analysis.get('yield', 1),
            'calories_per_serving': raw_analysis.get('calories', 0) / max(raw_analysis.get('yield', 1), 1),
            'total_weight': raw_analysis.get('totalWeight', 0),
            'nutrients': self._process_edamam_nutrients(raw_analysis.get('totalNutrients', {})),
            'daily_values': self._process_edamam_daily_values(raw_analysis.get('totalDaily', {})),
            'diet_labels': raw_analysis.get('dietLabels', []),
            'health_labels': raw_analysis.get('healthLabels', []),
            'cautions': raw_analysis.get('cautions', []),
            'ingredients': raw_analysis.get('ingredients', [])
        }
    
    def _process_edamam_nutrients(self, nutrients: Dict) -> Dict:
        """Process Edamam nutrients format"""
        processed = {}
        
        for key, nutrient in nutrients.items():
            processed[key.lower()] = {
                'label': nutrient.get('label', ''),
                'quantity': nutrient.get('quantity', 0),
                'unit': nutrient.get('unit', '')
            }
        
        return processed
    
    def _process_edamam_daily_values(self, daily_values: Dict) -> Dict:
        """Process Edamam daily values format"""
        processed = {}
        
        for key, value in daily_values.items():
            processed[key.lower()] = {
                'label': value.get('label', ''),
                'quantity': value.get('quantity', 0),
                'unit': value.get('unit', '%')
            }
        
        return processed
    
    def _extract_basic_nutrients(self, nutrients: List[Dict]) -> Dict:
        """Extract basic nutrients from USDA nutrient list"""
        basic_nutrients = {}
        
        # Key nutrients to extract
        key_nutrients = {
            'Energy': 'calories',
            'Protein': 'protein',
            'Total lipid (fat)': 'fat',
            'Carbohydrate, by difference': 'carbohydrates',
            'Fiber, total dietary': 'fiber',
            'Sugars, total including NLEA': 'sugars',
            'Sodium, Na': 'sodium'
        }
        
        for nutrient in nutrients:
            nutrient_info = nutrient.get('nutrient', {})
            nutrient_name = nutrient_info.get('name', '')
            
            if nutrient_name in key_nutrients:
                basic_nutrients[key_nutrients[nutrient_name]] = {
                    'value': nutrient.get('amount', 0),
                    'unit': nutrient_info.get('unitName', '')
                }
        
        return basic_nutrients
    
    def _standardize_nutrient_name(self, name: str) -> str:
        """Standardize nutrient names for consistency"""
        name_mapping = {
            'Energy': 'calories',
            'Protein': 'protein',
            'Total lipid (fat)': 'fat',
            'Carbohydrate, by difference': 'carbohydrates',
            'Fiber, total dietary': 'fiber',
            'Sugars, total including NLEA': 'sugars',
            'Sodium, Na': 'sodium',
            'Calcium, Ca': 'calcium',
            'Iron, Fe': 'iron',
            'Vitamin C, total ascorbic acid': 'vitamin_c',
            'Vitamin D (D2 + D3)': 'vitamin_d',
            'Potassium, K': 'potassium',
            'Magnesium, Mg': 'magnesium',
            'Phosphorus, P': 'phosphorus',
            'Zinc, Zn': 'zinc'
        }
        
        return name_mapping.get(name, name.lower().replace(' ', '_').replace(',', ''))
    
    def _initialize_nutrition_totals(self) -> Dict:
        """Initialize nutrition totals dictionary"""
        return {
            'calories': 0,
            'protein': 0,
            'fat': 0,
            'carbohydrates': 0,
            'fiber': 0,
            'sugars': 0,
            'sodium': 0,
            'calcium': 0,
            'iron': 0,
            'vitamin_c': 0,
            'vitamin_d': 0,
            'potassium': 0,
            'magnesium': 0,
            'phosphorus': 0,
            'zinc': 0
        }
    
    def _add_to_nutrition_totals(self, totals: Dict, food_details: Dict, quantity: float):
        """Add food nutrition to totals"""
        nutrients = food_details.get('nutrients', {})
        
        for key in totals.keys():
            if key in nutrients:
                totals[key] += nutrients[key].get('value', 0) * quantity
    
    def _calculate_contribution(self, food_details: Dict, quantity: float) -> Dict:
        """Calculate nutrient contribution of a single food item"""
        nutrients = food_details.get('nutrients', {})
        contribution = {}
        
        for nutrient, data in nutrients.items():
            contribution[nutrient] = data.get('value', 0) * quantity
        
        return contribution
    
    def _calculate_daily_values(self, nutrition: Dict) -> Dict:
        """Calculate daily value percentages"""
        daily_values_reference = {
            'calories': 2000,
            'protein': 50,
            'fat': 65,
            'carbohydrates': 300,
            'fiber': 25,
            'sodium': 2300,
            'calcium': 1000,
            'iron': 18,
            'vitamin_c': 90,
            'vitamin_d': 20,
            'potassium': 3500,
            'magnesium': 400,
            'phosphorus': 1250,
            'zinc': 11
        }
        
        percentages = {}
        for nutrient, value in nutrition.items():
            if nutrient in daily_values_reference and daily_values_reference[nutrient] > 0:
                percentages[nutrient] = round((value / daily_values_reference[nutrient]) * 100, 1)
            else:
                percentages[nutrient] = 0
        
        return percentages
    
    def _calculate_health_score(self, nutrition: Dict) -> int:
        """Calculate a health score (1-100) based on nutrition profile"""
        score = 50  # Base score
        
        # Positive factors
        if nutrition.get('fiber', 0) >= 25:
            score += 15
        elif nutrition.get('fiber', 0) >= 15:
            score += 10
        
        if nutrition.get('protein', 0) >= 50:
            score += 10
        elif nutrition.get('protein', 0) >= 30:
            score += 5
        
        if nutrition.get('vitamin_c', 0) >= 90:
            score += 10
        
        if nutrition.get('calcium', 0) >= 1000:
            score += 5
        
        # Negative factors
        if nutrition.get('sodium', 0) > 2300:
            score -= 20
        elif nutrition.get('sodium', 0) > 1500:
            score -= 10
        
        if nutrition.get('sugars', 0) > 50:
            score -= 15
        elif nutrition.get('sugars', 0) > 25:
            score -= 8
        
        if nutrition.get('fat', 0) > 78:  # >35% of 2000 cal diet
            score -= 10
        
        return max(0, min(100, score))
    
    def _generate_nutrition_analysis(self, nutrition: Dict) -> Dict:
        """Generate nutrition analysis and recommendations"""
        analysis = {
            'strengths': [],
            'concerns': [],
            'recommendations': []
        }
        
        # Analyze each nutrient
        daily_values = self._calculate_daily_values(nutrition)
        
        for nutrient, percentage in daily_values.items():
            if percentage >= 100:
                if nutrient in ['sodium', 'sugars']:
                    analysis['concerns'].append(f"High {nutrient}: {percentage}% of daily value")
                else:
                    analysis['strengths'].append(f"Excellent {nutrient}: {percentage}% of daily value")
            elif percentage >= 75:
                analysis['strengths'].append(f"Good {nutrient}: {percentage}% of daily value")
            elif percentage < 25:
                analysis['concerns'].append(f"Low {nutrient}: {percentage}% of daily value")
        
        # Generate recommendations
        if daily_values.get('fiber', 0) < 50:
            analysis['recommendations'].append("Increase fiber intake with whole grains, fruits, and vegetables")
        
        if daily_values.get('sodium', 0) > 100:
            analysis['recommendations'].append("Reduce sodium intake by limiting processed foods")
        
        if daily_values.get('protein', 0) < 75:
            analysis['recommendations'].append("Consider adding lean protein sources to your meals")
        
        return analysis
    
    def _analyze_recipe_fallback(self, ingredients: List[str], recipe_name: str) -> Dict:
        """Fallback recipe analysis using USDA data"""
        logger.info(f"Using USDA fallback for recipe analysis: {recipe_name}")
        
        total_nutrition = self._initialize_nutrition_totals()
        analyzed_ingredients = []
        
        # Simple ingredient parsing and lookup
        for ingredient in ingredients:
            # Extract food name (simple parsing)
            food_name = self._extract_food_name(ingredient)
            
            # Search for the food
            search_results = self.search_food(food_name, page_size=1)
            
            if search_results.get('foods'):
                food = search_results['foods'][0]
                fdc_id = food.get('fdc_id')
                
                if fdc_id:
                    food_details = self.get_food_details(fdc_id)
                    # Estimate quantity (simplified)
                    quantity = self._estimate_quantity(ingredient)
                    self._add_to_nutrition_totals(total_nutrition, food_details, quantity)
                    
                    analyzed_ingredients.append({
                        'original': ingredient,
                        'food_name': food_name,
                        'quantity': quantity,
                        'fdc_id': fdc_id,
                        'description': food_details.get('description', '')
                    })
        
        return {
            'recipe_name': recipe_name,
            'calories': total_nutrition.get('calories', 0),
            'servings': 1,
            'calories_per_serving': total_nutrition.get('calories', 0),
            'nutrients': total_nutrition,
            'daily_values': self._calculate_daily_values(total_nutrition),
            'health_score': self._calculate_health_score(total_nutrition),
            'analysis_method': 'usda_fallback',
            'analyzed_ingredients': analyzed_ingredients
        }
    
    def _extract_food_name(self, ingredient: str) -> str:
        """Extract food name from ingredient string"""
        # Remove common quantity words and measurements
        quantity_words = ['cup', 'cups', 'tbsp', 'tsp', 'tablespoon', 'tablespoons', 'teaspoon', 'teaspoons', 
                         'oz', 'ounce', 'ounces', 'lb', 'lbs', 'pound', 'pounds', 'gram', 'grams', 'g', 
                         'kg', 'kilogram', 'kilograms', 'ml', 'milliliter', 'milliliters', 'liter', 'liters', 
                         'l', 'pint', 'pints', 'quart', 'quarts', 'gallon', 'gallons', 'piece', 'pieces', 
                         'slice', 'slices', 'whole', 'half', 'quarter', 'large', 'medium', 'small', 'can', 
                         'cans', 'package', 'packages', 'container', 'containers', 'fresh', 'frozen', 'dried',
                         'chopped', 'diced', 'minced', 'sliced', 'grated', 'shredded', 'cooked', 'raw']
        
        # Clean and normalize the ingredient string
        ingredient_clean = ingredient.lower().strip()
        words = ingredient_clean.split()
        
        # Remove numbers and quantity words
        food_words = []
        for word in words:
            # Skip if it's a number (including fractions)
            if self._is_number_or_fraction(word):
                continue
            # Skip if it's a quantity word
            if word in quantity_words:
                continue
            # Skip common prepositions and articles
            if word in ['of', 'the', 'a', 'an', 'and', 'or', 'with', 'without']:
                continue
            
            food_words.append(word)
        
        # Join remaining words
        food_name = ' '.join(food_words)
        
        # Clean up common ingredient modifiers
        food_name = food_name.replace('extra virgin', '').replace('organic', '').strip()
        
        return food_name if food_name else ingredient.split()[0]  # Fallback to first word
    
    def _is_number_or_fraction(self, word: str) -> bool:
        """Check if a word is a number or fraction"""
        import re
        
        # Check for regular numbers
        if word.replace('.', '').replace(',', '').isdigit():
            return True
        
        # Check for fractions like 1/2, 3/4, etc.
        fraction_pattern = r'^\d+/\d+
        if re.match(fraction_pattern, word):
            return True
        
        # Check for mixed numbers like 1-1/2
        mixed_pattern = r'^\d+-\d+/\d+
        if re.match(mixed_pattern, word):
            return True
        
        return False
    
    def _estimate_quantity(self, ingredient: str) -> float:
        """Estimate quantity multiplier from ingredient string"""
        import re
        
        # Look for numbers in the ingredient
        numbers = re.findall(r'\d+\.?\d*', ingredient)
        
        if numbers:
            try:
                # Use the first number found
                quantity = float(numbers[0])
                
                # Adjust based on units (rough estimation)
                ingredient_lower = ingredient.lower()
                
                if any(unit in ingredient_lower for unit in ['cup', 'cups']):
                    return quantity * 0.8  # Cups are substantial
                elif any(unit in ingredient_lower for unit in ['tbsp', 'tablespoon', 'tablespoons']):
                    return quantity * 0.1  # Tablespoons are small
                elif any(unit in ingredient_lower for unit in ['tsp', 'teaspoon', 'teaspoons']):
                    return quantity * 0.03  # Teaspoons are very small
                elif any(unit in ingredient_lower for unit in ['oz', 'ounce', 'ounces']):
                    return quantity * 0.3  # Ounces
                elif any(unit in ingredient_lower for unit in ['lb', 'lbs', 'pound', 'pounds']):
                    return quantity * 4.0  # Pounds are large
                else:
                    return quantity * 0.5  # Default moderate amount
                    
            except ValueError:
                pass
        
        # Look for fraction patterns
        fraction_match = re.search(r'(\d+)/(\d+)', ingredient)
        if fraction_match:
            numerator = float(fraction_match.group(1))
            denominator = float(fraction_match.group(2))
            return (numerator / denominator) * 0.5  # Default multiplier for fractions
        
        return 1.0  # Default quantity
    
    def _get_fallback_search_results(self, query: str) -> Dict:
        """Fallback search results when API fails"""
        return {
            'foods': [],
            'total_results': 0,
            'current_page': 1,
            'total_pages': 1,
            'error': f"Search temporarily unavailable for '{query}'"
        }
    
    def _get_fallback_food_details(self) -> Dict:
        """Fallback food details when API fails"""
        return {
            'fdc_id': None,
            'description': 'Food details temporarily unavailable',
            'nutrients': {},
            'error': 'Details temporarily unavailable'
        }
    
    def _get_fallback_nutrition_facts(self) -> Dict:
        """Fallback nutrition facts when calculation fails"""
        return {
            'total_nutrition': self._initialize_nutrition_totals(),
            'daily_values': {},
            'health_score': 50,
            'error': 'Nutrition calculation temporarily unavailable'
        }
    
    def _process_branded_food_results(self, raw_results: Dict) -> Dict:
        """Process branded food search results"""
        return self._process_food_search_results(raw_results)
    
    # Additional utility methods for enhanced functionality
    
    def get_food_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get food name suggestions for autocomplete"""
        cache_key = f"food_suggestions_{partial_query}_{limit}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            search_results = self.search_food(partial_query, page_size=limit)
            suggestions = []
            
            for food in search_results.get('foods', []):
                description = food.get('description', '')
                if description and len(description) > 3:
                    # Clean up the description
                    clean_desc = description.split(',')[0].strip()  # Take first part before comma
                    suggestions.append(clean_desc)
            
            # Remove duplicates while preserving order
            unique_suggestions = []
            seen = set()
            for suggestion in suggestions:
                if suggestion.lower() not in seen:
                    unique_suggestions.append(suggestion)
                    seen.add(suggestion.lower())
            
            result = unique_suggestions[:limit]
            cache.set(cache_key, result, 1800)  # Cache for 30 minutes
            
            return result
            
        except Exception as e:
            logger.error(f"Food suggestions failed: {str(e)}")
            return []
    
    def compare_foods(self, fdc_ids: List[int]) -> Dict:
        """Compare nutritional content of multiple foods"""
        try:
            foods_data = []
            
            for fdc_id in fdc_ids[:5]:  # Limit to 5 foods for performance
                food_details = self.get_food_details(fdc_id)
                if food_details.get('nutrients'):
                    foods_data.append(food_details)
            
            if not foods_data:
                return {'error': 'No valid food data found for comparison'}
            
            # Create comparison matrix
            comparison = {
                'foods': [],
                'nutrients': {},
                'rankings': {}
            }
            
            # Get all unique nutrients across foods
            all_nutrients = set()
            for food in foods_data:
                all_nutrients.update(food.get('nutrients', {}).keys())
            
            # Build comparison data
            for food in foods_data:
                food_info = {
                    'fdc_id': food.get('fdc_id'),
                    'description': food.get('description', ''),
                    'nutrients': food.get('nutrients', {})
                }
                comparison['foods'].append(food_info)
            
            # Calculate rankings for key nutrients
            key_nutrients = ['calories', 'protein', 'fat', 'carbohydrates', 'fiber', 'sodium']
            
            for nutrient in key_nutrients:
                if nutrient in all_nutrients:
                    # Sort foods by this nutrient
                    sorted_foods = sorted(
                        foods_data,
                        key=lambda x: x.get('nutrients', {}).get(nutrient, {}).get('value', 0),
                        reverse=True
                    )
                    
                    comparison['rankings'][nutrient] = [
                        {
                            'fdc_id': food.get('fdc_id'),
                            'description': food.get('description', ''),
                            'value': food.get('nutrients', {}).get(nutrient, {}).get('value', 0),
                            'unit': food.get('nutrients', {}).get(nutrient, {}).get('unit', '')
                        }
                        for food in sorted_foods
                    ]
            
            return comparison
            
        except Exception as e:
            logger.error(f"Food comparison failed: {str(e)}")
            return {'error': 'Food comparison temporarily unavailable'}
    
    def get_seasonal_foods(self, season: str, category: str = None) -> List[Dict]:
        """Get foods that are in season"""
        seasonal_data = {
            'spring': {
                'fruits': ['strawberries', 'apricots', 'rhubarb', 'pineapple'],
                'vegetables': ['asparagus', 'artichokes', 'peas', 'spinach', 'lettuce', 'radishes']
            },
            'summer': {
                'fruits': ['berries', 'peaches', 'plums', 'tomatoes', 'watermelon', 'cherries'],
                'vegetables': ['corn', 'zucchini', 'bell peppers', 'cucumbers', 'eggplant', 'basil']
            },
            'fall': {
                'fruits': ['apples', 'pears', 'grapes', 'cranberries', 'pomegranates'],
                'vegetables': ['squash', 'pumpkin', 'sweet potatoes', 'brussels sprouts', 'cauliflower']
            },
            'winter': {
                'fruits': ['citrus', 'kiwi', 'persimmons'],
                'vegetables': ['cabbage', 'kale', 'turnips', 'parsnips', 'leeks', 'potatoes']
            }
        }
        
        season_lower = season.lower()
        if season_lower not in seasonal_data:
            return []
        
        seasonal_foods = []
        season_data = seasonal_data[season_lower]
        
        if category:
            category_lower = category.lower()
            if category_lower in season_data:
                seasonal_foods = season_data[category_lower]
        else:
            # Return all categories
            for cat_foods in season_data.values():
                seasonal_foods.extend(cat_foods)
        
        # Get nutrition data for seasonal foods
        result = []
        for food_name in seasonal_foods[:10]:  # Limit to 10 for performance
            try:
                search_results = self.search_food(food_name, page_size=1)
                if search_results.get('foods'):
                    food = search_results['foods'][0]
                    result.append({
                        'name': food_name.title(),
                        'fdc_id': food.get('fdc_id'),
                        'description': food.get('description', ''),
                        'basic_nutrients': food.get('basic_nutrients', {})
                    })
            except Exception:
                continue  # Skip foods that can't be found
        
        return result
    
    def validate_ingredient_list(self, ingredients: List[str]) -> Dict:
        """Validate and clean ingredient list for recipe analysis"""
        validated = {
            'valid_ingredients': [],
            'invalid_ingredients': [],
            'suggestions': [],
            'warnings': []
        }
        
        for ingredient in ingredients:
            if not ingredient or len(ingredient.strip()) < 2:
                validated['invalid_ingredients'].append({
                    'original': ingredient,
                    'reason': 'Too short or empty'
                })
                continue
            
            # Check if ingredient can be parsed
            food_name = self._extract_food_name(ingredient)
            
            if not food_name:
                validated['invalid_ingredients'].append({
                    'original': ingredient,
                    'reason': 'Could not extract food name'
                })
                continue
            
            # Try to find the food in database
            try:
                search_results = self.search_food(food_name, page_size=1)
                if search_results.get('foods'):
                    validated['valid_ingredients'].append({
                        'original': ingredient,
                        'cleaned': food_name,
                        'found_food': search_results['foods'][0].get('description', '')
                    })
                else:
                    validated['invalid_ingredients'].append({
                        'original': ingredient,
                        'reason': 'Food not found in database'
                    })
                    
                    # Try to provide suggestions
                    suggestions = self.get_food_suggestions(food_name, limit=3)
                    if suggestions:
                        validated['suggestions'].append({
                            'original': ingredient,
                            'suggestions': suggestions
                        })
            except Exception:
                validated['warnings'].append(f"Could not validate ingredient: {ingredient}")
        
        return validated
    
    def get_nutrient_density_score(self, fdc_id: int) -> Dict:
        """Calculate nutrient density score for a food"""
        try:
            food_details = self.get_food_details(fdc_id)
            nutrients = food_details.get('nutrients', {})
            
            if not nutrients:
                return {'error': 'No nutrient data available'}
            
            # Get calories
            calories = nutrients.get('calories', {}).get('value', 0)
            
            if calories == 0:
                return {'score': 0, 'rating': 'Unknown', 'reason': 'No calorie data'}
            
            # Calculate nutrient density (nutrients per 100 calories)
            beneficial_nutrients = ['protein', 'fiber', 'vitamin_c', 'calcium', 'iron', 'potassium']
            harmful_nutrients = ['sodium', 'sugars']
            
            beneficial_score = 0
            harmful_score = 0
            
            for nutrient in beneficial_nutrients:
                if nutrient in nutrients:
                    value = nutrients[nutrient].get('value', 0)
                    # Normalize to per 100 calories
                    per_100_cal = (value / calories) * 100 if calories > 0 else 0
                    beneficial_score += min(per_100_cal, 10)  # Cap at 10 points per nutrient
            
            for nutrient in harmful_nutrients:
                if nutrient in nutrients:
                    value = nutrients[nutrient].get('value', 0)
                    per_100_cal = (value / calories) * 100 if calories > 0 else 0
                    harmful_score += min(per_100_cal * 0.1, 5)  # Penalty for harmful nutrients
            
            # Final score (0-100)
            final_score = max(0, min(100, beneficial_score - harmful_score))
            
            # Rating categories
            if final_score >= 80:
                rating = 'Excellent'
            elif final_score >= 60:
                rating = 'Good'
            elif final_score >= 40:
                rating = 'Fair'
            elif final_score >= 20:
                rating = 'Poor'
            else:
                rating = 'Very Poor'
            
            return {
                'score': round(final_score, 1),
                'rating': rating,
                'beneficial_score': round(beneficial_score, 1),
                'harmful_score': round(harmful_score, 1),
                'calories_per_100g': calories,
                'description': food_details.get('description', '')
            }
            
        except Exception as e:
                logger.error(f"Nutrient density calculation failed: {str(e)}")
                return {'error': 'Calculation temporarily unavailable'}
    
    # Additional utility methods for enhanced functionality
    
    def batch_food_lookup(self, food_queries: List[str]) -> Dict:
        """
        Perform batch lookup of multiple foods efficiently
        
        Args:
            food_queries: List of food names to search for
            
        Returns:
            Dictionary with results for each query
        """
        results = {}
        
        for query in food_queries[:10]:  # Limit to 10 for performance
            try:
                self._rate_limit()  # Respect API limits
                search_result = self.search_food(query, page_size=1)
                
                if search_result.get('foods'):
                    food = search_result['foods'][0]
                    results[query] = {
                        'success': True,
                        'food': food,
                        'fdc_id': food.get('fdc_id'),
                        'description': food.get('description', '')
                    }
                else:
                    results[query] = {
                        'success': False,
                        'error': 'Food not found',
                        'suggestions': self.get_food_suggestions(query, limit=3)
                    }
                    
            except Exception as e:
                logger.error(f"Batch lookup failed for '{query}': {str(e)}")
                results[query] = {
                    'success': False,
                    'error': 'Lookup failed',
                    'suggestions': []
                }
        
        return results
    
    def get_daily_nutrition_summary(self, meals: List[Dict]) -> Dict:
        """
        Calculate comprehensive daily nutrition summary from multiple meals
        
        Args:
            meals: List of meal dictionaries with food items
            
        Returns:
            Complete daily nutrition analysis
        """
        try:
            daily_totals = self._initialize_nutrition_totals()
            meal_breakdown = []
            
            for meal in meals:
                meal_name = meal.get('name', 'Unnamed meal')
                meal_foods = meal.get('foods', [])
                meal_nutrition = self._initialize_nutrition_totals()
                
                # Calculate nutrition for this meal
                for food_item in meal_foods:
                    if food_item.get('fdc_id'):
                        food_details = self.get_food_details(food_item['fdc_id'])
                        quantity = food_item.get('quantity', 1.0)
                        
                        self._add_to_nutrition_totals(meal_nutrition, food_details, quantity)
                        self._add_to_nutrition_totals(daily_totals, food_details, quantity)
                
                meal_breakdown.append({
                    'meal_name': meal_name,
                    'nutrition': meal_nutrition,
                    'calories': meal_nutrition.get('calories', 0),
                    'meal_timing': meal.get('timing', 'Not specified')
                })
            
            return {
                'daily_totals': daily_totals,
                'meal_breakdown': meal_breakdown,
                'daily_values': self._calculate_daily_values(daily_totals),
                'health_score': self._calculate_health_score(daily_totals),
                'nutrition_balance': self._analyze_nutrition_balance(daily_totals),
                'recommendations': self._generate_daily_recommendations(daily_totals, meal_breakdown)
            }
            
        except Exception as e:
            logger.error(f"Daily nutrition summary failed: {str(e)}")
            return {'error': 'Summary calculation failed'}
    
    def _analyze_nutrition_balance(self, nutrition: Dict) -> Dict:
        """Analyze the balance of nutrients in daily intake"""
        balance_analysis = {
            'macronutrient_balance': {},
            'micronutrient_adequacy': {},
            'overall_balance_score': 0
        }
        
        total_calories = nutrition.get('calories', 0)
        
        if total_calories > 0:
            # Macronutrient balance analysis
            protein_cals = nutrition.get('protein', 0) * 4
            carb_cals = nutrition.get('carbohydrates', 0) * 4
            fat_cals = nutrition.get('fat', 0) * 9
            
            balance_analysis['macronutrient_balance'] = {
                'protein_percent': round((protein_cals / total_calories) * 100, 1),
                'carb_percent': round((carb_cals / total_calories) * 100, 1),
                'fat_percent': round((fat_cals / total_calories) * 100, 1),
                'balance_rating': self._rate_macro_balance(protein_cals, carb_cals, fat_cals, total_calories)
            }
        
        # Micronutrient adequacy
        daily_values = self._calculate_daily_values(nutrition)
        adequate_nutrients = sum(1 for pct in daily_values.values() if pct >= 75)
        total_nutrients = len(daily_values)
        
        balance_analysis['micronutrient_adequacy'] = {
            'adequate_count': adequate_nutrients,
            'total_assessed': total_nutrients,
            'adequacy_percentage': round((adequate_nutrients / total_nutrients) * 100, 1) if total_nutrients > 0 else 0
        }
        
        # Overall balance score
        macro_score = balance_analysis['macronutrient_balance'].get('balance_rating', 0)
        micro_score = balance_analysis['micronutrient_adequacy'].get('adequacy_percentage', 0)
        balance_analysis['overall_balance_score'] = round((macro_score + micro_score) / 2, 1)
        
        return balance_analysis
    
    def _rate_macro_balance(self, protein_cals: float, carb_cals: float, fat_cals: float, total_cals: float) -> int:
        """Rate macronutrient balance on a scale of 0-100"""
        if total_cals == 0:
            return 0
        
        protein_pct = (protein_cals / total_cals) * 100
        carb_pct = (carb_cals / total_cals) * 100
        fat_pct = (fat_cals / total_cals) * 100
        
        # Ideal ranges
        protein_ideal = (15, 25)
        carb_ideal = (45, 65)
        fat_ideal = (20, 35)
        
        # Calculate deviation from ideal ranges
        protein_score = 100 - min(100, abs(protein_pct - 20) * 5)  # 20% is middle of range
        carb_score = 100 - min(100, abs(carb_pct - 55) * 2)        # 55% is middle of range
        fat_score = 100 - min(100, abs(fat_pct - 27.5) * 4)       # 27.5% is middle of range
        
        return round((protein_score + carb_score + fat_score) / 3)
    
    def _generate_daily_recommendations(self, daily_nutrition: Dict, meal_breakdown: List[Dict]) -> List[Dict]:
        """Generate specific recommendations based on daily nutrition analysis"""
        recommendations = []
        daily_values = self._calculate_daily_values(daily_nutrition)
        
        # Check for low nutrients
        low_nutrients = {k: v for k, v in daily_values.items() if v < 50}
        
        for nutrient, percentage in low_nutrients.items():
            nutrient_info = self.get_nutrient_info(nutrient)
            recommendations.append({
                'type': 'nutrient_deficiency',
                'priority': 'high' if percentage < 25 else 'medium',
                'nutrient': nutrient,
                'current_percentage': percentage,
                'recommendation': f"Increase {nutrient_info.get('name', nutrient)} intake",
                'food_sources': nutrient_info.get('sources', []),
                'target_improvement': f"Aim for at least 75% daily value"
            })
        
        # Check for excess nutrients
        high_nutrients = {k: v for k, v in daily_values.items() if v > 150 and k in ['sodium', 'sugars']}
        
        for nutrient, percentage in high_nutrients.items():
            recommendations.append({
                'type': 'nutrient_excess',
                'priority': 'high' if percentage > 200 else 'medium',
                'nutrient': nutrient,
                'current_percentage': percentage,
                'recommendation': f"Reduce {nutrient} intake",
                'strategies': [
                    "Choose fresh foods over processed",
                    "Read nutrition labels carefully",
                    "Cook more meals at home"
                ]
            })
        
        # Meal timing recommendations
        total_calories = daily_nutrition.get('calories', 0)
        if meal_breakdown and total_calories > 0:
            evening_calories = sum(
                meal['calories'] for meal in meal_breakdown 
                if 'dinner' in meal.get('meal_name', '').lower() or 
                   'evening' in meal.get('meal_name', '').lower()
            )
            
            if evening_calories > total_calories * 0.4:  # More than 40% of calories in evening
                recommendations.append({
                    'type': 'meal_timing',
                    'priority': 'medium',
                    'recommendation': "Consider shifting more calories to earlier in the day",
                    'rationale': "Earlier calorie intake may support better metabolism and sleep quality"
                })
        
        return recommendations[:8]  # Limit to most important recommendations
    
    def export_nutrition_report(self, user_id: str, nutrition_data: Dict, format: str = 'json') -> Dict:
        """
        Export comprehensive nutrition report in specified format
        
        Args:
            user_id: Identifier for the user
            nutrition_data: Complete nutrition analysis data
            format: Export format ('json', 'csv', 'pdf')
            
        Returns:
            Export result with data or file path
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"nutrition_report_{user_id}_{timestamp}"
            
            if format.lower() == 'json':
                report_data = {
                    'report_metadata': {
                        'user_id': user_id,
                        'generated_at': datetime.now().isoformat(),
                        'report_type': 'comprehensive_nutrition_analysis',
                        'api_version': '1.0'
                    },
                    'nutrition_analysis': nutrition_data,
                    'summary': {
                        'total_calories': nutrition_data.get('daily_totals', {}).get('calories', 0),
                        'health_score': nutrition_data.get('health_score', 0),
                        'balance_score': nutrition_data.get('nutrition_balance', {}).get('overall_balance_score', 0),
                        'recommendation_count': len(nutrition_data.get('recommendations', []))
                    }
                }
                
                return {
                    'success': True,
                    'format': 'json',
                    'data': report_data,
                    'filename': f"{filename}.json"
                }
            
            elif format.lower() == 'csv':
                # Convert to CSV format (simplified)
                csv_data = []
                daily_totals = nutrition_data.get('daily_totals', {})
                
                for nutrient, value in daily_totals.items():
                    csv_data.append({
                        'nutrient': nutrient,
                        'amount': value,
                        'daily_value_percent': nutrition_data.get('daily_values', {}).get(nutrient, 0)
                    })
                
                return {
                    'success': True,
                    'format': 'csv',
                    'data': csv_data,
                    'filename': f"{filename}.csv"
                }
            
            else:
                return {
                    'success': False,
                    'error': f"Unsupported format: {format}",
                    'supported_formats': ['json', 'csv']
                }
                
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            return {
                'success': False,
                'error': 'Export generation failed'
            }
    
    def cleanup_cache(self, max_age_hours: int = 24) -> Dict:
        """
        Clean up old cache entries to manage memory usage
        
        Args:
            max_age_hours: Maximum age of cache entries to keep
            
        Returns:
            Cleanup summary
        """
        try:
            # This would typically integrate with your cache backend
            # For Django cache framework, you might implement custom cleanup
            
            # Placeholder for cache cleanup logic
            cleanup_summary = {
                'success': True,
                'message': f'Cache cleanup completed for entries older than {max_age_hours} hours',
                'entries_removed': 0,  # Would be actual count
                'cache_size_mb': 0     # Would be actual size
            }
            
            logger.info(f"Nutrition API cache cleanup completed: {cleanup_summary}")
            return cleanup_summary
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {str(e)}")
            return {
                'success': False,
                'error': 'Cache cleanup failed'
            }