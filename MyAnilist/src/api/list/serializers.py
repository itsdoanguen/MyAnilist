from rest_framework import serializers


class ListCreateSerializer(serializers.Serializer):
    """Serializer for creating a new list."""
    
    list_name = serializers.CharField(
        required=True,
        max_length=255,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            'required': 'List name is required',
            'blank': 'List name cannot be empty',
            'max_length': 'List name cannot exceed 255 characters'
        }
    )
    
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        trim_whitespace=True
    )
    
    is_private = serializers.BooleanField(
        required=False,
        default=True
    )
    
    color = serializers.RegexField(
        regex=r'^#[0-9A-Fa-f]{6}$',
        required=False,
        default='#3498db',
        error_messages={
            'invalid': 'Color must be a valid hex code (e.g., #3498db)'
        }
    )
    
    def validate_list_name(self, value):
        """Additional validation for list name."""
        if not value or not value.strip():
            raise serializers.ValidationError('List name cannot be empty')
        return value.strip()


class ListUpdateSerializer(serializers.Serializer):
    """Serializer for updating an existing list.
    
    All fields are optional. Only provided fields will be updated.
    Note: is_private can only be changed by the list owner.
    """
    
    list_name = serializers.CharField(
        required=False,
        max_length=255,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            'blank': 'List name cannot be empty',
            'max_length': 'List name cannot exceed 255 characters'
        }
    )
    
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True
    )
    
    color = serializers.RegexField(
        regex=r'^#[0-9A-Fa-f]{6}$',
        required=False,
        error_messages={
            'invalid': 'Color must be a valid hex code (e.g., #3498db)'
        }
    )
    
    is_private = serializers.BooleanField(
        required=False,
        help_text='Only the list owner can change this field'
    )
    
    def validate_list_name(self, value):
        """Additional validation for list name."""
        if value is not None and (not value or not value.strip()):
            raise serializers.ValidationError('List name cannot be empty')
        return value.strip() if value else value
