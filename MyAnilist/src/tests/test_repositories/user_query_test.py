from django.test import TestCase
from src.models.user import User

class UserQueryTest(TestCase):
    """Test cases for querying User model"""
    
    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username='queryuser1',
            email='queryuser1@example.com',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            username='queryuser2',
            email='queryuser2@example.com',
            password='password456'
        )

    def test_get_user_by_email(self):
        """Test retrieving a user by email"""
        user = User.objects.get(email='queryuser1@example.com')
        self.assertEqual(user.username, 'queryuser1')
        self.assertEqual(user.email, 'queryuser1@example.com')