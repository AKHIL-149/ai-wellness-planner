# backend/apps/chat/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    ChatSession, Message, ChatContext, ChatTemplate, 
    ChatAnalytics, ConversationSummary
)


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model"""
    is_ai_response = serializers.ReadOnlyField()
    has_structured_data = serializers.ReadOnlyField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'role', 'content', 'message_type', 'ai_model',
            'prompt_tokens', 'completion_tokens', 'total_tokens',
            'confidence_score', 'response_time_ms', 'structured_data',
            'user_rating', 'user_feedback', 'context_data', 'references',
            'parent_message', 'is_ai_response', 'has_structured_data',
            'replies', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'is_ai_response', 
            'has_structured_data'
        ]

    def get_replies(self, obj):
        """Get reply messages for threading"""
        if obj.replies.exists():
            return MessageSerializer(obj.replies.all(), many=True, context=self.context).data
        return []

    def validate_role(self, value):
        """Validate message role"""
        if value not in ['user', 'assistant', 'system']:
            raise serializers.ValidationError("Invalid role")
        return value

    def validate_user_rating(self, value):
        """Validate user rating"""
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages"""
    
    class Meta:
        model = Message
        fields = [
            'content', 'message_type', 'context_data', 'references', 'parent_message'
        ]

    def validate_content(self, value):
        """Validate message content"""
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        if len(value) > 10000:
            raise serializers.ValidationError("Message content too long (max 10000 characters)")
        return value


