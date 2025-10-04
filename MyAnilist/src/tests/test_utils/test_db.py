from django.test import TestCase
from src.models import User


class UserModelTest(TestCase):
    """Test cases for User model"""
    
    def test_user_creation(self):
        """Test creating a user with valid data"""
        user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='securepassword123'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertTrue(user.check_password('securepassword123'))
        self.assertFalse(user.email_verified)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIsNotNone(user.date_join)
        self.assertIsNotNone(user.user_id)
    
    def test_user_str_method(self):
        """Test the string representation of user"""
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='password123'
        )
        self.assertEqual(str(user), 'testuser2')
    
    def test_user_email_unique(self):
        """Test that email must be unique"""
        User.objects.create_user(
            username='user1',
            email='duplicate@example.com',
            password='password123'
        )
        
        # Duplicate email should be failed
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='user2',
                email='duplicate@example.com',
                password='password456'
            )
    
    def test_user_password_is_hashed(self):
        """Test that the password is stored as a hash"""
        user = User.objects.create_user(
            username='hashuser',
            email='hashuser@example.com',
            password='password123'
        )
        self.assertNotEqual(user.password, 'password123')
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.check_password('wrongpassword'))
