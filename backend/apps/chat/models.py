# backend/apps/chat/models.py

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class ChatSession(models.Model):
    """Chat session for organizing conversations"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    ]
    
    CHAT_TYPE_CHOICES = [
        ('nutrition', 'Nutrition Coaching'),
        ('fitness', 'Fitness Coaching'),
        ('general', 'General Wellness'),
        ('meal_planning', 'Meal Planning'),
        ('workout_planning', 'Workout Planning'),
        ('progress_review', 'Progress Review'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    
    # Session details
    title = models.CharField(max_length=200, blank=True)
    chat_type = models.CharField(max_length=20, choices=CHAT_TYPE_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Session context
    context_data = models.JSONField(default=dict, blank=True)
    session_goals = models.JSONField(default=list, blank=True)
    
    # Analytics
    message_count = models.IntegerField(default=0)
    total_tokens_used = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)
    
    # User satisfaction
    satisfaction_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    feedback = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-period_end', '-created_at']
        indexes = [
            models.Index(fields=['user', 'summary_type']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.summary_type})"Field(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['chat_type']),
            models.Index(fields=['last_activity']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title or f'{self.chat_type} chat'}"

    @property
    def is_active(self):
        return self.status == 'active'

    def update_activity(self):
        """Update last activity timestamp"""
        from django.utils import timezone
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])

    def generate_title(self):
        """Generate a title based on the first few messages"""
        if not self.title:
            recent_messages = self.messages.filter(
                role='user'
            ).order_by('created_at')[:3]
            
            if recent_messages.exists():
                first_message = recent_messages.first().content[:50]
                self.title = f"{first_message}..." if len(first_message) == 50 else first_message
                self.save(update_fields=['title'])


class Message(models.Model):
    """Individual message in a chat session"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'AI Assistant'),
        ('system', 'System'),
    ]
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text Message'),
        ('meal_plan', 'Meal Plan'),
        ('workout_plan', 'Workout Plan'),
        ('nutrition_analysis', 'Nutrition Analysis'),
        ('progress_update', 'Progress Update'),
        ('recommendation', 'Recommendation'),
        ('error', 'Error Message'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    
    # Message details
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    
    # AI-specific fields
    ai_model = models.CharField(max_length=50, blank=True)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    
    # Response quality metrics
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        null=True, blank=True
    )
    response_time_ms = models.IntegerField(null=True, blank=True)
    
    # Structured data for special message types
    structured_data = models.JSONField(default=dict, blank=True)
    
    # User feedback
    user_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="User rating for AI response quality"
    )
    user_feedback = models.TextField(blank=True)
    
    # Message context
    context_data = models.JSONField(default=dict, blank=True)
    references = models.JSONField(default=list, blank=True)  # Referenced meals, workouts, etc.
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Message threading
    parent_message = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        related_name='replies'
    )

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['role', 'message_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

    @property
    def is_ai_response(self):
        return self.role == 'assistant'

    @property
    def has_structured_data(self):
        return bool(self.structured_data)

    def add_user_feedback(self, rating: int, feedback: str = ''):
        """Add user feedback for the message"""
        self.user_rating = rating
        self.user_feedback = feedback
        self.save(update_fields=['user_rating', 'user_feedback', 'updated_at'])


class ChatContext(models.Model):
    """Persistent context data for chat sessions"""
    CONTEXT_TYPE_CHOICES = [
        ('user_profile', 'User Profile Data'),
        ('nutrition_preferences', 'Nutrition Preferences'),
        ('fitness_goals', 'Fitness Goals'),
        ('health_conditions', 'Health Conditions'),
        ('meal_history', 'Recent Meal History'),
        ('workout_history', 'Recent Workout History'),
        ('conversation_memory', 'Conversation Memory'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='context_items')
    
    # Context details
    context_type = models.CharField(max_length=30, choices=CONTEXT_TYPE_CHOICES)
    key = models.CharField(max_length=100)
    value = models.JSONField()
    
    # Context metadata
    importance_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        default=0.5,
        help_text="Importance of this context for future responses"
    )
    last_referenced = models.DateTimeField(null=True, blank=True)
    reference_count = models.IntegerField(default=0)
    
    # Expiration
    expires_at = models.DateTimeField(null=True, blank=True)
    auto_refresh = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-importance_score', '-last_referenced']
        unique_together = ['session', 'context_type', 'key']
        indexes = [
            models.Index(fields=['session', 'context_type']),
            models.Index(fields=['importance_score']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.session.user.username} - {self.context_type}: {self.key}"

    def mark_referenced(self):
        """Mark this context as recently referenced"""
        from django.utils import timezone
        self.last_referenced = timezone.now()
        self.reference_count += 1
        self.save(update_fields=['last_referenced', 'reference_count', 'updated_at'])

    @property
    def is_expired(self):
        """Check if this context has expired"""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at


class ChatTemplate(models.Model):
    """Templates for common chat interactions"""
    TEMPLATE_TYPE_CHOICES = [
        ('welcome', 'Welcome Message'),
        ('meal_planning', 'Meal Planning Prompt'),
        ('workout_suggestion', 'Workout Suggestion'),
        ('nutrition_advice', 'Nutrition Advice'),
        ('progress_check', 'Progress Check-in'),
        ('goal_setting', 'Goal Setting'),
        ('motivation', 'Motivational Message'),
        ('error_recovery', 'Error Recovery'),
    ]
    
    PERSONALIZATION_LEVEL_CHOICES = [
        ('none', 'No Personalization'),
        ('basic', 'Basic Personalization'),
        ('advanced', 'Advanced Personalization'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Template details
    name = models.CharField(max_length=200)
    description = models.TextField()
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPE_CHOICES)
    
    # Template content
    prompt_template = models.TextField()
    example_response = models.TextField(blank=True)
    
    # Personalization
    personalization_level = models.CharField(
        max_length=20, 
        choices=PERSONALIZATION_LEVEL_CHOICES,
        default='basic'
    )
    required_context = models.JSONField(default=list)  # Required context keys
    optional_context = models.JSONField(default=list)  # Optional context keys
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)
    avg_user_rating = models.FloatField(default=0.0)
    
    # Template metadata
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=10, default='1.0')
    
    # Metadata
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='created_chat_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['template_type', 'name']
        indexes = [
            models.Index(fields=['template_type', 'is_active']),
            models.Index(fields=['usage_count']),
        ]

    def __str__(self):
        return f"{self.name} ({self.template_type})"

    def track_usage(self, success: bool = True, user_rating: int = None):
        """Track template usage and update metrics"""
        self.usage_count += 1
        
        if success:
            self.success_rate = (
                (self.success_rate * (self.usage_count - 1) + 1) / self.usage_count
            )
        else:
            self.success_rate = (
                (self.success_rate * (self.usage_count - 1)) / self.usage_count
            )
        
        if user_rating:
            if self.avg_user_rating == 0:
                self.avg_user_rating = user_rating
            else:
                total_ratings = self.usage_count
                self.avg_user_rating = (
                    (self.avg_user_rating * (total_ratings - 1) + user_rating) / total_ratings
                )
        
        self.save(update_fields=['usage_count', 'success_rate', 'avg_user_rating', 'updated_at'])


class ChatAnalytics(models.Model):
    """Analytics data for chat sessions"""
    METRIC_TYPE_CHOICES = [
        ('session_duration', 'Session Duration'),
        ('messages_per_session', 'Messages per Session'),
        ('user_satisfaction', 'User Satisfaction'),
        ('response_accuracy', 'Response Accuracy'),
        ('goal_completion', 'Goal Completion Rate'),
        ('feature_usage', 'Feature Usage'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_analytics')
    session = models.ForeignKey(
        ChatSession, 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        related_name='analytics'
    )
    
    # Metric details
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPE_CHOICES)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=20)
    
    # Context
    additional_data = models.JSONField(default=dict, blank=True)
    
    # Aggregation period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Metadata
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['user', 'metric_type']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['recorded_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.metric_type}: {self.metric_value} {self.metric_unit}"


class ConversationSummary(models.Model):
    """Summarized conversation data for efficient context retrieval"""
    SUMMARY_TYPE_CHOICES = [
        ('daily', 'Daily Summary'),
        ('weekly', 'Weekly Summary'),
        ('session', 'Session Summary'),
        ('topic', 'Topic Summary'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversation_summaries')
    session = models.ForeignKey(
        ChatSession, 
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='summaries'
    )
    
    # Summary details
    summary_type = models.CharField(max_length=20, choices=SUMMARY_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    summary_text = models.TextField()
    
    # Key insights
    key_topics = models.JSONField(default=list)
    action_items = models.JSONField(default=list)
    user_preferences_learned = models.JSONField(default=dict)
    
    # Temporal context
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # AI generation details
    generated_by_ai = models.BooleanField(default=True)
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        null=True, blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTime