from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MailService:
	"""Simple mail service to send verification emails."""

	def __init__(self):
		self.base_url = getattr(settings, 'BASE_URL', 'https://doannguyen.pythonanywhere.com')

	def send_verification_email(self, user, token: str) -> bool:
		"""Send email containing verification link to the user.

		Returns True on success, False otherwise.
		"""
		try:
			subject = 'Verify your MyAnilist account'
			
			# Frontend URL (primary verification link)
			# Use production URL if not in DEBUG mode, otherwise use local/env URL
			if not getattr(settings, 'DEBUG', False):
				frontend_url = getattr(settings, 'FRONTEND_PRODUCTION_URL', 'https://my-animelist-front.vercel.app')
			else:
				frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
			
			frontend_verify_url = f"{frontend_url}/verify-email?token={token}"
			
			# Backend URL (backup verification link)
			backend_url = getattr(settings, 'BASE_URL', 'https://doannguyen.pythonanywhere.com')
			verify_path = reverse('auth_verify_email')
			backend_verify_url = f"{backend_url}{verify_path}?token={token}"
			logger.debug(f"Verification URLs: frontend={frontend_verify_url}, backend={backend_verify_url}")

			body = (
				f"Hi {user.username},\n\n"
				"Thank you for registering at MyAnilist!\n\n"
				"To complete your registration, please verify your email address by clicking the link below:\n\n"
				f"{frontend_verify_url}\n\n"
				"If the link above doesn't work, you can use this backup link:\n"
				f"{backend_verify_url}\n\n"
				"This link will expire in 24 hours.\n\n"
				"If you didn't create this account, you can safely ignore this email.\n\n"
				"Best regards,\n"
				"The MyAnilist Team"
			)

			email = EmailMessage(
				subject=subject,
				body=body,
				from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@myanilist.com'),
				to=[user.email]
			)
			email.send(fail_silently=False)
			logger.info(f"Sent verification email to {user.email}")
			return True
		except Exception as e:
			logger.exception(f"Failed to send verification email to {getattr(user, 'email', None)}: {e}")
			return False
