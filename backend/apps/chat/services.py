# backend/apps/chat/services.py

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Generator, Tuple
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Avg, Sum, Count
from django.utils import timezone

from core.ai_client import AIClient
from apps.users.models import UserProfile
from apps.nutrition.models import MealPlan, NutritionLog
from apps.fitness.models import WorkoutPlan, Workout
from .models import (
    ChatSession, Message, ChatContext, ChatTemplate,
    ConversationSummary, ChatAnalytics
)

logger = logging.getLogger(__name__)


class ChatService:
    """Main service for chat functionality"""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.context_service = ChatContextService()
        self.analytics_service = ChatAnalyticsService()
    
    def start_chat_session(self, user: User, initial_data: Dict) -> Dict:
        """Start a new chat session"""
        try:
            # Create chat session
            session = ChatSession.objects.create(
                user=user,
                chat_type=initial_data.get('chat_type', 'general'),
                context_data=initial_data.get('context', {}),
                session_goals=initial_data.get('goals', [])
            )
            
            # Initialize session context
            self.context_service.initialize_session_context(session, user)
            
            # Create initial user message
            user_message = Message.objects.create(
                session=session,
                role='user',
                content=initial_data['message'],
                message_type='text'
            )
            
            # Generate AI response
            ai_response = self.generate_ai_response(session, user_message)
            
            # Generate session title if needed
            session.generate_title()
            
            return {
                'success': True,
                'session_id': str(session.id),
                'initial_response': ai_response,
                'session_title': session.title
            }
            
        except Exception as e:
            logger.error(f"Error starting chat session: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_message(self, session_id: str, user: User, message_data: Dict) -> Dict:
        """Send a message in an existing chat session"""
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            
            # Create user message
            user_message = Message.objects.create(
                session=session,
                role='user',
                content=message_data['message'],
                message_type=message_data.get('message_type', 'text'),
                context_data=message_data.get('context', {}),
                parent_message_id=message_data.get('parent_message_id')
            )
            
            # Update session activity
            session.update_activity()
            session.message_count += 1
            session.save(update_fields=['message_count'])
            
            # Generate AI response
            ai_response = self.generate_ai_response(session, user_message)
            
            # Update context based on conversation
            self.context_service.update_context_from_message(session, user_message, ai_response)
            
            return {
                'success': True,
                'user_message_id': str(user_message.id),
                'ai_response': ai_response
            }
            
        except ChatSession.DoesNotExist:
            return {
                'success': False,
                'error': 'Chat session not found'
            }
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_ai_response(self, session: ChatSession, user_message: Message) -> Dict:
        """Generate AI response for a user message"""
        try:
            start_time = timezone.now()
            
            # Build conversation context
            context = self._build_conversation_context(session, user_message)
            
            # Generate response using AI client
            ai_response_data = self.ai_client.chat_response(
                message=user_message.content,
                context=context
            )
            
            # Calculate response time
            response_time = (timezone.now() - start_time).total_seconds() * 1000
            
            # Create AI message
            ai_message = Message.objects.create(
                session=session,
                role='assistant',
                content=ai_response_data.get('content', ''),
                message_type=self._determine_response_type(ai_response_data),
                ai_model=ai_response_data.get('model', 'unknown'),
                prompt_tokens=ai_response_data.get('prompt_tokens', 0),
                completion_tokens=ai_response_data.get('completion_tokens', 0),
                total_tokens=ai_response_data.get('total_tokens', 0),
                confidence_score=ai_response_data.get('confidence_score'),
                response_time_ms=int(response_time),
                structured_data=ai_response_data.get('structured_data', {}),
                context_data=context,
                parent_message=user_message
            )
            
            # Update session analytics
            session.total_tokens_used += ai_message.total_tokens
            session.avg_response_time = (
                (session.avg_response_time * (session.message_count - 1) + response_time) / 
                session.message_count
            )
            session.save(update_fields=['total_tokens_used', 'avg_response_time'])
            
            # Track analytics
            self.analytics_service.track_response_generated(session, ai_message)
            
            return {
                'message_id': str(ai_message.id),
                'content': ai_message.content,
                'message_type': ai_message.message_type,
                'structured_data': ai_message.structured_data,
                'confidence_score': ai_message.confidence_score,
                'response_time_ms': ai_message.response_time_ms,
                'created_at': ai_message.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            # Create error message
            error_message = Message.objects.create(
                session=session,
                role='assistant',
                content="I apologize, but I'm having trouble processing your request right now. Please try again.",
                message_type='error',
                parent_message=user_message
            )
            
            return {
                'message_id': str(error_message.id),
                'content': error_message.content,
                'message_type': 'error',
                'error': str(e)
            }
    
    def stream_ai_response(self, session_id: str, user: User, message_data: Dict) -> Generator[Dict, None, None]:
        """Stream AI response in real-time"""
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            
            # Create user message
            user_message = Message.objects.create(
                session=session,
                role='user',
                content=message_data['message'],
                message_type=message_data.get('message_type', 'text'),
                context_data=message_data.get('context', {})
            )
            
            # Build context
            context = self._build_conversation_context(session, user_message)
            
            # Create placeholder AI message
            ai_message = Message.objects.create(
                session=session,
                role='assistant',
                content='',
                message_type='text',
                parent_message=user_message
            )
            
            # Stream response
            full_content = ''
            start_time = timezone.now()
            
            for chunk in self.ai_client.stream_chat_response(user_message.content, context):
                content_chunk = chunk.get('content', '')
                full_content += content_chunk
                
                yield {
                    'session_id': str(session.id),
                    'message_id': str(ai_message.id),
                    'content_chunk': content_chunk,
                    'is_complete': chunk.get('is_complete', False),
                    'metadata': chunk.get('metadata', {})
                }
            
            # Update final message
            response_time = (timezone.now() - start_time).total_seconds() * 1000
            ai_message.content = full_content
            ai_message.response_time_ms = int(response_time)
            ai_message.save()
            
            # Update session
            session.update_activity()
            session.message_count += 1
            session.save(update_fields=['message_count'])
            
        except Exception as e:
            logger.error(f"Error streaming AI response: {str(e)}")
            yield {
                'error': str(e),
                'is_complete': True
            }
    
    def _build_conversation_context(self, session: ChatSession, current_message: Message) -> Dict:
        """Build comprehensive context for AI response generation"""
        context = {
            'user_profile': {},
            'session_info': {},
            'conversation_history': [],
            'user_data': {},
            'preferences': {}
        }
        
        try:
            # Get user profile
            user_profile = UserProfile.objects.get(user=session.user)
            context['user_profile'] = {
                'age': user_profile.age,
                'gender': user_profile.gender,
                'health_goals': getattr(user_profile, 'health_goals', []),
                'dietary_restrictions': getattr(user_profile, 'dietary_restrictions', []),
                'activity_level': user_profile.activity_level,
                'fitness_level': getattr(user_profile, 'fitness_level', 'beginner')
            }
        except UserProfile.DoesNotExist:
            pass
        
        # Session information
        context['session_info'] = {
            'chat_type': session.chat_type,
            'session_goals': session.session_goals,
            'message_count': session.message_count
        }
        
        # Recent conversation history
        recent_messages = session.messages.exclude(
            id=current_message.id
        ).order_by('-created_at')[:10]
        
        context['conversation_history'] = [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.created_at.isoformat()
            }
            for msg in reversed(recent_messages)
        ]
        
        # Get relevant context data
        session_context = self.context_service.get_relevant_context(session, current_message)
        context.update(session_context)
        
        return context
    
    def _determine_response_type(self, ai_response_data: Dict) -> str:
        """Determine the type of AI response based on content"""
        content = ai_response_data.get('content', '').lower()
        structured_data = ai_response_data.get('structured_data', {})
        
        if 'meal plan' in content or structured_data.get('type') == 'meal_plan':
            return 'meal_plan'
        elif 'workout' in content or structured_data.get('type') == 'workout_plan':
            return 'workout_plan'
        elif 'nutrition' in content and 'analysis' in content:
            return 'nutrition_analysis'
        elif 'progress' in content or 'tracking' in content:
            return 'progress_update'
        elif 'recommend' in content or 'suggest' in content:
            return 'recommendation'
        else:
            return 'text'
    
    def add_message_feedback(self, message_id: str, user: User, feedback_data: Dict) -> Dict:
        """Add user feedback to a message"""
        try:
            message = Message.objects.get(
                id=message_id,
                session__user=user,
                role='assistant'
            )
            
            message.add_user_feedback(
                rating=feedback_data['rating'],
                feedback=feedback_data.get('feedback', '')
            )
            
            # Update session satisfaction if this is recent
            self._update_session_satisfaction(message.session)
            
            # Track analytics
            self.analytics_service.track_user_feedback(message, feedback_data['rating'])
            
            return {
                'success': True,
                'message': 'Feedback recorded successfully'
            }
            
        except Message.DoesNotExist:
            return {
                'success': False,
                'error': 'Message not found'
            }
        except Exception as e:
            logger.error(f"Error adding message feedback: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_session_satisfaction(self, session: ChatSession):
        """Update session satisfaction based on recent message ratings"""
        recent_ratings = session.messages.filter(
            role='assistant',
            user_rating__isnull=False,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).values_list('user_rating', flat=True)
        
        if recent_ratings:
            avg_rating = sum(recent_ratings) / len(recent_ratings)
            session.satisfaction_rating = round(avg_rating, 1)
            session.save(update_fields=['satisfaction_rating'])


class ChatContextService:
    """Service for managing chat context and memory"""
    
    def initialize_session_context(self, session: ChatSession, user: User):
        """Initialize context for a new chat session"""
        try:
            # Add user profile context
            self._add_user_profile_context(session, user)
            
            # Add recent activity context
            self._add_recent_activity_context(session, user)
            
            # Add preferences context
            self._add_user_preferences_context(session, user)
            
        except Exception as e:
            logger.error(f"Error initializing session context: {str(e)}")
    
    def _add_user_profile_context(self, session: ChatSession, user: User):
        """Add user profile information to context"""
        try:
            user_profile = UserProfile.objects.get(user=user)
            
            ChatContext.objects.create(
                session=session,
                context_type='user_profile',
                key='basic_info',
                value={
                    'age': user_profile.age,
                    'gender': user_profile.gender,
                    'height': user_profile.height_cm,
                    'weight': user_profile.weight_kg,
                    'activity_level': user_profile.activity_level
                },
                importance_score=0.9
            )
            
            # Add health goals if available
            health_goals = getattr(user_profile, 'health_goals', [])
            if health_goals:
                ChatContext.objects.create(
                    session=session,
                    context_type='user_profile',
                    key='health_goals',
                    value=health_goals,
                    importance_score=0.8
                )
                
        except UserProfile.DoesNotExist:
            pass
    
    def _add_recent_activity_context(self, session: ChatSession, user: User):
        """Add recent user activity to context"""
        # Recent meal plans
        recent_meal_plan = MealPlan.objects.filter(
            user=user,
            status='active'
        ).first()
        
        if recent_meal_plan:
            ChatContext.objects.create(
                session=session,
                context_type='meal_history',
                key='active_meal_plan',
                value={
                    'id': str(recent_meal_plan.id),
                    'name': recent_meal_plan.name,
                    'created_at': recent_meal_plan.created_at.isoformat(),
                    'daily_calories': recent_meal_plan.daily_calories
                },
                importance_score=0.7,
                expires_at=timezone.now() + timedelta(days=30)
            )
        
        # Recent workout plans
        recent_workout_plan = WorkoutPlan.objects.filter(
            user=user,
            status='active'
        ).first()
        
        if recent_workout_plan:
            ChatContext.objects.create(
                session=session,
                context_type='workout_history',
                key='active_workout_plan',
                value={
                    'id': str(recent_workout_plan.id),
                    'name': recent_workout_plan.name,
                    'plan_type': recent_workout_plan.plan_type,
                    'completion_percentage': recent_workout_plan.completion_percentage
                },
                importance_score=0.7,
                expires_at=timezone.now() + timedelta(days=30)
            )
        
        # Recent nutrition logs
        recent_logs = NutritionLog.objects.filter(
            user=user,
            date__gte=timezone.now().date() - timedelta(days=7)
        ).order_by('-date')[:5]
        
        if recent_logs:
            log_data = [
                {
                    'date': log.date.isoformat(),
                    'calories_consumed': log.calories_consumed,
                    'adherence_score': getattr(log, 'adherence_score', 0)
                }
                for log in recent_logs
            ]
            
            ChatContext.objects.create(
                session=session,
                context_type='nutrition_preferences',
                key='recent_nutrition_logs',
                value=log_data,
                importance_score=0.6,
                expires_at=timezone.now() + timedelta(days=7)
            )
    
    def _add_user_preferences_context(self, session: ChatSession, user: User):
        """Add user preferences to context"""
        # Get preferences from previous chat sessions
        recent_sessions = ChatSession.objects.filter(
            user=user,
            status='active'
        ).exclude(id=session.id).order_by('-last_activity')[:3]
        
        preferences = {}
        for prev_session in recent_sessions:
            session_prefs = prev_session.context_data.get('user_preferences', {})
            preferences.update(session_prefs)
        
        if preferences:
            ChatContext.objects.create(
                session=session,
                context_type='nutrition_preferences',
                key='learned_preferences',
                value=preferences,
                importance_score=0.5,
                auto_refresh=True
            )
    
    def update_context_from_message(self, session: ChatSession, user_message: Message, ai_response: Dict):
        """Update session context based on conversation"""
        try:
            # Extract preferences from user message
            self._extract_preferences_from_message(session, user_message)
            
            # Store important conversation memories
            self._store_conversation_memory(session, user_message, ai_response)
            
        except Exception as e:
            logger.error(f"Error updating context from message: {str(e)}")
    
    def _extract_preferences_from_message(self, session: ChatSession, message: Message):
        """Extract user preferences from message content"""
        content = message.content.lower()
        preferences = {}
        
        # Extract dietary preferences
        if 'vegetarian' in content:
            preferences['diet_type'] = 'vegetarian'
        elif 'vegan' in content:
            preferences['diet_type'] = 'vegan'
        elif 'keto' in content:
            preferences['diet_type'] = 'ketogenic'
        
        # Extract activity preferences
        if 'morning workout' in content or 'morning exercise' in content:
            preferences['preferred_workout_time'] = 'morning'
        elif 'evening workout' in content or 'evening exercise' in content:
            preferences['preferred_workout_time'] = 'evening'
        
        # Extract food preferences
        food_likes = []
        food_dislikes = []
        
        if 'love' in content or 'like' in content:
            # Simple extraction - can be enhanced with NLP
            words = content.split()
            for i, word in enumerate(words):
                if word in ['love', 'like', 'enjoy'] and i + 1 < len(words):
                    food_likes.append(words[i + 1])
        
        if 'hate' in content or 'dislike' in content:
            words = content.split()
            for i, word in enumerate(words):
                if word in ['hate', 'dislike', 'avoid'] and i + 1 < len(words):
                    food_dislikes.append(words[i + 1])
        
        if food_likes:
            preferences['food_likes'] = food_likes
        if food_dislikes:
            preferences['food_dislikes'] = food_dislikes
        
        # Store preferences in context
        if preferences:
            existing_context, created = ChatContext.objects.get_or_create(
                session=session,
                context_type='nutrition_preferences',
                key='extracted_preferences',
                defaults={
                    'value': preferences,
                    'importance_score': 0.6
                }
            )
            
            if not created:
                # Merge with existing preferences
                existing_prefs = existing_context.value
                existing_prefs.update(preferences)
                existing_context.value = existing_prefs
                existing_context.save()
    
    def _store_conversation_memory(self, session: ChatSession, user_message: Message, ai_response: Dict):
        """Store important conversation elements as memory"""
        # Store if user mentions specific goals or plans
        content = user_message.content.lower()
        
        if any(goal_word in content for goal_word in ['goal', 'want to', 'trying to', 'plan to']):
            ChatContext.objects.create(
                session=session,
                context_type='conversation_memory',
                key=f'goal_mentioned_{user_message.id}',
                value={
                    'user_message': user_message.content,
                    'timestamp': user_message.created_at.isoformat(),
                    'context': 'goal_setting'
                },
                importance_score=0.8,
                expires_at=timezone.now() + timedelta(days=30)
            )
    
    def get_relevant_context(self, session: ChatSession, current_message: Message) -> Dict:
        """Get relevant context for AI response generation"""
        context_data = {}
        
        # Get high-importance context
        high_importance_context = session.context_items.filter(
            importance_score__gte=0.7
        ).exclude(
            expires_at__lt=timezone.now()
        )
        
        for context_item in high_importance_context:
            context_item.mark_referenced()
            
            if context_item.context_type not in context_data:
                context_data[context_item.context_type] = {}
            
            context_data[context_item.context_type][context_item.key] = context_item.value
        
        return context_data


class ChatAnalyticsService:
    """Service for chat analytics and insights"""
    
    def track_response_generated(self, session: ChatSession, ai_message: Message):
        """Track analytics when AI response is generated"""
        try:
            # Record response time
            ChatAnalytics.objects.create(
                user=session.user,
                session=session,
                metric_type='response_time',
                metric_value=ai_message.response_time_ms,
                metric_unit='milliseconds',
                period_start=ai_message.created_at,
                period_end=ai_message.created_at
            )
            
            # Record token usage
            if ai_message.total_tokens > 0:
                ChatAnalytics.objects.create(
                    user=session.user,
                    session=session,
                    metric_type='tokens_used',
                    metric_value=ai_message.total_tokens,
                    metric_unit='tokens',
                    period_start=ai_message.created_at,
                    period_end=ai_message.created_at
                )
            
        except Exception as e:
            logger.error(f"Error tracking response analytics: {str(e)}")
    
    def track_user_feedback(self, message: Message, rating: int):
        """Track user feedback analytics"""
        try:
            ChatAnalytics.objects.create(
                user=message.session.user,
                session=message.session,
                metric_type='user_satisfaction',
                metric_value=rating,
                metric_unit='rating',
                additional_data={
                    'message_id': str(message.id),
                    'message_type': message.message_type,
                    'ai_model': message.ai_model
                },
                period_start=message.created_at,
                period_end=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Error tracking feedback analytics: {str(e)}")
    
    def generate_user_insights(self, user: User, period_days: int = 30) -> Dict:
        """Generate comprehensive chat insights for user"""
        try:
            start_date = timezone.now() - timedelta(days=period_days)
            
            # Get user's chat sessions
            sessions = ChatSession.objects.filter(
                user=user,
                created_at__gte=start_date
            )
            
            # Get user's messages
            messages = Message.objects.filter(
                session__user=user,
                created_at__gte=start_date
            )
            
            insights = {
                'communication_patterns': self._analyze_communication_patterns(messages),
                'preferred_topics': self._analyze_preferred_topics(sessions),
                'engagement_trends': self._analyze_engagement_trends(sessions),
                'ai_performance': self._analyze_ai_performance(messages),
                'personalization_opportunities': self._identify_personalization_opportunities(user),
                'recommended_features': self._recommend_features(user)
            }
            
            return {
                'success': True,
                'insights': insights,
                'period_days': period_days
            }
            
        except Exception as e:
            logger.error(f"Error generating chat insights: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_communication_patterns(self, messages) -> Dict:
        """Analyze user communication patterns"""
        user_messages = messages.filter(role='user')
        
        # Message frequency by time of day
        hourly_distribution = {}
        for hour in range(24):
            count = user_messages.filter(created_at__hour=hour).count()
            hourly_distribution[f"{hour:02d}:00"] = count
        
        # Average message length
        avg_length = user_messages.aggregate(
            avg_length=Avg(models.Length('content'))
        )['avg_length'] or 0
        
        # Most active days
        daily_counts = {}
        for message in user_messages:
            day = message.created_at.strftime('%A')
            daily_counts[day] = daily_counts.get(day, 0) + 1
        
        return {
            'hourly_distribution': hourly_distribution,
            'average_message_length': round(avg_length, 1),
            'most_active_days': dict(sorted(daily_counts.items(), key=lambda x: x[1], reverse=True)),
            'total_messages': user_messages.count()
        }
    
    def _analyze_preferred_topics(self, sessions) -> List[Dict]:
        """Analyze user's preferred chat topics"""
        topic_counts = sessions.values('chat_type').annotate(
            count=Count('id'),
            avg_satisfaction=Avg('satisfaction_rating')
        ).order_by('-count')
        
        return [
            {
                'topic': item['chat_type'],
                'session_count': item['count'],
                'avg_satisfaction': round(item['avg_satisfaction'] or 0, 1)
            }
            for item in topic_counts
        ]
    
    def _analyze_engagement_trends(self, sessions) -> Dict:
        """Analyze user engagement trends"""
        # Session duration trends
        session_durations = []
        for session in sessions:
            duration = (session.last_activity - session.created_at).total_seconds() / 60
            session_durations.append(duration)
        
        avg_duration = sum(session_durations) / len(session_durations) if session_durations else 0
        
        # Message count trends
        avg_messages = sessions.aggregate(
            avg_messages=Avg('message_count')
        )['avg_messages'] or 0
        
        return {
            'average_session_duration_minutes': round(avg_duration, 1),
            'average_messages_per_session': round(avg_messages, 1),
            'total_sessions': sessions.count(),
            'active_sessions': sessions.filter(status='active').count()
        }
    
    def _analyze_ai_performance(self, messages) -> Dict:
        """Analyze AI performance metrics"""
        ai_messages = messages.filter(role='assistant')
        
        # Average response time
        avg_response_time = ai_messages.aggregate(
            avg_time=Avg('response_time_ms')
        )['avg_time'] or 0
        
        # User satisfaction with AI responses
        rated_messages = ai_messages.filter(user_rating__isnull=False)
        avg_rating = rated_messages.aggregate(
            avg_rating=Avg('user_rating')
        )['avg_rating'] or 0
        
        # Confidence scores
        avg_confidence = ai_messages.filter(
            confidence_score__isnull=False
        ).aggregate(
            avg_confidence=Avg('confidence_score')
        )['avg_confidence'] or 0
        
        return {
            'average_response_time_ms': round(avg_response_time, 1),
            'average_user_rating': round(avg_rating, 1),
            'average_confidence_score': round(avg_confidence, 2),
            'total_ai_responses': ai_messages.count(),
            'rated_responses': rated_messages.count()
        }
    
    def _identify_personalization_opportunities(self, user: User) -> List[Dict]:
        """Identify opportunities for better personalization"""
        opportunities = []
        
        # Check if user profile is incomplete
        try:
            user_profile = UserProfile.objects.get(user=user)
            if not getattr(user_profile, 'dietary_restrictions', None):
                opportunities.append({
                    'type': 'profile_completion',
                    'title': 'Complete Dietary Preferences',
                    'description': 'Adding dietary restrictions will improve meal recommendations',
                    'priority': 'medium'
                })
        except UserProfile.DoesNotExist:
            opportunities.append({
                'type': 'profile_creation',
                'title': 'Create User Profile',
                'description': 'A complete profile enables personalized recommendations',
                'priority': 'high'
            })
        
        # Check for repeated questions
        recent_messages = Message.objects.filter(
            session__user=user,
            role='user',
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        # Simple keyword analysis for repeated topics
        common_keywords = {}
        for message in recent_messages:
            words = message.content.lower().split()
            for word in words:
                if len(word) > 4:  # Only count longer words
                    common_keywords[word] = common_keywords.get(word, 0) + 1
        
        # If user frequently asks about the same topics
        frequent_topics = [word for word, count in common_keywords.items() if count >= 3]
        if frequent_topics:
            opportunities.append({
                'type': 'topic_templates',
                'title': 'Create Quick Templates',
                'description': f'You frequently ask about {", ".join(frequent_topics[:3])}. Create quick templates for faster answers.',
                'priority': 'low'
            })
        
        return opportunities
    
    def _recommend_features(self, user: User) -> List[Dict]:
        """Recommend features based on user behavior"""
        recommendations = []
        
        # Check if user has active meal plans
        has_meal_plan = MealPlan.objects.filter(user=user, status='active').exists()
        if not has_meal_plan:
            recommendations.append({
                'feature': 'meal_planning',
                'title': 'Try AI Meal Planning',
                'description': 'Generate personalized meal plans based on your goals',
                'category': 'nutrition'
            })
        
        # Check if user has workout plans
        has_workout_plan = WorkoutPlan.objects.filter(user=user, status='active').exists()
        if not has_workout_plan:
            recommendations.append({
                'feature': 'workout_planning',
                'title': 'Create Workout Plans',
                'description': 'Get AI-generated workout routines tailored to your fitness level',
                'category': 'fitness'
            })
        
        # Check chat usage patterns
        recent_sessions = ChatSession.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        if recent_sessions >= 5:
            recommendations.append({
                'feature': 'chat_templates',
                'title': 'Save Chat Templates',
                'description': 'Save frequently used questions as templates for quicker access',
                'category': 'productivity'
            })
        
        return recommendations


class ConversationSummaryService:
    """Service for generating and managing conversation summaries"""
    
    def __init__(self):
        self.ai_client = AIClient()
    
    def generate_session_summary(self, session: ChatSession) -> Dict:
        """Generate a summary for a completed chat session"""
        try:
            messages = session.messages.order_by('created_at')
            
            if messages.count() < 3:
                return {'success': False, 'error': 'Session too short to summarize'}
            
            # Build conversation text
            conversation_text = self._build_conversation_text(messages)
            
            # Generate summary using AI
            summary_data = self.ai_client.generate_conversation_summary(
                conversation_text=conversation_text,
                session_type=session.chat_type
            )
            
            # Create summary record
            summary = ConversationSummary.objects.create(
                user=session.user,
                session=session,
                summary_type='session',
                title=summary_data.get('title', f"{session.chat_type.title()} Session Summary"),
                summary_text=summary_data.get('summary', ''),
                key_topics=summary_data.get('key_topics', []),
                action_items=summary_data.get('action_items', []),
                user_preferences_learned=summary_data.get('preferences', {}),
                period_start=session.created_at,
                period_end=session.last_activity,
                confidence_score=summary_data.get('confidence_score', 0.8)
            )
            
            return {
                'success': True,
                'summary_id': str(summary.id),
                'summary': summary_data
            }
            
        except Exception as e:
            logger.error(f"Error generating session summary: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_conversation_text(self, messages) -> str:
        """Build formatted conversation text for summarization"""
        conversation_lines = []
        
        for message in messages:
            role_label = "User" if message.role == 'user' else "Assistant"
            conversation_lines.append(f"{role_label}: {message.content}")
        
        return "\n\n".join(conversation_lines)