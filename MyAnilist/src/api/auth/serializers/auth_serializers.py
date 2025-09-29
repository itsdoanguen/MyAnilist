from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for displaying user information
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'email_verified', 'date_join']
        read_only_fields = ['id', 'date_join']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    Handles input validation and data transformation
    """
    password = serializers.CharField(
        write_only=True, 
        required=True,
        min_length=8,
        help_text="Password must be at least 8 characters long"
    )
    confirm_password = serializers.CharField(
        write_only=True, 
        required=True,
        help_text="Confirm your password"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']
        extra_kwargs = {
            'username': {
                'required': True,
                'min_length': 3,
                'help_text': "Username must be at least 3 characters long"
            },
            'email': {
                'required': True,
                'help_text': "Valid email address"
            }
        }

    def validate_email(self, value):
        """
        Validate email uniqueness
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        """
        Validate username format and uniqueness
        """
        if ' ' in value:
            raise serializers.ValidationError("Username cannot contain spaces.")
        
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        
        return value

    def validate_password(self, value):
        """
        Validate password strength using Django validators
        """
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, attrs):
        """
        Validate password confirmation
        """
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': "Passwords do not match."
            })
        return attrs

    def to_representation(self, instance):
        """
        Customize output representation - exclude sensitive data
        """
        return UserSerializer(instance).data


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField(
        required=True,
        help_text="Your registered email address"
    )
    password = serializers.CharField(
        required=True, 
        write_only=True,
        help_text="Your account password"
    )

    def validate(self, attrs):
        """
        Validate login credentials
        """
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        # Authenticate user
        user = authenticate(username=email, password=password)
        
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        
        attrs['user'] = user
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing password
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, 
        write_only=True,
        validators=[validate_password]
    )
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({
                'confirm_new_password': "New passwords do not match."
            })
        return attrs

    def validate_old_password(self, value):
        """
        Validate old password
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value