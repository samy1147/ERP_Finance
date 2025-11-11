"""
Serializers for attachment handling.
"""

from rest_framework import serializers
from .models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    """Serializer for file attachments."""
    
    uploaded_by_name = serializers.CharField(
        source='uploaded_by.username',
        read_only=True
    )
    file_size_display = serializers.CharField(
        source='get_file_size_display',
        read_only=True
    )
    file_extension = serializers.CharField(
        source='get_file_extension',
        read_only=True
    )
    file_url = serializers.CharField(read_only=True)
    
    class Meta:
        model = Attachment
        fields = [
            'id',
            'po_header',
            'pr_header',
            'temp_session',
            'is_temporary',
            'file',
            'file_url',
            'document_type',
            'description',
            'file_size',
            'file_size_display',
            'file_extension',
            'original_filename',
            'uploaded_by',
            'uploaded_by_name',
            'uploaded_at',
        ]
        read_only_fields = [
            'id',
            'file_size',
            'original_filename',
            'uploaded_by',
            'uploaded_at',
        ]
    
    def validate_file(self, value):
        """Validate file size (max 10MB)."""
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size must not exceed 10MB. Current size: {value.size / (1024*1024):.1f}MB"
            )
        return value
    
    def validate(self, data):
        """Ensure either po_header, pr_header, or temp_session is provided."""
        po_header = data.get('po_header')
        pr_header = data.get('pr_header')
        temp_session = data.get('temp_session')
        is_temporary = data.get('is_temporary', False)
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Attachment validation - po_header: {po_header}, pr_header: {pr_header}, "
                   f"temp_session: {temp_session}, is_temporary: {is_temporary}")
        
        # For temporary uploads, temp_session is required
        if is_temporary:
            if not temp_session:
                raise serializers.ValidationError(
                    "temp_session is required for temporary attachments."
                )
            if po_header or pr_header:
                raise serializers.ValidationError(
                    "Temporary attachments cannot have po_header or pr_header."
                )
        else:
            # For permanent attachments, either po_header or pr_header is required (but not both)
            if not po_header and not pr_header:
                raise serializers.ValidationError({
                    "error": "Either po_header or pr_header must be provided for permanent attachments.",
                    "received_data": {
                        "po_header": po_header,
                        "pr_header": pr_header,
                        "is_temporary": is_temporary
                    }
                })
            
            if po_header and pr_header:
                raise serializers.ValidationError(
                    "Cannot attach to both PO and PR simultaneously."
                )
        
        return data


class AttachmentUploadSerializer(serializers.ModelSerializer):
    """Simplified serializer for file upload."""
    
    class Meta:
        model = Attachment
        fields = [
            'file',
            'document_type',
            'description',
        ]
