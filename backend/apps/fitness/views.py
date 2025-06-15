# backend/apps/fitness/views.py

import logging
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q, Avg, Sum, Count
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .models import (
    Exercise, WorkoutTemplate, WorkoutPlan, Workout,
    WorkoutExercise, FitnessGoal, FitnessMetric
)
from .serializers import (
    ExerciseSerializer, ExerciseSearchSerializer, WorkoutTemplateSerializer,
    WorkoutPlanSerializer, WorkoutPlanGenerateSerializer, WorkoutSerializer,
    WorkoutCreateSerializer, WorkoutExerciseSerializer, FitnessGoalSerializer,
    FitnessMetricSerializer, FitnessDashboardSerializer, WorkoutProgressSerializer,
    WorkoutAnalyticsSerializer
)
from .services import (
    WorkoutPlanningService, WorkoutTrackingService, FitnessAnalyticsService,
    ExerciseRecommendationService, WorkoutPlanOptimizationService
)

logger = logging.getLogger(__name__)


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for exercise management"""
    queryset = Exercise.objects.filter(is_active=True)
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'difficulty', 'equipment']
    
    def get_queryset(self):
        """Filter exercises based on query parameters"""
        queryset = super().get_queryset()
        
        # Search by name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        # Filter by muscle groups
        muscle_groups = self.request.query_params.getlist('muscle_groups')
        if muscle_groups:
            queryset = queryset.filter(
                Q(primary_muscles__overlap=muscle_groups) |
                Q(secondary_muscles__overlap=muscle_groups)
            )
        
        return queryset.order_by('name')
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Advanced exercise search with AI recommendations"""
        serializer = ExerciseSearchSerializer(data=request.data)
        if serializer.is_valid():
            recommendation_service = ExerciseRecommendationService()
            result = recommendation_service.recommend_exercises(
                user=request.user,
                criteria=serializer.validated_data
            )
            
            if result['success']:
                return Response({
                    'exercises': result['exercises'],
                    'total_count': result['total_count']
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def substitutes(self, request, pk=None):
        """Find substitute exercises"""
        reason = request.query_params.get('reason', '')
        
        recommendation_service = ExerciseRecommendationService()
        result = recommendation_service.find_exercise_substitutes(
            exercise_id=pk,
            reason=reason
        )
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_404_NOT_FOUND
            )


class WorkoutTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for workout templates"""
    queryset = WorkoutTemplate.objects.filter(is_active=True)
    serializer_class = WorkoutTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['workout_type', 'difficulty', 'fitness_level']
    
    def get_queryset(self):
        """Filter templates based on user preferences"""
        queryset = super().get_queryset()
        
        # Filter by duration
        max_duration = self.request.query_params.get('max_duration')
        if max_duration:
            try:
                queryset = queryset.filter(estimated_duration__lte=int(max_duration))
            except ValueError:
                pass
        
        # Filter by equipment
        equipment = self.request.query_params.getlist('equipment')
        if equipment:
            queryset = queryset.filter(equipment_needed__overlap=equipment)
        
        return queryset.order_by('name')


class WorkoutPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for workout plan management"""
    serializer_class = WorkoutPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return workout plans for the authenticated user"""
        return WorkoutPlan.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set the user when creating a workout plan"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a personalized workout plan using AI"""
        serializer = WorkoutPlanGenerateSerializer(data=request.data)
        if serializer.is_valid():
            planning_service = WorkoutPlanningService()
            
            result = planning_service.generate_personalized_workout_plan(
                user=request.user,
                generation_params=serializer.validated_data
            )
            
            if result['success']:
                return Response({
                    'workout_plan_id': result['workout_plan_id'],
                    'ai_confidence': result['ai_confidence'],
                    'message': 'Workout plan generated successfully'
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': result['error'],
                    'fallback_plan': result.get('fallback_plan')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a workout plan"""
        workout_plan = self.get_object()
        
        # Deactivate other active plans
        WorkoutPlan.objects.filter(
            user=request.user,
            status='active'
        ).update(status='paused')
        
        # Activate this plan
        workout_plan.status = 'active'
        workout_plan.save()
        
        return Response({
            'message': 'Workout plan activated successfully',
            'plan_id': str(workout_plan.id)
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def optimize(self, request, pk=None):
        """Optimize an existing workout plan"""
        workout_plan = self.get_object()
        optimization_criteria = request.data
        
        optimization_service = WorkoutPlanOptimizationService()
        result = optimization_service.optimize_workout_plan(
            workout_plan_id=str(workout_plan.id),
            optimization_criteria=optimization_criteria
        )
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for a specific workout plan"""
        workout_plan = self.get_object()
        
        # Calculate plan analytics
        workouts = workout_plan.workouts.all()
        completed_workouts = workouts.filter(status='completed')
        
        analytics = {
            'plan_overview': {
                'total_workouts': workouts.count(),
                'completed_workouts': completed_workouts.count(),
                'completion_rate': (completed_workouts.count() / workouts.count() * 100) if workouts.exists() else 0,
                'average_duration': completed_workouts.aggregate(avg=Avg('actual_duration'))['avg'] or 0,
                'total_calories': completed_workouts.aggregate(sum=Sum('total_calories_burned'))['sum'] or 0
            },
            'workout_distribution': {},
            'weekly_progress': []
        }
        
        # Workout type distribution
        workout_types = completed_workouts.values('workout_type').annotate(
            count=Count('id')
        )
        analytics['workout_distribution'] = {
            item['workout_type']: item['count'] for item in workout_types
        }
        
        return Response(analytics, status=status.HTTP_200_OK)


class WorkoutViewSet(viewsets.ModelViewSet):
    """ViewSet for individual workout management"""
    serializer_class = WorkoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return workouts for the authenticated user"""
        queryset = Workout.objects.filter(user=self.request.user)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)
        
        # Filter by status
        workout_status = self.request.query_params.get('status')
        if workout_status:
            queryset = queryset.filter(status=workout_status)
        
        return queryset.order_by('-scheduled_date', '-scheduled_time')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return WorkoutCreateSerializer
        return WorkoutSerializer
    
    def perform_create(self, serializer):
        """Set the user when creating a workout"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a workout session"""
        workout = self.get_object()
        
        if workout.status != 'scheduled':
            return Response(
                {'error': 'Workout is not in scheduled status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        workout.status = 'in_progress'
        workout.started_at = timezone.now()
        workout.save()
        
        return Response({
            'message': 'Workout started successfully',
            'started_at': workout.started_at
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a workout session"""
        workout = self.get_object()
        
        if workout.status not in ['in_progress', 'scheduled']:
            return Response(
                {'error': 'Workout cannot be completed from current status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update workout data from request
        workout.status = 'completed'
        workout.completed_at = timezone.now()
        workout.total_calories_burned = request.data.get('total_calories_burned')
        workout.average_heart_rate = request.data.get('average_heart_rate')
        workout.max_heart_rate = request.data.get('max_heart_rate')
        workout.difficulty_rating = request.data.get('difficulty_rating')
        workout.energy_level_before = request.data.get('energy_level_before')
        workout.energy_level_after = request.data.get('energy_level_after')
        workout.notes = request.data.get('notes', '')
        
        # Set started_at if not already set
        if not workout.started_at:
            workout.started_at = workout.completed_at - timedelta(
                minutes=request.data.get('duration_minutes', 30)
            )
        
        workout.save()
        
        # Update workout plan progress if applicable
        if workout.workout_plan:
            workout.workout_plan.completed_workouts += 1
            workout.workout_plan.update_completion_percentage()
        
        return Response({
            'message': 'Workout completed successfully',
            'completed_at': workout.completed_at,
            'duration_minutes': workout.duration_minutes
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def track_progress(self, request, pk=None):
        """Track progress for workout exercises"""
        workout = self.get_object()
        
        serializer = WorkoutProgressSerializer(data=request.data, many=True)
        if serializer.is_valid():
            tracking_service = WorkoutTrackingService()
            result = tracking_service.track_workout_progress(
                user=request.user,
                workout_id=str(workout.id),
                exercise_progress=serializer.validated_data
            )
            
            if result['success']:
                return Response({
                    'message': 'Progress tracked successfully',
                    'workout_completion': result['workout_completion'],
                    'calories_estimate': result['calories_estimate']
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FitnessGoalViewSet(viewsets.ModelViewSet):
    """ViewSet for fitness goal management"""
    serializer_class = FitnessGoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return fitness goals for the authenticated user"""
        queryset = FitnessGoal.objects.filter(user=self.request.user)
        
        # Filter by status
        goal_status = self.request.query_params.get('status')
        if goal_status:
            queryset = queryset.filter(status=goal_status)
        
        # Filter by goal type
        goal_type = self.request.query_params.get('goal_type')
        if goal_type:
            queryset = queryset.filter(goal_type=goal_type)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set the user when creating a fitness goal"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update progress for a fitness goal"""
        goal = self.get_object()
        
        new_value = request.data.get('current_value')
        if new_value is not None:
            goal.current_value = new_value
            goal.update_progress()
            
            return Response({
                'message': 'Goal progress updated successfully',
                'current_value': goal.current_value,
                'progress_percentage': goal.progress_percentage,
                'status': goal.status
            }, status=status.HTTP_200_OK)
        
        return Response(
            {'error': 'current_value is required'},
            status=status.HTTP_400_BAD_REQUEST
        )


class FitnessMetricViewSet(viewsets.ModelViewSet):
    """ViewSet for fitness metric tracking"""
    serializer_class = FitnessMetricSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return fitness metrics for the authenticated user"""
        queryset = FitnessMetric.objects.filter(user=self.request.user)
        
        # Filter by metric type
        metric_type = self.request.query_params.get('metric_type')
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(recorded_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(recorded_date__lte=end_date)
        
        return queryset.order_by('-recorded_date')
    
    def perform_create(self, serializer):
        """Set the user when creating a fitness metric"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get trend analysis for fitness metrics"""
        metric_type = request.query_params.get('metric_type')
        days = int(request.query_params.get('days', 90))
        
        if not metric_type:
            return Response(
                {'error': 'metric_type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get metrics for the specified period
        start_date = timezone.now().date() - timedelta(days=days)
        metrics = self.get_queryset().filter(
            metric_type=metric_type,
            recorded_date__gte=start_date
        ).order_by('recorded_date')
        
        if not metrics.exists():
            return Response({
                'metric_type': metric_type,
                'trend_data': [],
                'trend_analysis': {
                    'direction': 'no_data',
                    'change_percent': 0,
                    'data_points': 0
                }
            }, status=status.HTTP_200_OK)
        
        # Prepare trend data
        trend_data = [
            {
                'date': metric.recorded_date.isoformat(),
                'value': metric.value,
                'unit': metric.unit
            }
            for metric in metrics
        ]
        
        # Calculate trend direction
        first_value = metrics.first().value
        last_value = metrics.last().value
        change_percent = ((last_value - first_value) / first_value) * 100 if first_value != 0 else 0
        
        if change_percent > 5:
            direction = 'up'
        elif change_percent < -5:
            direction = 'down'
        else:
            direction = 'stable'
        
        return Response({
            'metric_type': metric_type,
            'trend_data': trend_data,
            'trend_analysis': {
                'direction': direction,
                'change_percent': round(change_percent, 2),
                'data_points': len(trend_data),
                'period_days': days
            }
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def fitness_dashboard(request):
    """Get comprehensive fitness dashboard data"""
    user = request.user
    
    try:
        # Get active workout plan
        active_plan = WorkoutPlan.objects.filter(
            user=user,
            status='active'
        ).first()
        
        # Get upcoming workouts (next 7 days)
        upcoming_workouts = Workout.objects.filter(
            user=user,
            status='scheduled',
            scheduled_date__gte=timezone.now().date(),
            scheduled_date__lte=timezone.now().date() + timedelta(days=7)
        ).order_by('scheduled_date', 'scheduled_time')[:5]
        
        # Get recent completed workouts
        recent_workouts = Workout.objects.filter(
            user=user,
            status='completed',
            completed_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-completed_at')[:5]
        
        # Get active goals
        active_goals = FitnessGoal.objects.filter(
            user=user,
            status='active'
        ).order_by('-created_at')[:5]
        
        # Get recent metrics
        recent_metrics = FitnessMetric.objects.filter(
            user=user,
            recorded_date__gte=timezone.now().date() - timedelta(days=30)
        ).order_by('-recorded_date')[:10]
        
        # Calculate statistics
        total_workouts = Workout.objects.filter(
            user=user,
            status='completed'
        ).count()
        
        total_calories = Workout.objects.filter(
            user=user,
            status='completed',
            total_calories_burned__isnull=False
        ).aggregate(
            total=Sum('total_calories_burned')
        )['total'] or 0
        
        # Calculate workout streak
        workout_streak = _calculate_workout_streak(user)
        
        # Average workout duration
        avg_duration = Workout.objects.filter(
            user=user,
            status='completed',
            actual_duration__isnull=False
        ).aggregate(
            avg=Avg('actual_duration')
        )['avg'] or 0
        
        # Goals completion rate
        total_goals = FitnessGoal.objects.filter(user=user).count()
        completed_goals = FitnessGoal.objects.filter(
            user=user,
            status='completed'
        ).count()
        goals_completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0
        
        # Weekly statistics
        week_start = timezone.now().date() - timedelta(days=7)
        weekly_workouts = Workout.objects.filter(
            user=user,
            status='completed',
            completed_at__date__gte=week_start
        )
        
        weekly_stats = {
            'workout_count': weekly_workouts.count(),
            'calories_burned': weekly_workouts.aggregate(
                sum=Sum('total_calories_burned')
            )['sum'] or 0,
            'exercise_minutes': weekly_workouts.aggregate(
                sum=Sum('actual_duration')
            )['sum'] or 0
        }
        
        # Serialize the data
        dashboard_data = {
            'active_workout_plan': WorkoutPlanSerializer(active_plan).data if active_plan else None,
            'upcoming_workouts': WorkoutSerializer(upcoming_workouts, many=True).data,
            'recent_workouts': WorkoutSerializer(recent_workouts, many=True).data,
            'active_goals': FitnessGoalSerializer(active_goals, many=True).data,
            'recent_metrics': FitnessMetricSerializer(recent_metrics, many=True).data,
            'total_workouts_completed': total_workouts,
            'total_calories_burned': int(total_calories),
            'workout_streak': workout_streak,
            'avg_workout_duration': round(avg_duration, 1),
            'goals_completion_rate': round(goals_completion_rate, 1),
            'weekly_workout_count': weekly_stats['workout_count'],
            'weekly_calories_burned': int(weekly_stats['calories_burned']),
            'weekly_exercise_minutes': int(weekly_stats['exercise_minutes'])
        }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating fitness dashboard: {str(e)}")
        return Response(
            {'error': 'Failed to generate dashboard data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def fitness_insights(request):
    """Get AI-generated fitness insights and recommendations"""
    user = request.user
    
    try:
        analytics_service = FitnessAnalyticsService()
        result = analytics_service.generate_user_insights(user)
        
        if result['success']:
            return Response(result['insights'], status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Error generating fitness insights: {str(e)}")
        return Response(
            {'error': 'Failed to generate insights'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def workout_analytics(request):
    """Get detailed workout analytics"""
    user = request.user
    period = request.query_params.get('period', 'month')
    
    try:
        # Calculate date range based on period
        if period == 'week':
            start_date = timezone.now().date() - timedelta(days=7)
        elif period == 'month':
            start_date = timezone.now().date() - timedelta(days=30)
        elif period == 'quarter':
            start_date = timezone.now().date() - timedelta(days=90)
        elif period == 'year':
            start_date = timezone.now().date() - timedelta(days=365)
        else:
            start_date = timezone.now().date() - timedelta(days=30)
        
        # Get workouts for the period
        workouts = Workout.objects.filter(
            user=user,
            status='completed',
            completed_at__date__gte=start_date
        )
        
        # Workouts by day of week
        workouts_by_day = {}
        for workout in workouts:
            day_name = workout.completed_at.strftime('%A')
            workouts_by_day[day_name] = workouts_by_day.get(day_name, 0) + 1
        
        # Workouts by type
        workouts_by_type = workouts.values('workout_type').annotate(
            count=Count('id')
        )
        workouts_by_type_dict = {
            item['workout_type']: item['count'] for item in workouts_by_type
        }
        
        # Calculate total volume and average intensity
        total_volume = workouts.count()
        avg_intensity = workouts.aggregate(
            avg=Avg('difficulty_rating')
        )['avg'] or 0
        
        # Goal progress (placeholder - would need more complex logic)
        goals = FitnessGoal.objects.filter(user=user, status='active')
        goals_achieved = goals.filter(progress_percentage__gte=100).count()
        goals_on_track = goals.filter(
            progress_percentage__gte=50,
            progress_percentage__lt=100
        ).count()
        goals_behind = goals.filter(progress_percentage__lt=50).count()
        
        analytics_data = {
            'period': period,
            'workouts_by_day': workouts_by_day,
            'workouts_by_type': workouts_by_type_dict,
            'strength_progression': {},  # Placeholder for strength trends
            'endurance_progression': {},  # Placeholder for endurance trends
            'total_volume': total_volume,
            'average_intensity': round(avg_intensity, 1),
            'goals_achieved': goals_achieved,
            'goals_on_track': goals_on_track,
            'goals_behind': goals_behind
        }
        
        return Response(analytics_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating workout analytics: {str(e)}")
        return Response(
            {'error': 'Failed to generate analytics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _calculate_workout_streak(user: User) -> int:
    """Calculate current workout streak for user"""
    try:
        # Get recent workouts ordered by date
        recent_workouts = Workout.objects.filter(
            user=user,
            status='completed'
        ).order_by('-completed_at')
        
        if not recent_workouts.exists():
            return 0
        
        # Calculate streak by checking consecutive workout days
        streak = 0
        current_date = timezone.now().date()
        
        # Group workouts by date
        workout_dates = set()
        for workout in recent_workouts:
            workout_dates.add(workout.completed_at.date())
        
        # Count consecutive days with workouts
        check_date = current_date
        while check_date in workout_dates:
            streak += 1
            check_date -= timedelta(days=1)
            
            # Prevent infinite loop
            if streak > 365:
                break
        
        return streak
        
    except Exception:
        return 0