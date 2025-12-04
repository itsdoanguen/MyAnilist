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
			
			# Frontend URL (primary verification link) - Always use production URL
			frontend_url = getattr(settings, 'FRONTEND_PRODUCTION_URL', 'https://my-animelist-front.vercel.app')
			frontend_verify_url = f"{frontend_url}/verify-email?token={token}"
			
			logger.info(f"Verification URL: {frontend_verify_url}")

			body = (
				f"Hi {user.username},\n\n"
				"Thank you for registering at MyAnilist!\n\n"
				"To complete your registration, please verify your email address by clicking the link below:\n\n"
				f"{frontend_verify_url}\n\n"
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

	def send_anime_airing_notification(
		self, 
		user, 
		anime_title: str, 
		episode_number: int, 
		airing_at, 
		hours_until_airing: int, 
		cover_image: str = '', 
		anilist_id: int = 0
	) -> bool:
		"""
		Send notification about upcoming anime episode.

		Args:
			user: User instance
			anime_title: Title of the anime
			episode_number: Episode number
			airing_at: DateTime when episode airs
			hours_until_airing: Hours until airing
			cover_image: URL to anime cover image
			anilist_id: AniList anime ID

		Returns:
			True on success, False otherwise
		"""
		try:
			subject = f"🎬 {anime_title} - Episode {episode_number} airs in {hours_until_airing}h!"
			
			airing_time = airing_at.strftime('%B %d, %Y at %H:%M')
			frontend_url = getattr(settings, 'FRONTEND_PRODUCTION_URL', 'https://my-animelist-front.vercel.app')
			
			body = (
				f"Hello {user.username},\n\n"
				f"The next episode of \"{anime_title}\" is airing soon! 🍿\n\n"
				f"Episode: {episode_number}\n"
				f"Airing Time: {airing_time}\n"
				f"Time Until Airing: {hours_until_airing} hours\n\n"
				"Don't miss it!\n\n"
				f"View on MyAniList: {frontend_url}/anime/{anilist_id}\n"
				f"View on AniList: https://anilist.co/anime/{anilist_id}\n\n"
				"---\n"
				"You're receiving this because you're following this anime.\n"
				f"Manage notification settings: {frontend_url}/settings/notifications\n\n"
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
			logger.info(f"Sent anime airing notification to {user.email} for {anime_title} Ep {episode_number}")
			return True
		except Exception as e:
			logger.exception(f"Failed to send anime airing notification to {getattr(user, 'email', None)}: {e}")
			return False
