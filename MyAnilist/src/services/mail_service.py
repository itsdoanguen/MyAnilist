from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MailService:
	"""Simple mail service to send verification emails."""

	def __init__(self):
		self.frontend_url = getattr(settings, 'FRONT_END_URL', None) or getattr(settings, 'FRONTEND_URL', None) or 'http://localhost:3000'

	def send_verification_email(self, user, token: str) -> bool:
		"""Send email containing verification link to the user.

		Returns True on success, False otherwise.
		"""
		try:
			subject = 'Verify your MyAnilist account'
			frontend_verify = f"{self.frontend_url}/verify-email?token={token}"

			# Fallback to backend path
			backend_path = reverse('auth_verify_email')
			backend_host = getattr(settings, 'BACKEND_BASE_URL', None) or 'http://localhost:8000'
			backend_verify = f"{backend_host}{backend_path}?token={token}"

			body = (
				f"Hi {user.username},\n\n"
				"Thanks for registering at MyAnilist. Please verify your email by clicking the link below:\n\n"
				f"{frontend_verify}\n\n"
				"If your frontend does not handle verification, use this link:\n\n"
				f"{backend_verify}\n\n"
				"If you didn't create an account, you can ignore this message.\n\n"
				"Regards,\nMyAnilist Team"
			)

			email = EmailMessage(
				subject=subject,
				body=body,
				from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
				to=[user.email]
			)
			email.send(fail_silently=False)
			logger.info(f"Sent verification email to {user.email}")
			return True
		except Exception as e:
			logger.exception(f"Failed to send verification email to {getattr(user, 'email', None)}: {e}")
			return False
