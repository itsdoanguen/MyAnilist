from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core import mail
from src.services.mail_service import MailService

User = get_user_model()


class MailServiceTest(TestCase):
    """Test cases for MailService"""

    def setUp(self):
        """Set up test fixtures"""
        self.mail_service = MailService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = 'test-verification-token-123'

    def test_send_verification_email_success(self):
        """Test sending verification email successfully"""
        result = self.mail_service.send_verification_email(self.user, self.token)
        
        # Check that email was sent successfully
        self.assertTrue(result)
        
        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email details
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, 'Verify your MyAnilist account')
        self.assertEqual(sent_email.to, ['test@example.com'])
        self.assertIn('testuser', sent_email.body)
        self.assertIn(self.token, sent_email.body)

    def test_verification_email_contains_frontend_link(self):
        """Test that email contains frontend verification link"""
        self.mail_service.send_verification_email(self.user, self.token)
        
        sent_email = mail.outbox[0]
        # Default frontend URL should be localhost:3000
        self.assertIn('http://localhost:3000/verify-email?token=', sent_email.body)
        self.assertIn(f'token={self.token}', sent_email.body)

    def test_verification_email_contains_backend_link(self):
        """Test that email contains backend verification link"""
        self.mail_service.send_verification_email(self.user, self.token)
        
        sent_email = mail.outbox[0]
        # Should contain backend URL as backup
        self.assertIn('https://doannguyen.pythonanywhere.com', sent_email.body)
        self.assertIn('backup link', sent_email.body)

    @override_settings(FRONTEND_URL='https://myanilist.com')
    def test_custom_frontend_url(self):
        """Test email with custom frontend URL from settings"""
        mail_service = MailService()
        mail_service.send_verification_email(self.user, self.token)
        
        sent_email = mail.outbox[0]
        self.assertIn('https://myanilist.com/verify-email?token=', sent_email.body)

    @override_settings(BASE_URL='https://custom-backend.com')
    def test_custom_backend_url(self):
        """Test email with custom backend URL from settings"""
        mail_service = MailService()
        mail_service.send_verification_email(self.user, self.token)
        
        sent_email = mail.outbox[0]
        self.assertIn('https://custom-backend.com', sent_email.body)

    def test_email_body_structure(self):
        """Test that email body has correct structure"""
        self.mail_service.send_verification_email(self.user, self.token)
        
        sent_email = mail.outbox[0]
        body = sent_email.body
        
        # Check all required sections
        self.assertIn('Hi testuser', body)
        self.assertIn('Thank you for registering', body)
        self.assertIn('verify your email address', body)
        self.assertIn('expire in 24 hours', body)
        self.assertIn('Best regards', body)
        self.assertIn('MyAnilist Team', body)

    @override_settings(DEFAULT_FROM_EMAIL='custom@myanilist.com')
    def test_custom_from_email(self):
        """Test email with custom from address"""
        mail_service = MailService()
        mail_service.send_verification_email(self.user, self.token)
        
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.from_email, 'custom@myanilist.com')

    def test_send_verification_email_with_special_characters(self):
        """Test sending email to user with special characters in username"""
        special_user = User.objects.create_user(
            username='test_user-123',
            email='special@example.com',
            password='testpass123'
        )
        
        result = self.mail_service.send_verification_email(special_user, self.token)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIn('test_user-123', sent_email.body)
