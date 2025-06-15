# backend/apps/fitness/services.py

import json
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Avg, Sum, Count
from django.utils import timezone

from core.ai_client import AIClient
from apps.users.models import UserProfile
from .models import (
    Exercise, WorkoutTemplate, WorkoutPlan, Workout,
    WorkoutExercise, FitnessGoal, FitnessMetric
)

logger = logging.getLogger(__name__)


class WorkoutPlanningService:
    """Service for AI-powered workout plan generation"""
    
    def __init__(self):
        self.ai_client = AIClient()
    
    def generate_personalized_workout_plan(self, user: User, generation_params: Dict) -> Dict:
        """Generate a personalized workout plan using AI"""
        try:
            # Get user profile for personalization
            user_profile = UserProfile.objects.get(user=user)
            
            # Build AI prompt with user data and preferences
            prompt = self._build_workout_plan_prompt(user_profile, generation_params)
            
            # Generate plan using AI
            ai_response = self.ai_client.generate_workout_plan(prompt)
            
            # Parse and validate AI response
            parsed_plan = self._parse_ai_workout_plan(ai_response)
            
            # Save plan to database
            workout_plan = self._save_workout_plan_to_db(user, generation_params, parsed_plan)
            
            return {
                'success': True,
                'workout_plan_id': workout_plan.id,
                'plan_data': parsed_plan,
                'ai_confidence': parsed_plan.get('confidence_score', 0.8)
            }
            
        except Exception as e:
            logger.error(f"Workout plan generation failed for user {user.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fallback_plan': self._generate_fallback_plan(user, generation_params)
            }
    
    def _build_workout_plan_prompt(self, user_profile: UserProfile, params: Dict) -> str:
        """Build AI prompt for workout plan generation"""
        from core.prompts import PromptTemplates
        
        # Calculate user metrics
        bmi = user_profile.calculate_bmi() if hasattr(user_profile, 'calculate_bmi') else 25
        fitness_level = self._assess_fitness_level(user_profile)
        
        prompt_data = {
            'user_profile': {
                'age': user_profile.age,
                'gender': user_profile.gender,
                'height': user_profile.height_cm,
                'weight': user_profile.weight_kg,
                'bmi': bmi,
                'activity_level': user_profile.activity_level,
                'fitness_level': fitness_level,
                'health_conditions': getattr(user_profile, 'health_conditions', []),
                'injuries_limitations': params.get('injuries_limitations', ''),
            },
            'plan_preferences': {
                'duration_weeks': params.get('duration_weeks', 12),
                'workouts_per_week': params.get('workout_days_per_week', 3),
                'workout_duration': params.get('workout_duration', 45),
                'fitness_goals': params.get('fitness_goals', []),
                'preferred_workout_types': params.get('preferred_workout_types', []),
                'available_equipment': params.get('available_equipment', ['bodyweight']),
                'preferred_times': params.get('preferred_times', []),
                'experience_level': params.get('experience_level', 'beginner'),
            },
            'context': {
                'current_date': datetime.now().strftime('%Y-%m-%d'),
                'season': self._get_current_season(),
            }
        }
        
        return PromptTemplates.get_workout_plan_prompt(prompt_data)
    
    def _parse_ai_workout_plan(self, ai_response: str) -> Dict:
        """Parse and validate AI workout plan response"""
        try:
            # Extract JSON from AI response
            plan_data = json.loads(ai_response)
            
            # Validate required fields
            required_fields = ['program_overview', 'weekly_schedule', 'exercises_database']
            for field in required_fields:
                if field not in plan_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate and enhance exercise data
            plan_data = self._validate_and_enhance_exercises(plan_data)
            
            # Add confidence score based on plan quality
            plan_data['confidence_score'] = self._calculate_plan_confidence(plan_data)
            
            return plan_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI workout plan JSON: {str(e)}")
            raise ValueError("Invalid AI response format")
        except Exception as e:
            logger.error(f"Error parsing workout plan: {str(e)}")
            raise
    
    def _validate_and_enhance_exercises(self, plan_data: Dict) -> Dict:
        """Validate exercises against database and enhance with additional data"""
        enhanced_exercises = {}
        
        for exercise_name, exercise_data in plan_data.get('exercises_database', {}).items():
            # Try to find exercise in our database
            try:
                db_exercise = Exercise.objects.get(
                    name__icontains=exercise_name.lower()
                )
                
                # Enhance with database information
                enhanced_exercises[exercise_name] = {
                    **exercise_data,
                    'database_id': str(db_exercise.id),
                    'category': db_exercise.category,
                    'difficulty': db_exercise.difficulty,
                    'equipment': db_exercise.equipment,
                    'primary_muscles': db_exercise.primary_muscles,
                    'secondary_muscles': db_exercise.secondary_muscles,
                    'calories_per_minute': db_exercise.calories_per_minute,
                    'instructions': db_exercise.instructions,
                    'tips': db_exercise.tips,
                }
                
            except Exercise.DoesNotExist:
                # Exercise not in database, use AI data
                enhanced_exercises[exercise_name] = {
                    **exercise_data,
                    'database_id': None,
                    'source': 'ai_generated'
                }
                logger.warning(f"Exercise not found in database: {exercise_name}")
        
        plan_data['exercises_database'] = enhanced_exercises
        return plan_data
    
    def _calculate_plan_confidence(self, plan_data: Dict) -> float:
        """Calculate confidence score for the workout plan"""
        confidence_factors = []
        
        # Check if exercises are in our database
        db_exercises = sum(1 for ex in plan_data['exercises_database'].values() 
                          if ex.get('database_id'))
        total_exercises = len(plan_data['exercises_database'])
        db_coverage = db_exercises / total_exercises if total_exercises > 0 else 0
        confidence_factors.append(db_coverage * 0.3)
        
        # Check plan structure completeness
        structure_score = 0
        if 'program_overview' in plan_data: structure_score += 0.2
        if 'weekly_schedule' in plan_data: structure_score += 0.3
        if 'progression_plan' in plan_data: structure_score += 0.2
        confidence_factors.append(structure_score)
        
        # Check exercise variety
        categories = set()
        for exercise_data in plan_data['exercises_database'].values():
            categories.add(exercise_data.get('category', 'unknown'))
        variety_score = min(len(categories) / 4, 1.0) * 0.2  # Expect 4+ categories
        confidence_factors.append(variety_score)
        
        return sum(confidence_factors)
    
    @transaction.atomic
    def _save_workout_plan_to_db(self, user: User, params: Dict, plan_data: Dict) -> WorkoutPlan:
        """Save the generated workout plan to database"""
        # Create WorkoutPlan
        start_date = date.today()
        duration_weeks = params.get('duration_weeks', 12)
        end_date = start_date + timedelta(weeks=duration_weeks)
        
        workout_plan = WorkoutPlan.objects.create(
            user=user,
            name=params.get('name', f"AI Workout Plan - {start_date}"),
            description=plan_data.get('program_overview', {}).get('description', ''),
            plan_type='custom',
            status='draft',
            start_date=start_date,
            end_date=end_date,
            total_weeks=duration_weeks,
            ai_generated=True,
            generation_prompt=json.dumps(params),
            ai_confidence_score=plan_data.get('confidence_score', 0.8),
            plan_data=plan_data
        )
        
        # Create individual workouts
        self._create_workouts_from_plan(workout_plan, plan_data)
        
        # Update total workout count
        workout_plan.total_workouts = workout_plan.workouts.count()
        workout_plan.save()
        
        return workout_plan
    
    def _create_workouts_from_plan(self, workout_plan: WorkoutPlan, plan_data: Dict):
        """Create individual workout sessions from plan data"""
        weekly_schedule = plan_data.get('weekly_schedule', {})
        current_date = workout_plan.start_date
        
        for week_num in range(workout_plan.total_weeks):
            for day_name, day_workout in weekly_schedule.items():
                if not day_workout or day_workout.get('rest_day'):
                    continue
                
                # Calculate workout date
                day_offset = self._get_day_offset(day_name)
                workout_date = current_date + timedelta(days=day_offset)
                
                # Create workout
                workout = Workout.objects.create(
                    user=workout_plan.user,
                    workout_plan=workout_plan,
                    name=day_workout.get('name', f"{day_name} Workout"),
                    description=day_workout.get('description', ''),
                    workout_type=day_workout.get('type', 'strength'),
                    scheduled_date=workout_date,
                    workout_data=day_workout
                )
                
                # Create workout exercises
                self._create_workout_exercises(workout, day_workout)
            
            # Move to next week
            current_date += timedelta(weeks=1)
    
    def _create_workout_exercises(self, workout: Workout, workout_data: Dict):
        """Create exercises for a specific workout"""
        exercises_list = workout_data.get('exercises', [])
        
        for idx, exercise_info in enumerate(exercises_list):
            exercise_name = exercise_info.get('name')
            
            # Try to find exercise in database
            try:
                exercise = Exercise.objects.get(name__icontains=exercise_name)
            except Exercise.DoesNotExist:
                # Create a temporary exercise record or skip
                logger.warning(f"Exercise not found: {exercise_name}")
                continue
            
            WorkoutExercise.objects.create(
                workout=workout,
                exercise=exercise,
                order=idx,
                sets_planned=exercise_info.get('sets', 3),
                reps_planned=exercise_info.get('reps'),
                weight_planned=exercise_info.get('weight'),
                duration_planned=exercise_info.get('duration'),
                rest_duration=exercise_info.get('rest_seconds', 60)
            )
    
    def _generate_fallback_plan(self, user: User, params: Dict) -> Dict:
        """Generate a basic fallback workout plan if AI fails"""
        return {
            'program_overview': {
                'name': 'Basic Fitness Plan',
                'description': 'A simple bodyweight workout plan for general fitness',
                'duration_weeks': params.get('duration_weeks', 4),
                'difficulty': 'beginner'
            },
            'weekly_schedule': {
                'monday': {
                    'name': 'Upper Body',
                    'type': 'strength',
                    'exercises': [
                        {'name': 'Push-ups', 'sets': 3, 'reps': 10},
                        {'name': 'Pull-ups', 'sets': 3, 'reps': 5},
                        {'name': 'Plank', 'sets': 3, 'duration': 30}
                    ]
                },
                'wednesday': {
                    'name': 'Lower Body',
                    'type': 'strength',
                    'exercises': [
                        {'name': 'Squats', 'sets': 3, 'reps': 15},
                        {'name': 'Lunges', 'sets': 3, 'reps': 10},
                        {'name': 'Calf Raises', 'sets': 3, 'reps': 15}
                    ]
                },
                'friday': {
                    'name': 'Cardio',
                    'type': 'cardio',
                    'exercises': [
                        {'name': 'Jumping Jacks', 'sets': 3, 'duration': 60},
                        {'name': 'High Knees', 'sets': 3, 'duration': 30},
                        {'name': 'Burpees', 'sets': 3, 'reps': 5}
                    ]
                }
            }
        }
    
    def _assess_fitness_level(self, user_profile: UserProfile) -> str:
        """Assess user's fitness level based on profile data"""
        # Simple assessment logic - can be enhanced
        activity_level = getattr(user_profile, 'activity_level', 'sedentary')
        
        activity_mapping = {
            'sedentary': 'beginner',
            'lightly_active': 'beginner',
            'moderately_active': 'intermediate',
            'very_active': 'intermediate',
            'extremely_active': 'advanced'
        }
        
        return activity_mapping.get(activity_level, 'beginner')
    
    def _get_current_season(self) -> str:
        """Get current season for seasonal workout adjustments"""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'
    
    def _get_day_offset(self, day_name: str) -> int:
        """Get day offset from monday for scheduling"""
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        return day_mapping.get(day_name.lower(), 0)


