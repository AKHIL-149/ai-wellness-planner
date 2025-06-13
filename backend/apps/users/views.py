# backend/apps/users/views.py

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import transaction
import logging

from .models import User, UserProfile, UserGoal, UserPreference
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserGoalSerializer,
    UserPreferenceSerializer,
    UserDetailSerializer
)

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    """
    Register a new user account
    """
    try:
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            with transaction.atomic():
                # Create user
                user = serializer.save()
                
                # Create authentication token
                token, created = Token.objects.get_or_create(user=user)
                
                # Create default profile
                UserProfile.objects.create(
                    user=user,
                    age=request.data.get('age', 25),
                    gender=request.data.get('gender', 'prefer_not_to_say'),
                    height=request.data.get('height', 170),
                    weight=request.data.get('weight', 70)
                )
                
                # Create default preferences
                UserPreference.objects.create(user=user)
                
                logger.info(f"New user registered: {user.email}")
                
                return Response({
                    'message': 'Registration successful',
                    'user': {
                        'id': str(user.id),
                        'email': user.email,
                        'full_name': user.full_name
                    },
                    'token': token.key
                }, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': 'Registration failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return Response({
            'error': 'Registration failed',
            'message': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    """
    Authenticate user and return token
    """
    try:
        serializer = UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            # Authenticate user
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
            except User.DoesNotExist:
                user = None
            
            if user:
                # Get or create token
                token, created = Token.objects.get_or_create(user=user)
                
                logger.info(f"User logged in: {user.email}")
                
                return Response({
                    'message': 'Login successful',
                    'user': {
                        'id': str(user.id),
                        'email': user.email,
                        'full_name': user.full_name,
                        'has_profile': hasattr(user, 'profile')
                    },
                    'token': token.key
                }, status=status.HTTP_200_OK)
            
            return Response({
                'error': 'Invalid credentials',
                'message': 'Email or password is incorrect'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'error': 'Login failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return Response({
            'error': 'Login failed',
            'message': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_user(request):
    """
    Logout user by deleting their token
    """
    try:
        # Delete the user's token
        Token.objects.filter(user=request.user).delete()
        
        logger.info(f"User logged out: {request.user.email}")
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({
            'error': 'Logout failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get and update user profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def update(self, request, *args, **kwargs):
        try:
            response = super().update(request, *args, **kwargs)
            logger.info(f"Profile updated for user: {request.user.email}")
            return response
        except ValidationError as e:
            return Response({
                'error': 'Profile update failed',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Get and update user details
    """
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class UserGoalListCreateView(generics.ListCreateAPIView):
    """
    List user goals and create new goals
    """
    serializer_class = UserGoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserGoal.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        logger.info(f"New goal created for user: {self.request.user.email}")

class UserGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific goal
    """
    serializer_class = UserGoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserGoal.objects.filter(user=self.request.user)

class UserPreferenceView(generics.RetrieveUpdateAPIView):
    """
    Get and update user preferences
    """
    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        preference, created = UserPreference.objects.get_or_create(user=self.request.user)
        return preference

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_dashboard_data(request):
    """
    Get comprehensive dashboard data for the user
    """
    try:
        user = request.user
        
        # Get or create profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Get active goals
        active_goals = UserGoal.objects.filter(user=user, status='active')[:5]
        
        # Calculate health metrics
        health_metrics = {}
        if profile.bmi:
            health_metrics['bmi'] = {
                'value': profile.bmi,
                'category': profile.bmi_category,
                'status': 'normal' if 18.5 <= profile.bmi < 25 else 'attention_needed'
            }
        
        if profile.tdee:
            health_metrics['daily_calories'] = {
                'tdee': profile.tdee,
                'goal': profile.calorie_goal,
                'difference': profile.calorie_goal - profile.tdee if profile.calorie_goal else 0
            }
        
        macro_targets = profile.get_macro_targets()
        
        # Recent activity summary (placeholder - would come from meal/workout tracking)
        recent_activity = {
            'meals_logged_this_week': 0,  # Would be calculated from actual meal logs
            'workouts_completed_this_week': 0,  # Would be calculated from actual workout logs
            'water_intake_today': profile.water_intake,
            'sleep_hours_last_night': profile.sleep_hours
        }
        
        dashboard_data = {
            'user': {
                'id': str(user.id),
                'full_name': user.full_name,
                'email': user.email,
                'member_since': user.date_joined.strftime('%Y-%m-%d')
            },
            'profile': {
                'age': profile.age,
                'primary_goal': profile.get_primary_goal_display(),
                'activity_level': profile.get_activity_level_display(),
                'fitness_level': profile.get_fitness_level_display()
            },
            'health_metrics': health_metrics,
            'macro_targets': macro_targets,
            'active_goals': [
                {
                    'id': goal.id,
                    'title': goal.title,
                    'type': goal.get_goal_type_display(),
                    'progress': goal.progress_percentage,
                    'target_date': goal.target_date.strftime('%Y-%m-%d') if goal.target_date else None
                } for goal in active_goals
            ],
            'recent_activity': recent_activity,
            'recommendations': generate_user_recommendations(profile)
        }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Dashboard data error for user {request.user.email}: {str(e)}")
        return Response({
            'error': 'Failed to load dashboard data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_goal_progress(request, goal_id):
    """
    Update progress for a specific goal
    """
    try:
        goal = UserGoal.objects.get(id=goal_id, user=request.user)
        
        new_value = request.data.get('current_value')
        if new_value is not None:
            goal.current_value = float(new_value)
            
            # Check if goal is completed
            if goal.target_value and goal.current_value >= goal.target_value:
                goal.status = 'completed'
                goal.completed_at = timezone.now()
            
            goal.save()
            
            logger.info(f"Goal progress updated for user {request.user.email}: {goal.title}")
            
            return Response({
                'message': 'Goal progress updated',
                'goal': {
                    'id': goal.id,
                    'current_value': goal.current_value,
                    'progress_percentage': goal.progress_percentage,
                    'status': goal.status
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Invalid progress value'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except UserGoal.DoesNotExist:
        return Response({
            'error': 'Goal not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Goal progress update error: {str(e)}")
        return Response({
            'error': 'Failed to update goal progress'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_health_insights(request):
    """
    Get AI-powered health insights for the user
    """
    try:
        profile = request.user.profile
        
        insights = []
        
        # BMI insights
        if profile.bmi:
            if profile.bmi < 18.5:
                insights.append({
                    'type': 'health',
                    'priority': 'medium',
                    'title': 'Underweight Concern',
                    'message': 'Your BMI indicates you may be underweight. Consider consulting with a healthcare provider.',
                    'action': 'Consider increasing caloric intake with nutrient-dense foods.'
                })
            elif profile.bmi >= 30:
                insights.append({
                    'type': 'health',
                    'priority': 'high',
                    'title': 'Weight Management',
                    'message': 'Your BMI indicates obesity. A structured weight loss plan could benefit your health.',
                    'action': 'Focus on creating a sustainable caloric deficit through diet and exercise.'
                })
        
        # Activity level insights
        if profile.activity_level == 'sedentary':
            insights.append({
                'type': 'fitness',
                'priority': 'medium',
                'title': 'Increase Activity',
                'message': 'Adding more physical activity could significantly improve your health.',
                'action': 'Start with 15-20 minutes of daily walking or light exercise.'
            })
        
        # Sleep insights
        if profile.sleep_hours < 7:
            insights.append({
                'type': 'lifestyle',
                'priority': 'high',
                'title': 'Sleep Optimization',
                'message': 'You may not be getting enough sleep for optimal health and recovery.',
                'action': 'Aim for 7-9 hours of quality sleep per night.'
            })
        
        # Hydration insights
        if profile.water_intake < 2.0:
            insights.append({
                'type': 'nutrition',
                'priority': 'low',
                'title': 'Hydration',
                'message': 'Consider increasing your daily water intake.',
                'action': 'Aim for at least 2-3 liters of water per day.'
            })
        
        # Stress insights
        if profile.stress_level >= 7:
            insights.append({
                'type': 'lifestyle',
                'priority': 'high',
                'title': 'Stress Management',
                'message': 'High stress levels can impact your health and fitness goals.',
                'action': 'Consider stress-reduction techniques like meditation, yoga, or regular exercise.'
            })
        
        return Response({
            'insights': insights,
            'generated_at': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Health insights error: {str(e)}")
        return Response({
            'error': 'Failed to generate health insights'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_user_account(request):
    """
    Delete user account and all associated data
    """
    try:
        user = request.user
        email = user.email
        
        # Delete user (cascade will handle related objects)
        user.delete()
        
        logger.info(f"User account deleted: {email}")
        
        return Response({
            'message': 'Account deleted successfully'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Account deletion error: {str(e)}")
        return Response({
            'error': 'Failed to delete account'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def generate_user_recommendations(profile):
    """
    Generate personalized recommendations based on user profile
    """
    recommendations = []
    
    # Goal-based recommendations
    if profile.primary_goal == 'weight_loss':
        recommendations.append({
            'type': 'nutrition',
            'title': 'Create a Caloric Deficit',
            'description': 'Focus on portion control and nutrient-dense foods to achieve your weight loss goal.',
            'priority': 'high'
        })
        recommendations.append({
            'type': 'fitness',
            'title': 'Combine Cardio and Strength',
            'description': 'Mix cardiovascular exercise with strength training for optimal weight loss.',
            'priority': 'high'
        })
    elif profile.primary_goal == 'muscle_gain':
        recommendations.append({
            'type': 'nutrition',
            'title': 'Increase Protein Intake',
            'description': f'Aim for {profile.protein_goal}g of protein daily to support muscle growth.',
            'priority': 'high'
        })
        recommendations.append({
            'type': 'fitness',
            'title': 'Progressive Overload',
            'description': 'Focus on compound movements and gradually increase weights.',
            'priority': 'high'
        })
    
    # Activity level recommendations
    if profile.activity_level == 'sedentary':
        recommendations.append({
            'type': 'lifestyle',
            'title': 'Start Moving More',
            'description': 'Begin with short walks and gradually increase daily activity.',
            'priority': 'medium'
        })
    
    # Beginner-specific recommendations
    if profile.fitness_level == 'beginner':
        recommendations.append({
            'type': 'fitness',
            'title': 'Focus on Form',
            'description': 'Master basic movements before progressing to more complex exercises.',
            'priority': 'medium'
        })
    
    return recommendations[:5]  # Limit to top 5 recommendations