# backend/core/ai_client.py

import json
import requests
import logging
from typing import Dict, List, Optional, Generator
from django.conf import settings
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)

class AIClient:
    """
    Unified AI client for different providers (DeepSeek, LocalAI, HuggingFace)
    Handles meal planning, workout generation, and chat responses
    """
    
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.api_key = settings.AI_API_KEY
        self.base_url = settings.AI_BASE_URL
        self.prompts = PromptTemplates()
        
    def generate_meal_plan(self, user_profile: Dict) -> Dict:
        """
        Generate AI-powered meal plan based on user profile
        
        Args:
            user_profile: Dictionary containing user's health data and preferences
            
        Returns:
            Dictionary containing structured meal plan
        """
        try:
            prompt = self.prompts.get_meal_plan_prompt(user_profile)
            response = self._call_ai_api(prompt, max_tokens=2000)
            
            # Parse JSON response
            meal_plan = self._parse_json_response(response)
            
            # Validate meal plan structure
            if self._validate_meal_plan(meal_plan):
                return meal_plan
            else:
                return self._get_fallback_meal_plan(user_profile)
                
        except Exception as e:
            logger.error(f"Meal plan generation failed: {str(e)}")
            return self._get_fallback_meal_plan(user_profile)
    
    def generate_workout_plan(self, user_profile: Dict) -> Dict:
        """
        Generate AI-powered workout plan based on user profile
        
        Args:
            user_profile: Dictionary containing user's fitness data and preferences
            
        Returns:
            Dictionary containing structured workout plan
        """
        try:
            prompt = self.prompts.get_workout_prompt(user_profile)
            response = self._call_ai_api(prompt, max_tokens=1500)
            
            # Parse JSON response
            workout_plan = self._parse_json_response(response)
            
            # Validate workout plan structure
            if self._validate_workout_plan(workout_plan):
                return workout_plan
            else:
                return self._get_fallback_workout_plan(user_profile)
                
        except Exception as e:
            logger.error(f"Workout plan generation failed: {str(e)}")
            return self._get_fallback_workout_plan(user_profile)
    
    def chat_response(self, message: str, context: Dict) -> Generator[str, None, None]:
        """
        Generate streaming AI chat response
        
        Args:
            message: User's chat message
            context: Chat context including user profile and conversation history
            
        Yields:
            String chunks of the AI response
        """
        try:
            prompt = self.prompts.get_chat_prompt(message, context)
            
            # Stream response
            for chunk in self._call_ai_api_stream(prompt):
                yield chunk
                
        except Exception as e:
            logger.error(f"Chat response generation failed: {str(e)}")
            yield "I apologize, but I'm having trouble responding right now. Please try again later."
    
    def analyze_nutrition(self, food_data: List[Dict]) -> Dict:
        """
        Analyze nutrition data and provide AI insights
        
        Args:
            food_data: List of food items with nutritional information
            
        Returns:
            Dictionary containing nutrition analysis and recommendations
        """
        try:
            prompt = self.prompts.get_nutrition_analysis_prompt(food_data)
            response = self._call_ai_api(prompt, max_tokens=1000)
            
            return {
                'analysis': response,
                'recommendations': self._extract_recommendations(response),
                'insights': self._extract_insights(response)
            }
            
        except Exception as e:
            logger.error(f"Nutrition analysis failed: {str(e)}")
            return {'analysis': 'Analysis unavailable', 'recommendations': [], 'insights': []}
    
    def _call_ai_api(self, prompt: str, max_tokens: int = 1000) -> str:
        """Make API call to configured AI provider"""
        
        if self.provider == 'deepseek':
            return self._call_deepseek(prompt, max_tokens)
        elif self.provider == 'localai':
            return self._call_localai(prompt, max_tokens)
        elif self.provider == 'huggingface':
            return self._call_huggingface(prompt, max_tokens)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
    
    def _call_ai_api_stream(self, prompt: str) -> Generator[str, None, None]:
        """Make streaming API call to configured AI provider"""
        
        if self.provider == 'deepseek':
            yield from self._call_deepseek_stream(prompt)
        elif self.provider == 'localai':
            yield from self._call_localai_stream(prompt)
        else:
            # Fallback to non-streaming for unsupported providers
            response = self._call_ai_api(prompt)
            for word in response.split():
                yield word + " "
    
    def _call_deepseek(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call DeepSeek API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': 0.7
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _call_deepseek_stream(self, prompt: str) -> Generator[str, None, None]:
        """Call DeepSeek API with streaming"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'stream': True,
            'temperature': 0.7
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            stream=True,
            timeout=30
        )
        
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data != '[DONE]':
                        try:
                            chunk = json.loads(data)
                            content = chunk['choices'][0]['delta'].get('content', '')
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
    
    def _call_localai(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call LocalAI API"""
        headers = {'Content-Type': 'application/json'}
        
        data = {
            'model': 'ggml-gpt4all-j-v1.3-groovy',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': 0.7
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _call_localai_stream(self, prompt: str) -> Generator[str, None, None]:
        """Call LocalAI with streaming (similar to DeepSeek)"""
        # Implementation similar to DeepSeek streaming
        headers = {'Content-Type': 'application/json'}
        
        data = {
            'model': 'ggml-gpt4all-j-v1.3-groovy',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'stream': True,
            'temperature': 0.7
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            stream=True,
            timeout=30
        )
        
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data != '[DONE]':
                        try:
                            chunk = json.loads(data)
                            content = chunk['choices'][0]['delta'].get('content', '')
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
    
    def _call_huggingface(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call HuggingFace API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'inputs': prompt,
            'parameters': {
                'max_new_tokens': max_tokens,
                'temperature': 0.7,
                'do_sample': True
            }
        }
        
        response = requests.post(
            f"https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
            headers=headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        return result[0]['generated_text']
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON response from AI, handling potential formatting issues"""
        try:
            # Try to parse as JSON directly
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try to find JSON object in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            raise ValueError("No valid JSON found in response")
    
    def _validate_meal_plan(self, meal_plan: Dict) -> bool:
        """Validate meal plan structure"""
        required_keys = ['daily_calories', 'days']
        return all(key in meal_plan for key in required_keys)
    
    def _validate_workout_plan(self, workout_plan: Dict) -> bool:
        """Validate workout plan structure"""
        required_keys = ['plan_name', 'days']
        return all(key in workout_plan for key in required_keys)
    
    def _get_fallback_meal_plan(self, user_profile: Dict) -> Dict:
        """Generate fallback meal plan if AI fails"""
        return {
            'daily_calories': 1800,
            'days': [
                {
                    'day': 'Monday',
                    'meals': {
                        'breakfast': {
                            'name': 'Oatmeal with berries',
                            'calories': 350,
                            'ingredients': ['1 cup oatmeal', '1/2 cup mixed berries', '1 tbsp honey']
                        },
                        'lunch': {
                            'name': 'Grilled chicken salad',
                            'calories': 450,
                            'ingredients': ['4oz grilled chicken', '2 cups mixed greens', '1 tbsp olive oil']
                        },
                        'dinner': {
                            'name': 'Baked salmon with vegetables',
                            'calories': 500,
                            'ingredients': ['5oz salmon fillet', '1 cup broccoli', '1/2 cup brown rice']
                        },
                        'snack': {
                            'name': 'Greek yogurt with almonds',
                            'calories': 200,
                            'ingredients': ['1 cup Greek yogurt', '1oz almonds']
                        }
                    }
                }
            ]
        }
    
    def _get_fallback_workout_plan(self, user_profile: Dict) -> Dict:
        """Generate fallback workout plan if AI fails"""
        return {
            'plan_name': 'Basic Fitness Plan',
            'days': [
                {
                    'day': 'Monday',
                    'type': 'Upper Body',
                    'duration': '30 minutes',
                    'exercises': [
                        {'name': 'Push-ups', 'sets': 3, 'reps': 10},
                        {'name': 'Plank', 'sets': 3, 'duration': '30 seconds'}
                    ]
                }
            ]
        }
    
    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Extract recommendations from nutrition analysis"""
        # Simple keyword-based extraction
        recommendations = []
        lines = analysis.split('\n')
        for line in lines:
            if 'recommend' in line.lower() or 'suggest' in line.lower():
                recommendations.append(line.strip())
        return recommendations[:5]  # Limit to top 5
    
    def _extract_insights(self, analysis: str) -> List[str]:
        """Extract insights from nutrition analysis"""
        # Simple keyword-based extraction
        insights = []
        lines = analysis.split('\n')
        for line in lines:
            if any(word in line.lower() for word in ['high', 'low', 'deficient', 'excess']):
                insights.append(line.strip())
        return insights[:5]  # Limit to top 5