class WorkoutTrackingService:
    """Service for workout progress tracking and analytics"""
    
    def track_workout_progress(self, user: User, workout_id: str, exercise_progress: List[Dict]) -> Dict:
        """Track progress for a specific workout"""
        try:
            workout = Workout.objects.get(id=workout_id, user=user)
            
            with transaction.atomic():
                for progress_data in exercise_progress:
                    self._update_exercise_progress(workout, progress_data)
                
                # Update workout status if all exercises completed
                self._update_workout_status(workout)
                
                # Update workout plan progress
                if workout.workout_plan:
                    workout.workout_plan.update_completion_percentage()
            
            return {
                'success': True,
                'workout_completion': self._calculate_workout_completion(workout),
                'calories_estimate': self._estimate_calories_burned(workout)
            }
            
        except Workout.DoesNotExist:
            return {'success': False, 'error': 'Workout not found'}
        except Exception as e:
            logger.error(f"Error tracking workout progress: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _update_exercise_progress(self, workout: Workout, progress_data: Dict):
        """Update progress for a specific exercise in workout"""
        try:
            workout_exercise = WorkoutExercise.objects.get(
                workout=workout,
                exercise_id=progress_data['exercise_id']
            )
            
            # Add new performance data
            performance_entry = {
                'set': progress_data['set_number'],
                'timestamp': timezone.now().isoformat(),
            }
            
            if 'reps_completed' in progress_data:
                performance_entry['reps'] = progress_data['reps_completed']
            if 'weight_used' in progress_data:
                performance_entry['weight'] = progress_data['weight_used']
            if 'duration_seconds' in progress_data:
                performance_entry['duration'] = progress_data['duration_seconds']
            if 'notes' in progress_data:
                performance_entry['notes'] = progress_data['notes']
            
            # Update performance data
            if not workout_exercise.performance_data:
                workout_exercise.performance_data = []
            
            workout_exercise.performance_data.append(performance_entry)
            
            # Update sets completed
            completed_sets = len([p for p in workout_exercise.performance_data 
                                if p.get('set') == progress_data['set_number']])
            workout_exercise.sets_completed = max(
                workout_exercise.sets_completed, 
                progress_data['set_number']
            )
            
            workout_exercise.save()
            
        except WorkoutExercise.DoesNotExist:
            logger.error(f"WorkoutExercise not found for exercise {progress_data['exercise_id']}")
    
    def _update_workout_status(self, workout: Workout):
        """Update workout status based on exercise completion"""
        total_exercises = workout.exercises.count()
        if total_exercises == 0:
            return
        
        completed_exercises = workout.exercises.filter(
            sets_completed__gte=models.F('sets_planned')
        ).count()
        
        completion_rate = completed_exercises / total_exercises
        
        if completion_rate >= 0.8:  # 80% completion threshold
            workout.status = 'completed'
            if not workout.completed_at:
                workout.completed_at = timezone.now()
        elif workout.status == 'scheduled':
            workout.status = 'in_progress'
            if not workout.started_at:
                workout.started_at = timezone.now()
        
        workout.save()
    
    def _calculate_workout_completion(self, workout: Workout) -> float:
        """Calculate overall workout completion percentage"""
        exercises = workout.exercises.all()
        if not exercises:
            return 0.0
        
        total_completion = 0
        for exercise in exercises:
            if exercise.sets_planned > 0:
                exercise_completion = min(
                    exercise.sets_completed / exercise.sets_planned, 1.0
                )
                total_completion += exercise_completion
        
        return (total_completion / len(exercises)) * 100
    
    def _estimate_calories_burned(self, workout: Workout) -> int:
        """Estimate calories burned during workout"""
        total_calories = 0
        
        for exercise in workout.exercises.all():
            if exercise.exercise.calories_per_minute > 0:
                # Estimate duration based on sets and rest
                estimated_duration = (
                    exercise.sets_completed * 1 +  # 1 min per set
                    exercise.sets_completed * (exercise.rest_duration / 60)
                )
                total_calories += exercise.exercise.calories_per_minute * estimated_duration
        
        return int(total_calories)


class FitnessAnalyticsService:
    """Service for fitness analytics and insights"""
    
    def generate_user_insights(self, user: User) -> Dict:
        """Generate comprehensive fitness insights for user"""
        try:
            insights = {
                'workout_patterns': self._analyze_workout_patterns(user),
                'progress_trends': self._analyze_progress_trends(user),
                'goal_analysis': self._analyze_goal_progress(user),
                'recommendations': self._generate_recommendations(user),
                'achievements': self._identify_achievements(user),
            }
            
            return {'success': True, 'insights': insights}
            
        except Exception as e:
            logger.error(f"Error generating fitness insights: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _analyze_workout_patterns(self, user: User) -> Dict:
        """Analyze user's workout patterns and habits"""
        # Get workouts from last 3 months
        three_months_ago = timezone.now() - timedelta(days=90)
        workouts = Workout.objects.filter(
            user=user,
            created_at__gte=three_months_ago,
            status='completed'
        )
        
        # Workout frequency analysis
        workout_by_day = {}
        workout_by_type = {}
        
        for workout in workouts:
            day_name = workout.scheduled_date.strftime('%A')
            workout_by_day[day_name] = workout_by_day.get(day_name, 0) + 1
            
            workout_by_type[workout.workout_type] = workout_by_type.get(workout.workout_type, 0) + 1
        
        # Calculate consistency
        weeks_with_workouts = len(set(
            workout.scheduled_date.strftime('%Y-%W') for workout in workouts
        ))
        total_weeks = 13  # ~3 months
        consistency_rate = (weeks_with_workouts / total_weeks) * 100
        
        return {
            'total_workouts': workouts.count(),
            'consistency_rate': consistency_rate,
            'preferred_days': dict(sorted(workout_by_day.items(), key=lambda x: x[1], reverse=True)),
            'workout_types': workout_by_type,
            'average_duration': workouts.aggregate(
                avg_duration=Avg('actual_duration')
            )['avg_duration'] or 0,
        }
    
    def _analyze_progress_trends(self, user: User) -> Dict:
        """Analyze fitness progress trends"""
        # Get recent metrics
        recent_metrics = FitnessMetric.objects.filter(
            user=user,
            recorded_date__gte=timezone.now().date() - timedelta(days=90)
        ).order_by('recorded_date')
        
        trends = {}
        for metric in recent_metrics:
            metric_key = metric.metric_type
            if metric_key not in trends:
                trends[metric_key] = []
            
            trends[metric_key].append({
                'date': metric.recorded_date.isoformat(),
                'value': metric.value,
                'unit': metric.unit
            })
        
        # Calculate trend directions
        trend_analysis = {}
        for metric_type, values in trends.items():
            if len(values) >= 2:
                first_value = values[0]['value']
                last_value = values[-1]['value']
                change_percent = ((last_value - first_value) / first_value) * 100
                
                trend_analysis[metric_type] = {
                    'direction': 'up' if change_percent > 5 else 'down' if change_percent < -5 else 'stable',
                    'change_percent': round(change_percent, 1),
                    'data_points': values
                }
        
        return trend_analysis
    
    def _analyze_goal_progress(self, user: User) -> Dict:
        """Analyze progress toward fitness goals"""
        goals = FitnessGoal.objects.filter(user=user, status='active')
        
        goal_analysis = {
            'total_goals': goals.count(),
            'on_track': 0,
            'behind': 0,
            'ahead': 0,
            'goal_details': []
        }
        
        for goal in goals:
            # Calculate expected progress based on time elapsed
            total_days = (goal.target_date - goal.start_date).days
            elapsed_days = (timezone.now().date() - goal.start_date).days
            expected_progress = (elapsed_days / total_days) * 100 if total_days > 0 else 0
            
            actual_progress = goal.progress_percentage
            
            # Categorize progress
            if actual_progress >= expected_progress + 10:
                status = 'ahead'
                goal_analysis['ahead'] += 1
            elif actual_progress >= expected_progress - 10:
                status = 'on_track'
                goal_analysis['on_track'] += 1
            else:
                status = 'behind'
                goal_analysis['behind'] += 1
            
            goal_analysis['goal_details'].append({
                'id': str(goal.id),
                'title': goal.title,
                'status': status,
                'progress': actual_progress,
                'expected_progress': expected_progress,
                'target_date': goal.target_date.isoformat()
            })
        
        return goal_analysis
    
    def _generate_recommendations(self, user: User) -> List[Dict]:
        """Generate personalized fitness recommendations"""
        recommendations = []
        
        # Analyze workout patterns
        patterns = self._analyze_workout_patterns(user)
        
        # Consistency recommendations
        if patterns['consistency_rate'] < 50:
            recommendations.append({
                'type': 'consistency',
                'priority': 'high',
                'title': 'Improve Workout Consistency',
                'description': 'Try to maintain at least 3 workouts per week for better results.',
                'action': 'Schedule specific workout times in your calendar'
            })
        
        # Variety recommendations
        if len(patterns['workout_types']) < 2:
            recommendations.append({
                'type': 'variety',
                'priority': 'medium',
                'title': 'Add Workout Variety',
                'description': 'Include different types of exercises for balanced fitness.',
                'action': 'Try adding cardio or flexibility workouts to your routine'
            })
        
        # Progress tracking recommendations
        recent_metrics = FitnessMetric.objects.filter(
            user=user,
            recorded_date__gte=timezone.now().date() - timedelta(days=30)
        ).count()
        
        if recent_metrics < 4:  # Less than weekly tracking
            recommendations.append({
                'type': 'tracking',
                'priority': 'medium',
                'title': 'Track Progress Regularly',
                'description': 'Regular progress tracking helps maintain motivation.',
                'action': 'Log your key metrics at least weekly'
            })
        
        return recommendations
    
    def _identify_achievements(self, user: User) -> List[Dict]:
        """Identify recent achievements and milestones"""
        achievements = []
        
        # Check for completed goals
        recent_completed_goals = FitnessGoal.objects.filter(
            user=user,
            status='completed',
            completed_date__gte=timezone.now().date() - timedelta(days=30)
        )
        
        for goal in recent_completed_goals:
            achievements.append({
                'type': 'goal_completed',
                'title': f'Goal Achieved: {goal.title}',
                'description': f'Successfully reached your target of {goal.target_value} {goal.unit}',
                'date': goal.completed_date.isoformat(),
                'icon': '🎯'
            })
        
        # Check workout streaks
        recent_workouts = Workout.objects.filter(
            user=user,
            status='completed',
            completed_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-completed_at')
        
        if recent_workouts.count() >= 5:
            achievements.append({
                'type': 'streak',
                'title': 'Workout Warrior!',
                'description': f'Completed {recent_workouts.count()} workouts this month',
                'date': timezone.now().date().isoformat(),
                'icon': '🔥'
            })
        
        # Check for personal records
        strength_metrics = FitnessMetric.objects.filter(
            user=user,
            metric_type='strength_1rm',
            recorded_date__gte=timezone.now().date() - timedelta(days=30)
        ).order_by('-value')
        
        if strength_metrics.exists():
            best_lift = strength_metrics.first()
            achievements.append({
                'type': 'personal_record',
                'title': 'New Personal Record!',
                'description': f'New 1RM in {best_lift.exercise_name}: {best_lift.value} {best_lift.unit}',
                'date': best_lift.recorded_date.isoformat(),
                'icon': '💪'
            })
        
        return achievements


class ExerciseRecommendationService:
    """Service for exercise recommendations and substitutions"""
    
    def __init__(self):
        self.ai_client = AIClient()
    
    def recommend_exercises(self, user: User, criteria: Dict) -> Dict:
        """Recommend exercises based on user criteria"""
        try:
            # Get user profile for personalization
            user_profile = UserProfile.objects.get(user=user)
            
            # Build base query
            exercises_query = Exercise.objects.filter(is_active=True)
            
            # Apply filters
            if criteria.get('category'):
                exercises_query = exercises_query.filter(category=criteria['category'])
            
            if criteria.get('difficulty'):
                exercises_query = exercises_query.filter(difficulty=criteria['difficulty'])
            
            if criteria.get('equipment'):
                exercises_query = exercises_query.filter(equipment__in=criteria['equipment'])
            
            if criteria.get('muscle_groups'):
                exercises_query = exercises_query.filter(
                    Q(primary_muscles__overlap=criteria['muscle_groups']) |
                    Q(secondary_muscles__overlap=criteria['muscle_groups'])
                )
            
            # Get exercises
            exercises = list(exercises_query[:20])
            
            # Use AI to rank and personalize recommendations
            if exercises:
                ranked_exercises = self._ai_rank_exercises(user_profile, exercises, criteria)
                return {
                    'success': True,
                    'exercises': ranked_exercises,
                    'total_count': len(ranked_exercises)
                }
            else:
                return {
                    'success': True,
                    'exercises': [],
                    'total_count': 0,
                    'message': 'No exercises found matching your criteria'
                }
                
        except Exception as e:
            logger.error(f"Error recommending exercises: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def find_exercise_substitutes(self, exercise_id: str, reason: str = '') -> Dict:
        """Find substitute exercises for a given exercise"""
        try:
            original_exercise = Exercise.objects.get(id=exercise_id)
            
            # Find similar exercises based on muscle groups and movement patterns
            substitutes = Exercise.objects.filter(
                category=original_exercise.category,
                primary_muscles__overlap=original_exercise.primary_muscles,
                is_active=True
            ).exclude(id=exercise_id)[:10]
            
            # Use AI to rank substitutes based on similarity and reason
            if reason:
                ranked_substitutes = self._ai_rank_substitutes(
                    original_exercise, list(substitutes), reason
                )
            else:
                ranked_substitutes = list(substitutes)
            
            return {
                'success': True,
                'original_exercise': {
                    'id': str(original_exercise.id),
                    'name': original_exercise.name,
                    'category': original_exercise.category
                },
                'substitutes': [
                    {
                        'id': str(ex.id),
                        'name': ex.name,
                        'category': ex.category,
                        'difficulty': ex.difficulty,
                        'equipment': ex.equipment,
                        'similarity_score': getattr(ex, 'similarity_score', 0.8)
                    }
                    for ex in ranked_substitutes
                ]
            }
            
        except Exercise.DoesNotExist:
            return {'success': False, 'error': 'Exercise not found'}
        except Exception as e:
            logger.error(f"Error finding exercise substitutes: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _ai_rank_exercises(self, user_profile: UserProfile, exercises: List[Exercise], criteria: Dict) -> List[Dict]:
        """Use AI to rank exercises based on user profile and preferences"""
        # For now, implement simple ranking logic
        # Can be enhanced with actual AI ranking later
        
        user_experience = getattr(user_profile, 'fitness_experience', 'beginner')
        user_goals = criteria.get('fitness_goals', [])
        
        ranked_exercises = []
        
        for exercise in exercises:
            score = 0.5  # Base score
            
            # Adjust based on difficulty match
            if exercise.difficulty == user_experience:
                score += 0.2
            elif (exercise.difficulty == 'beginner' and user_experience == 'intermediate') or \
                 (exercise.difficulty == 'intermediate' and user_experience == 'advanced'):
                score += 0.1
            
            # Adjust based on goals
            if 'strength' in user_goals and exercise.category == 'strength':
                score += 0.15
            if 'cardio' in user_goals and exercise.category == 'cardio':
                score += 0.15
            if 'flexibility' in user_goals and exercise.category == 'flexibility':
                score += 0.15
            
            # Add some randomization for variety
            import random
            score += random.uniform(-0.1, 0.1)
            
            ranked_exercises.append({
                'id': str(exercise.id),
                'name': exercise.name,
                'category': exercise.category,
                'difficulty': exercise.difficulty,
                'equipment': exercise.equipment,
                'description': exercise.description,
                'primary_muscles': exercise.primary_muscles,
                'secondary_muscles': exercise.secondary_muscles,
                'calories_per_minute': exercise.calories_per_minute,
                'recommendation_score': round(score, 2),
                'instructions': exercise.instructions,
                'tips': exercise.tips,
                'image_url': exercise.image_url,
                'video_url': exercise.video_url
            })
        
        # Sort by recommendation score
        ranked_exercises.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        return ranked_exercises
    
    def _ai_rank_substitutes(self, original: Exercise, substitutes: List[Exercise], reason: str) -> List[Exercise]:
        """Use AI to rank exercise substitutes based on substitution reason"""
        # Simple ranking based on muscle overlap and equipment similarity
        ranked = []
        
        for substitute in substitutes:
            score = 0.5
            
            # Muscle group overlap
            primary_overlap = len(set(original.primary_muscles) & set(substitute.primary_muscles))
            score += primary_overlap * 0.1
            
            # Equipment similarity
            if original.equipment == substitute.equipment:
                score += 0.2
            
            # Difficulty matching
            if original.difficulty == substitute.difficulty:
                score += 0.1
            
            substitute.similarity_score = score
            ranked.append(substitute)
        
        # Sort by similarity score
        ranked.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return ranked


class WorkoutPlanOptimizationService:
    """Service for optimizing and adjusting workout plans"""
    
    def optimize_workout_plan(self, workout_plan_id: str, optimization_criteria: Dict) -> Dict:
        """Optimize an existing workout plan based on user feedback and progress"""
        try:
            workout_plan = WorkoutPlan.objects.get(id=workout_plan_id)
            
            # Analyze current plan performance
            performance_analysis = self._analyze_plan_performance(workout_plan)
            
            # Generate optimization recommendations
            optimizations = self._generate_optimizations(
                workout_plan, performance_analysis, optimization_criteria
            )
            
            # Apply optimizations if requested
            if optimization_criteria.get('apply_optimizations', False):
                optimized_plan = self._apply_optimizations(workout_plan, optimizations)
                return {
                    'success': True,
                    'optimized_plan_id': str(optimized_plan.id),
                    'optimizations_applied': optimizations,
                    'performance_improvement_estimate': 15  # Placeholder
                }
            else:
                return {
                    'success': True,
                    'current_performance': performance_analysis,
                    'recommended_optimizations': optimizations,
                    'estimated_improvement': 15  # Placeholder
                }
                
        except WorkoutPlan.DoesNotExist:
            return {'success': False, 'error': 'Workout plan not found'}
        except Exception as e:
            logger.error(f"Error optimizing workout plan: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _analyze_plan_performance(self, workout_plan: WorkoutPlan) -> Dict:
        """Analyze the performance of a workout plan"""
        workouts = workout_plan.workouts.all()
        completed_workouts = workouts.filter(status='completed')
        
        if not workouts.exists():
            return {'completion_rate': 0, 'adherence': 0, 'satisfaction': 0}
        
        # Calculate completion rate
        completion_rate = (completed_workouts.count() / workouts.count()) * 100
        
        # Calculate average satisfaction (difficulty ratings)
        avg_satisfaction = completed_workouts.aggregate(
            avg_difficulty=Avg('difficulty_rating')
        )['avg_difficulty'] or 5
        
        # Calculate adherence (workouts completed on time)
        on_time_workouts = completed_workouts.filter(
            completed_at__date=models.F('scheduled_date')
        ).count()
        adherence_rate = (on_time_workouts / completed_workouts.count()) * 100 if completed_workouts.exists() else 0
        
        return {
            'completion_rate': round(completion_rate, 1),
            'adherence_rate': round(adherence_rate, 1),
            'average_satisfaction': round(avg_satisfaction, 1),
            'total_workouts': workouts.count(),
            'completed_workouts': completed_workouts.count()
        }
    
    def _generate_optimizations(self, workout_plan: WorkoutPlan, performance: Dict, criteria: Dict) -> List[Dict]:
        """Generate optimization recommendations"""
        optimizations = []
        
        # Low completion rate optimizations
        if performance['completion_rate'] < 70:
            optimizations.append({
                'type': 'reduce_frequency',
                'priority': 'high',
                'description': 'Reduce workout frequency to improve consistency',
                'current_value': 'Current frequency might be too high',
                'recommended_value': 'Reduce by 1 workout per week',
                'expected_impact': 'Improve completion rate by 20%'
            })
        
        # Low adherence optimizations
        if performance['adherence_rate'] < 60:
            optimizations.append({
                'type': 'adjust_scheduling',
                'priority': 'medium',
                'description': 'Adjust workout scheduling for better adherence',
                'current_value': 'Current schedule may not fit lifestyle',
                'recommended_value': 'Move workouts to preferred time slots',
                'expected_impact': 'Improve adherence by 15%'
            })
        
        # Difficulty adjustments
        if performance['average_satisfaction'] < 4:  # Too hard
            optimizations.append({
                'type': 'reduce_difficulty',
                'priority': 'high',
                'description': 'Reduce workout difficulty to improve satisfaction',
                'current_value': f"Average difficulty rating: {performance['average_satisfaction']}",
                'recommended_value': 'Reduce sets/reps by 10-15%',
                'expected_impact': 'Improve satisfaction and completion'
            })
        elif performance['average_satisfaction'] > 7:  # Too easy
            optimizations.append({
                'type': 'increase_difficulty',
                'priority': 'medium',
                'description': 'Increase workout difficulty for better results',
                'current_value': f"Average difficulty rating: {performance['average_satisfaction']}",
                'recommended_value': 'Increase intensity by 10%',
                'expected_impact': 'Improve fitness gains'
            })
        
        return optimizations
    
    def _apply_optimizations(self, original_plan: WorkoutPlan, optimizations: List[Dict]) -> WorkoutPlan:
        """Apply optimizations to create a new optimized workout plan"""
        # Create a copy of the original plan
        optimized_plan = WorkoutPlan.objects.create(
            user=original_plan.user,
            name=f"{original_plan.name} (Optimized)",
            description=f"Optimized version of {original_plan.name}",
            plan_type=original_plan.plan_type,
            status='draft',
            start_date=timezone.now().date(),
            end_date=original_plan.end_date,
            total_weeks=original_plan.total_weeks,
            ai_generated=True,
            plan_data=original_plan.plan_data.copy(),
            generation_prompt=f"Optimization of plan {original_plan.id}"
        )
        
        # Apply each optimization
        for optimization in optimizations:
            if optimization['type'] == 'reduce_frequency':
                self._reduce_workout_frequency(optimized_plan)
            elif optimization['type'] == 'reduce_difficulty':
                self._adjust_workout_difficulty(optimized_plan, -0.15)
            elif optimization['type'] == 'increase_difficulty':
                self._adjust_workout_difficulty(optimized_plan, 0.10)
        
        return optimized_plan
    
    def _reduce_workout_frequency(self, workout_plan: WorkoutPlan):
        """Reduce workout frequency in the plan"""
        # Implementation would modify the plan_data to reduce frequency
        # This is a placeholder for the actual optimization logic
        pass
    
    def _adjust_workout_difficulty(self, workout_plan: WorkoutPlan, adjustment_factor: float):
        """Adjust workout difficulty by the given factor"""
        # Implementation would modify sets/reps in the plan_data
        # This is a placeholder for the actual optimization logic
        pass