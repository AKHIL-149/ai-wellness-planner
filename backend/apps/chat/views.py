# backend/apps/chat/views.py

import logging
import json
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q, Avg, Sum, Count
from django.http import StreamingHttpResponse
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .models import (
    ChatSession, Message, ChatContext, ChatTemplate,
    ConversationSummary, ChatAnalytics
)
from .serializers import (
    ChatSessionSerializer, ChatSessionCreateSerializer, MessageSerializer,
    MessageCreateSerializer, ChatContextSerializer, ChatTemplateSerializer,
    ConversationSummarySerializer, ChatStartSerializer, ChatMessageSerializer,
    MessageFeedbackSerializer, ChatDashboardSerializer, ChatInsightsSerializer,
    ChatSearchSerializer, ChatExportSerializer, ChatContextUpdateSerializer
)
from .services import (
    ChatService, ChatContextService, ChatAnalyticsService,
    ConversationSummaryService
)

logger = logging.getLogger(__name__)


class ChatSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for chat session management"""
    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['chat_type', 'status']
    
    def get_queryset(self):
        """Return chat sessions for the authenticated user"""
        queryset = ChatSession.objects.filter(user=self.request.user)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset.order_by('-last_activity')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ChatSessionCreateSerializer
        return ChatSessionSerializer
    
    def perform_create(self, serializer):
        """Set the user when creating a chat session"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a chat session"""
        session = self.get_object()
        session.status = 'archived'
        session.save()
        
        return Response({
            'message': 'Chat session archived successfully',
            'session_id': str(session.id)
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore an archived chat session"""
        session = self.get_object()
        session.status = 'active'
        session.save()
        
        return Response({
            'message': 'Chat session restored successfully',
            'session_id': str(session.id)
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages for a chat session"""
        session = self.get_object()
        messages = session.messages.order_by('created_at')
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 50))
        page = int(request.query_params.get('page', 1))
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_messages = messages[start_idx:end_idx]
        serializer = MessageSerializer(paginated_messages, many=True)
        
        return Response({
            'messages': serializer.data,
            'total_count': messages.count(),
            'page': page,
            'page_size': page_size,
            'has_next': end_idx < messages.count()
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def context(self, request, pk=None):
        """Get context data for a chat session"""
        session = self.get_object()
        context_items = session.context_items.filter(
            expires_at__gte=timezone.now()
        ).order_by('-importance_score')
        
        serializer = ChatContextSerializer(context_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def generate_summary(self, request, pk=None):
        """Generate a summary for the chat session"""
        session = self.get_object()
        
        summary_service = ConversationSummaryService()
        result = summary_service.generate_session_summary(session)
        
        if result['success']:
            return Response({
                'message': 'Summary generated successfully',
                'summary_id': result['summary_id'],
                'summary': result['summary']
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for message management"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return messages for the authenticated user's sessions"""
        return Message.objects.filter(session__user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    @action(detail=True, methods=['post'])
    def add_feedback(self, request, pk=None):
        """Add user feedback to a message"""
        message = self.get_object()
        
        if message.role != 'assistant':
            return Response(
                {'error': 'Feedback can only be added to AI messages'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = MessageFeedbackSerializer(data=request.data)
        if serializer.is_valid():
            chat_service = ChatService()
            result = chat_service.add_message_feedback(
                message_id=str(message.id),
                user=request.user,
                feedback_data=serializer.validated_data
            )
            
            if result['success']:
                return Response({
                    'message': result['message']
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_chat(request):
    """Start a new chat session"""
    serializer = ChatStartSerializer(data=request.data)
    if serializer.is_valid():
        chat_service = ChatService()
        result = chat_service.start_chat_session(
            user=request.user,
            initial_data=serializer.validated_data
        )
        
        if result['success']:
            return Response({
                'session_id': result['session_id'],
                'initial_response': result['initial_response'],
                'session_title': result['session_title']
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_message(request):
    """Send a message in a chat session"""
    serializer = ChatMessageSerializer(data=request.data)
    if serializer.is_valid():
        chat_service = ChatService()
        result = chat_service.send_message(
            session_id=str(serializer.validated_data['session_id']),
            user=request.user,
            message_data=serializer.validated_data
        )
        
        if result['success']:
            return Response({
                'user_message_id': result['user_message_id'],
                'ai_response': result['ai_response']
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def stream_message(request):
    """Send a message and stream the AI response"""
    serializer = ChatMessageSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def generate_stream():
        chat_service = ChatService()
        
        try:
            for chunk in chat_service.stream_ai_response(
                session_id=str(serializer.validated_data['session_id']),
                user=request.user,
                message_data=serializer.validated_data
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
                
                if chunk.get('is_complete', False):
                    break
                    
        except Exception as e:
            error_chunk = {
                'error': str(e),
                'is_complete': True
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    response = StreamingHttpResponse(
        generate_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    response['Access-Control-Allow-Origin'] = '*'
    
    return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_context(request):
    """Update context for a chat session"""
    serializer = ChatContextUpdateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            session = ChatSession.objects.get(
                id=serializer.validated_data['session_id'],
                user=request.user
            )
            
            context_service = ChatContextService()
            
            # Update context based on merge strategy
            merge_strategy = serializer.validated_data['merge_strategy']
            context_updates = serializer.validated_data['context_updates']
            
            if merge_strategy == 'replace':
                session.context_data = context_updates
            elif merge_strategy == 'merge':
                session.context_data.update(context_updates)
            elif merge_strategy == 'append':
                for key, value in context_updates.items():
                    if key in session.context_data:
                        if isinstance(session.context_data[key], list):
                            session.context_data[key].extend(value if isinstance(value, list) else [value])
                        else:
                            session.context_data[key] = [session.context_data[key], value]
                    else:
                        session.context_data[key] = value
            
            session.save()
            
            return Response({
                'message': 'Context updated successfully',
                'updated_context': session.context_data
            }, status=status.HTTP_200_OK)
            
        except ChatSession.DoesNotExist:
            return Response({
                'error': 'Chat session not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def chat_dashboard(request):
    """Get comprehensive chat dashboard data"""
    user = request.user
    
    try:
        # Get active sessions
        active_sessions = ChatSession.objects.filter(
            user=user,
            status='active'
        ).order_by('-last_activity')[:5]
        
        # Get recent sessions
        recent_sessions = ChatSession.objects.filter(
            user=user
        ).order_by('-last_activity')[:10]
        
        # Get conversation summaries
        recent_summaries = ConversationSummary.objects.filter(
            user=user
        ).order_by('-created_at')[:5]
        
        # Calculate statistics
        total_sessions = ChatSession.objects.filter(user=user).count()
        
        total_messages = Message.objects.filter(
            session__user=user
        ).count()
        
        avg_session_length = ChatSession.objects.filter(
            user=user
        ).aggregate(
            avg_length=Avg('message_count')
        )['avg_length'] or 0
        
        avg_satisfaction = ChatSession.objects.filter(
            user=user,
            satisfaction_rating__isnull=False
        ).aggregate(
            avg_rating=Avg('satisfaction_rating')
        )['avg_rating'] or 0
        
        # Usage patterns
        chat_type_usage = ChatSession.objects.filter(
            user=user
        ).values('chat_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        most_used_chat_types = {
            item['chat_type']: item['count'] for item in chat_type_usage
        }
        
        # Daily message counts (last 7 days)
        daily_messages = {}
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = Message.objects.filter(
                session__user=user,
                created_at__date=date,
                role='user'
            ).count()
            daily_messages[date.strftime('%Y-%m-%d')] = count
        
        # AI metrics
        ai_messages = Message.objects.filter(
            session__user=user,
            role='assistant'
        )
        
        avg_response_time = ai_messages.aggregate(
            avg_time=Avg('response_time_ms')
        )['avg_time'] or 0
        
        total_tokens = ai_messages.aggregate(
            total=Sum('total_tokens')
        )['total'] or 0
        
        avg_confidence = ai_messages.filter(
            confidence_score__isnull=False
        ).aggregate(
            avg_conf=Avg('confidence_score')
        )['avg_conf'] or 0
        
        # Serialize dashboard data
        dashboard_data = {
            'active_sessions': ChatSessionSerializer(active_sessions, many=True).data,
            'recent_sessions': ChatSessionSerializer(recent_sessions, many=True).data,
            'conversation_summaries': ConversationSummarySerializer(recent_summaries, many=True).data,
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'avg_session_length': round(avg_session_length, 1),
            'avg_satisfaction_rating': round(avg_satisfaction, 1),
            'most_used_chat_types': most_used_chat_types,
            'daily_message_counts': daily_messages,
            'avg_response_time': round(avg_response_time, 1),
            'total_tokens_used': total_tokens,
            'avg_confidence_score': round(avg_confidence, 2)
        }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating chat dashboard: {str(e)}")
        return Response(
            {'error': 'Failed to generate dashboard data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def chat_insights(request):
    """Get AI-generated chat insights and recommendations"""
    user = request.user
    period_days = int(request.query_params.get('period_days', 30))
    
    try:
        analytics_service = ChatAnalyticsService()
        result = analytics_service.generate_user_insights(user, period_days)
        
        if result['success']:
            return Response(result['insights'], status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Error generating chat insights: {str(e)}")
        return Response(
            {'error': 'Failed to generate insights'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def search_conversations(request):
    """Search through chat history"""
    serializer = ChatSearchSerializer(data=request.data)
    if serializer.is_valid():
        try:
            query = serializer.validated_data['query']
            chat_type = serializer.validated_data.get('chat_type')
            date_from = serializer.validated_data.get('date_from')
            date_to = serializer.validated_data.get('date_to')
            include_context = serializer.validated_data.get('include_context', False)
            max_results = serializer.validated_data.get('max_results', 20)
            
            # Build search query
            messages_query = Message.objects.filter(
                session__user=request.user
            )
            
            # Text search
            messages_query = messages_query.filter(
                Q(content__icontains=query)
            )
            
            # Filter by chat type
            if chat_type:
                messages_query = messages_query.filter(
                    session__chat_type=chat_type
                )
            
            # Date range filter
            if date_from:
                messages_query = messages_query.filter(
                    created_at__gte=date_from
                )
            if date_to:
                messages_query = messages_query.filter(
                    created_at__lte=date_to
                )
            
            # Execute search
            search_results = messages_query.order_by('-created_at')[:max_results]
            
            # Prepare results
            results = []
            for message in search_results:
                result = {
                    'message_id': str(message.id),
                    'session_id': str(message.session.id),
                    'session_title': message.session.title,
                    'content': message.content,
                    'role': message.role,
                    'message_type': message.message_type,
                    'created_at': message.created_at.isoformat(),
                    'chat_type': message.session.chat_type
                }
                
                if include_context:
                    result['context_data'] = message.context_data
                
                results.append(result)
            
            return Response({
                'results': results,
                'total_found': len(results),
                'query': query,
                'search_params': {
                    'chat_type': chat_type,
                    'date_from': date_from.isoformat() if date_from else None,
                    'date_to': date_to.isoformat() if date_to else None
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error searching conversations: {str(e)}")
            return Response(
                {'error': 'Search failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def export_chat_data(request):
    """Export chat data in various formats"""
    serializer = ChatExportSerializer(data=request.data)
    if serializer.is_valid():
        try:
            export_format = serializer.validated_data['export_format']
            session_ids = serializer.validated_data.get('session_ids', [])
            include_context = serializer.validated_data.get('include_context', True)
            include_analytics = serializer.validated_data.get('include_analytics', False)
            date_from = serializer.validated_data.get('date_from')
            date_to = serializer.validated_data.get('date_to')
            
            # Build query
            sessions_query = ChatSession.objects.filter(user=request.user)
            
            if session_ids:
                sessions_query = sessions_query.filter(id__in=session_ids)
            
            if date_from:
                sessions_query = sessions_query.filter(created_at__gte=date_from)
            if date_to:
                sessions_query = sessions_query.filter(created_at__lte=date_to)
            
            sessions = sessions_query.order_by('-created_at')
            
            # Prepare export data
            export_data = {
                'export_info': {
                    'user_id': str(request.user.id),
                    'username': request.user.username,
                    'export_date': timezone.now().isoformat(),
                    'format': export_format,
                    'total_sessions': sessions.count()
                },
                'sessions': []
            }
            
            for session in sessions:
                session_data = {
                    'session_id': str(session.id),
                    'title': session.title,
                    'chat_type': session.chat_type,
                    'status': session.status,
                    'created_at': session.created_at.isoformat(),
                    'last_activity': session.last_activity.isoformat(),
                    'message_count': session.message_count,
                    'messages': []
                }
                
                # Add messages
                for message in session.messages.order_by('created_at'):
                    message_data = {
                        'message_id': str(message.id),
                        'role': message.role,
                        'content': message.content,
                        'message_type': message.message_type,
                        'created_at': message.created_at.isoformat()
                    }
                    
                    if include_context:
                        message_data['context_data'] = message.context_data
                        message_data['structured_data'] = message.structured_data
                    
                    if message.user_rating:
                        message_data['user_rating'] = message.user_rating
                        message_data['user_feedback'] = message.user_feedback
                    
                    session_data['messages'].append(message_data)
                
                # Add context if requested
                if include_context:
                    session_data['context_items'] = [
                        {
                            'context_type': ctx.context_type,
                            'key': ctx.key,
                            'value': ctx.value,
                            'importance_score': ctx.importance_score
                        }
                        for ctx in session.context_items.all()
                    ]
                
                # Add analytics if requested
                if include_analytics:
                    session_data['analytics'] = {
                        'avg_response_time': session.avg_response_time,
                        'total_tokens_used': session.total_tokens_used,
                        'satisfaction_rating': session.satisfaction_rating
                    }
                
                export_data['sessions'].append(session_data)
            
            # Format response based on export format
            if export_format == 'json':
                return Response(export_data, status=status.HTTP_200_OK)
            
            elif export_format == 'csv':
                # Convert to CSV format (simplified)
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write headers
                headers = ['Session ID', 'Session Title', 'Chat Type', 'Message Role', 
                          'Message Content', 'Created At']
                writer.writerow(headers)
                
                # Write data
                for session in export_data['sessions']:
                    for message in session['messages']:
                        writer.writerow([
                            session['session_id'],
                            session['title'],
                            session['chat_type'],
                            message['role'],
                            message['content'][:500],  # Truncate long content
                            message['created_at']
                        ])
                
                csv_data = output.getvalue()
                output.close()
                
                return Response({
                    'format': 'csv',
                    'data': csv_data,
                    'filename': f"chat_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }, status=status.HTTP_200_OK)
            
            elif export_format == 'txt':
                # Convert to readable text format
                text_lines = []
                text_lines.append(f"Chat Export for {request.user.username}")
                text_lines.append(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
                text_lines.append("=" * 50)
                text_lines.append("")
                
                for session in export_data['sessions']:
                    text_lines.append(f"Session: {session['title']}")
                    text_lines.append(f"Type: {session['chat_type']}")
                    text_lines.append(f"Created: {session['created_at']}")
                    text_lines.append("-" * 30)
                    
                    for message in session['messages']:
                        role_label = "You" if message['role'] == 'user' else "AI Assistant"
                        text_lines.append(f"{role_label}: {message['content']}")
                        text_lines.append("")
                    
                    text_lines.append("=" * 50)
                    text_lines.append("")
                
                text_content = "\n".join(text_lines)
                
                return Response({
                    'format': 'txt',
                    'data': text_content,
                    'filename': f"chat_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.txt"
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error exporting chat data: {str(e)}")
            return Response(
                {'error': 'Export failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for chat templates"""
    queryset = ChatTemplate.objects.filter(is_active=True)
    serializer_class = ChatTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['template_type', 'personalization_level']
    
    def get_queryset(self):
        """Filter templates based on user needs"""
        queryset = super().get_queryset()
        
        # Filter by template type
        template_type = self.request.query_params.get('template_type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        
        return queryset.order_by('template_type', 'name')
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Use a template to start a chat or generate content"""
        template = self.get_object()
        
        # Track template usage
        template.track_usage(success=True)
        
        # Get user context for personalization
        context_data = request.data.get('context', {})
        
        # Build personalized prompt (placeholder implementation)
        personalized_prompt = template.prompt_template.format(**context_data)
        
        return Response({
            'template_id': str(template.id),
            'personalized_prompt': personalized_prompt,
            'example_response': template.example_response
        }, status=status.HTTP_200_OK)


class ConversationSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for conversation summaries"""
    serializer_class = ConversationSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['summary_type']
    
    def get_queryset(self):
        """Return summaries for the authenticated user"""
        queryset = ConversationSummary.objects.filter(user=self.request.user)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(period_start__gte=start_date)
        if end_date:
            queryset = queryset.filter(period_end__lte=end_date)
        
        return queryset.order_by('-period_end')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def chat_analytics(request):
    """Get detailed chat analytics"""
    user = request.user
    period_days = int(request.query_params.get('period_days', 30))
    
    try:
        start_date = timezone.now() - timedelta(days=period_days)
        
        # Get analytics data
        analytics = ChatAnalytics.objects.filter(
            user=user,
            recorded_at__gte=start_date
        )
        
        # Group by metric type
        analytics_by_type = {}
        for metric_type, _ in ChatAnalytics.METRIC_TYPE_CHOICES:
            metric_analytics = analytics.filter(metric_type=metric_type)
            
            if metric_analytics.exists():
                analytics_by_type[metric_type] = {
                    'average_value': metric_analytics.aggregate(
                        avg=Avg('metric_value')
                    )['avg'],
                    'total_records': metric_analytics.count(),
                    'trend_data': [
                        {
                            'date': item.recorded_at.date().isoformat(),
                            'value': item.metric_value,
                            'unit': item.metric_unit
                        }
                        for item in metric_analytics.order_by('recorded_at')
                    ]
                }
        
        return Response({
            'period_days': period_days,
            'analytics_by_type': analytics_by_type,
            'total_analytics_records': analytics.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating chat analytics: {str(e)}")
        return Response(
            {'error': 'Failed to generate analytics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )