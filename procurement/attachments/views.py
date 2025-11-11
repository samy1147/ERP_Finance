"""
API views for attachment handling.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from .models import Attachment
from .serializers import AttachmentSerializer, AttachmentUploadSerializer


class AttachmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing attachments.
    """
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def get_queryset(self):
        """Filter attachments based on query parameters."""
        queryset = Attachment.objects.all()
        
        po_id = self.request.query_params.get('po_header', None)
        pr_id = self.request.query_params.get('pr_header', None)
        temp_session = self.request.query_params.get('temp_session', None)
        
        if po_id:
            queryset = queryset.filter(po_header_id=po_id, is_temporary=False)
        elif pr_id:
            queryset = queryset.filter(pr_header_id=pr_id, is_temporary=False)
        elif temp_session:
            queryset = queryset.filter(temp_session=temp_session, is_temporary=True)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set uploaded_by to current user."""
        # Only set uploaded_by if user is authenticated
        uploaded_by = self.request.user if self.request.user.is_authenticated else None
        serializer.save(uploaded_by=uploaded_by)
    
    @action(detail=False, methods=['post'], url_path='upload-po')
    def upload_po(self, request):
        """
        Upload attachment for a Purchase Order.
        
        POST /api/procurement/attachments/upload-po/
        Body: {
            "po_header": 123,
            "file": <file>,
            "document_type": "QUOTE",
            "description": "Vendor quote"
        }
        """
        po_id = request.data.get('po_header')
        if not po_id:
            return Response(
                {'error': 'po_header is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AttachmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(uploaded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='upload-pr')
    def upload_pr(self, request):
        """
        Upload attachment for a Purchase Requisition.
        
        POST /api/procurement/attachments/upload-pr/
        Body: {
            "pr_header": 456,
            "file": <file>,
            "document_type": "SPEC",
            "description": "Technical specifications"
        }
        """
        pr_id = request.data.get('pr_header')
        if not pr_id:
            return Response(
                {'error': 'pr_header is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AttachmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(uploaded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='upload-temp')
    def upload_temp(self, request):
        """
        Upload temporary attachment (before PO/PR is created).
        
        POST /api/procurement/attachments/upload-temp/
        Body: {
            "temp_session": "unique-session-id",
            "file": <file>,
            "document_type": "QUOTE",
            "description": "Vendor quote"
        }
        """
        temp_session = request.data.get('temp_session')
        if not temp_session:
            return Response(
                {'error': 'temp_session is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add is_temporary flag
        data = request.data.copy()
        data['is_temporary'] = True
        
        serializer = AttachmentSerializer(data=data)
        if serializer.is_valid():
            uploaded_by = request.user if request.user.is_authenticated else None
            serializer.save(uploaded_by=uploaded_by)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='link-to-po', parser_classes=[JSONParser])
    def link_to_po(self, request):
        """
        Link temporary attachments to a Purchase Order.
        
        POST /api/procurement/attachments/link-to-po/
        Body: {
            "temp_session": "unique-session-id",
            "po_header": 123
        }
        """
        temp_session = request.data.get('temp_session')
        po_id = request.data.get('po_header')
        
        if not temp_session or not po_id:
            return Response(
                {'error': 'Both temp_session and po_header are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find and update all temporary attachments
        attachments = Attachment.objects.filter(
            temp_session=temp_session,
            is_temporary=True
        )
        
        count = attachments.update(
            po_header_id=po_id,
            is_temporary=False,
            temp_session=None
        )
        
        return Response({
            'message': f'Successfully linked {count} attachment(s) to PO',
            'count': count
        })
    
    @action(detail=False, methods=['post'], url_path='link-to-pr', parser_classes=[JSONParser])
    def link_to_pr(self, request):
        """
        Link temporary attachments to a Purchase Requisition.
        
        POST /api/procurement/attachments/link-to-pr/
        Body: {
            "temp_session": "unique-session-id",
            "pr_header": 456
        }
        """
        temp_session = request.data.get('temp_session')
        pr_id = request.data.get('pr_header')
        
        if not temp_session or not pr_id:
            return Response(
                {'error': 'Both temp_session and pr_header are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find and update all temporary attachments
        attachments = Attachment.objects.filter(
            temp_session=temp_session,
            is_temporary=True
        )
        
        count = attachments.update(
            pr_header_id=pr_id,
            is_temporary=False,
            temp_session=None
        )
        
        return Response({
            'message': f'Successfully linked {count} attachment(s) to PR',
            'count': count
        })
    
    @action(detail=False, methods=['post'], url_path='cleanup-temp', parser_classes=[JSONParser])
    def cleanup_temp(self, request):
        """
        Clean up old temporary attachments (older than 24 hours).
        
        POST /api/procurement/attachments/cleanup-temp/
        """
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        old_attachments = Attachment.objects.filter(
            is_temporary=True,
            uploaded_at__lt=cutoff_time
        )
        
        count = old_attachments.count()
        
        # Delete files
        for attachment in old_attachments:
            if attachment.file:
                attachment.file.delete()
        
        # Delete records
        old_attachments.delete()
        
        return Response({
            'message': f'Cleaned up {count} temporary attachment(s)',
            'count': count
        })