class ChatContextSerializer(serializers.ModelSerializer):
    """Serializer for ChatContext model"""
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = ChatContext
        fields = [
            'id', 'context_type', 'key', 'value', 'importance_score',
            'last_referenced', 'reference_count', 'expires_at',
            'auto_refresh', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_expired']

    def validate_importance_score(self, value):
        """Validate importance score"""
        if value < 0 or value > 1:
            raise serializers.ValidationError("Importance score must be between 0 and 1")
        return value


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for ChatSession model"""
    is_active = serializers.ReadOnlyField()
    recent_messages = serializers.SerializerMethodField()
    context_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'chat_type', 'status', 'context_data',
            'session_goals', 'message_count', 'total_tokens_used',
            'avg_response_time', 'satisfaction_rating', 'feedback',
            'is_active', 'recent_messages', 'context_summary',
            'created_at', 'updated_at', 'last_activity'
        ]
        read_only_fields = [
            'id', 'message_count', 'total_tokens_used', 'avg_response_time',
            'is_active', 'created_at', 'updated_at', 'last_activity'
        ]

    def get_recent_messages(self, obj):
        """Get recent messages for session preview"""
        recent_messages = obj.messages.order_by('-created_at')[:5]
        return MessageSerializer(recent_messages, many=True, context=self.context).data

    def get_context_summary(self, obj):
        """Get summary of session context"""
        context_items = obj.context_items.filter(
            importance_score__gte=0.7
        ).order_by('-importance_score')[:3]
        
        return [
            {
                'type': item.context_type,
                'key': item.key,
                'importance': item.importance_score
            }
            for item in context_items
        ]


class ChatSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat sessions"""
    
    class Meta:
        model = ChatSession
        fields = ['title', 'chat_type', 'context_data', 'session_goals']

    def validate_chat_type(self, value):
        """Validate chat type"""
        valid_types = [choice[0] for choice in ChatSession.CHAT_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid chat type. Must be one of: {valid_types}")
        return value


class ChatTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ChatTemplate model"""
    
    class Meta:
        model = ChatTemplate
        fields = [
            'id', 'name', 'description', 'template_type', 'prompt_template',
            'example_response', 'personalization_level', 'required_context',
            'optional_context', 'usage_count', 'success_rate',
            'avg_user_rating', 'is_active', 'version', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'usage_count', 'success_rate', 'avg_user_rating',
            'created_at', 'updated_at'
        ]


class ConversationSummarySerializer(serializers.ModelSerializer):
    """Serializer for ConversationSummary model"""
    
    class Meta:
        model = ConversationSummary
        fields = [
            'id', 'summary_type', 'title', 'summary_text', 'key_topics',
            'action_items', 'user_preferences_learned', 'period_start',
            'period_end', 'generated_by_ai', 'confidence_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatStartSerializer(serializers.Serializer):
    """Serializer for starting a new chat"""
    message = serializers.CharField(max_length=10000)
    chat_type = serializers.ChoiceField(choices=ChatSession.CHAT_TYPE_CHOICES, required=False)
    context = serializers.DictField(required=False, default=dict)
    goals = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        default=list
    )

    def validate_message(self, value):
        """Validate initial message"""
        if not value.strip():
            raise serializers.ValidationError("Initial message cannot be empty")
        return value.strip()


class ChatMessageSerializer(serializers.Serializer):
    """Serializer for sending chat messages"""
    session_id = serializers.UUIDField()
    message = serializers.CharField(max_length=10000)
    context = serializers.DictField(required=False, default=dict)
    parent_message_id = serializers.UUIDField(required=False)
    message_type = serializers.ChoiceField(
        choices=Message.MESSAGE_TYPE_CHOICES,
        default='text'
    )

    def validate_message(self, value):
        """Validate message content"""
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip()


class MessageFeedbackSerializer(serializers.Serializer):
    """Serializer for message feedback"""
    message_id = serializers.UUIDField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    feedback = serializers.CharField(max_length=1000, required=False, default='')

    def validate_feedback(self, value):
        """Validate feedback content"""
        return value.strip()


class ChatAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for ChatAnalytics model"""
    
    class Meta:
        model = ChatAnalytics
        fields = [
            'id', 'metric_type', 'metric_value', 'metric_unit',
            'additional_data', 'period_start', 'period_end', 'recorded_at'
        ]
        read_only_fields = ['id', 'recorded_at']


class ChatDashboardSerializer(serializers.Serializer):
    """Serializer for chat dashboard data"""
    active_sessions = ChatSessionSerializer(many=True, read_only=True)
    recent_sessions = ChatSessionSerializer(many=True, read_only=True)
    conversation_summaries = ConversationSummarySerializer(many=True, read_only=True)
    
    # Statistics
    total_sessions = serializers.IntegerField(read_only=True)
    total_messages = serializers.IntegerField(read_only=True)
    avg_session_length = serializers.FloatField(read_only=True)
    avg_satisfaction_rating = serializers.FloatField(read_only=True)
    
    # Usage patterns
    most_used_chat_types = serializers.DictField(read_only=True)
    daily_message_counts = serializers.DictField(read_only=True)
    
    # AI metrics
    avg_response_time = serializers.FloatField(read_only=True)
    total_tokens_used = serializers.IntegerField(read_only=True)
    avg_confidence_score = serializers.FloatField(read_only=True)


class ChatInsightsSerializer(serializers.Serializer):
    """Serializer for chat insights and recommendations"""
    user_communication_patterns = serializers.DictField(read_only=True)
    preferred_topics = serializers.ListField(read_only=True)
    engagement_trends = serializers.DictField(read_only=True)
    ai_performance_metrics = serializers.DictField(read_only=True)
    personalization_opportunities = serializers.ListField(read_only=True)
    recommended_features = serializers.ListField(read_only=True)


class StreamingResponseSerializer(serializers.Serializer):
    """Serializer for streaming chat responses"""
    session_id = serializers.UUIDField(read_only=True)
    message_id = serializers.UUIDField(read_only=True)
    content_chunk = serializers.CharField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    metadata = serializers.DictField(read_only=True)


class ChatContextUpdateSerializer(serializers.Serializer):
    """Serializer for updating chat context"""
    session_id = serializers.UUIDField()
    context_updates = serializers.DictField()
    merge_strategy = serializers.ChoiceField(
        choices=[('replace', 'Replace'), ('merge', 'Merge'), ('append', 'Append')],
        default='merge'
    )

    def validate_context_updates(self, value):
        """Validate context updates"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Context updates must be a dictionary")
        return value


class ChatSearchSerializer(serializers.Serializer):
    """Serializer for searching chat history"""
    query = serializers.CharField(max_length=500)
    chat_type = serializers.ChoiceField(
        choices=ChatSession.CHAT_TYPE_CHOICES,
        required=False
    )
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    include_context = serializers.BooleanField(default=False)
    max_results = serializers.IntegerField(min_value=1, max_value=100, default=20)

    def validate(self, data):
        """Validate search parameters"""
        if data.get('date_from') and data.get('date_to'):
            if data['date_from'] > data['date_to']:
                raise serializers.ValidationError(
                    "date_from must be before date_to"
                )
        return data


class ChatExportSerializer(serializers.Serializer):
    """Serializer for exporting chat data"""
    session_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    export_format = serializers.ChoiceField(
        choices=[('json', 'JSON'), ('csv', 'CSV'), ('txt', 'Text')],
        default='json'
    )
    include_context = serializers.BooleanField(default=True)
    include_analytics = serializers.BooleanField(default=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)

    def validate(self, data):
        """Validate export parameters"""
        if not data.get('session_ids') and not (data.get('date_from') or data.get('date_to')):
            raise serializers.ValidationError(
                "Either session_ids or date range must be provided"
            )
        return data