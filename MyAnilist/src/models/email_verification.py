from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from datetime import timedelta


class EmailVerification(models.Model):
    """
    Stores a one-time token used to verify a user's email address.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_verifications')
    token = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'email_verifications'
        verbose_name = 'Email Verification'
        verbose_name_plural = 'Email Verifications'

    def save(self, *args, **kwargs):
        # generate token if not present
        if not self.token:
            self.token = uuid.uuid4().hex

        # set default expiry from settings if not provided
        if not self.expires_at:
            hours = getattr(settings, 'EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS', None)
            if hours is None:
                # fallback older/alternate name
                hours = int(getattr(settings, 'DEFAULT_EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS', 12))
            self.expires_at = self.created_at + timedelta(hours=int(hours))

        super().save(*args, **kwargs)

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def __str__(self) -> str:
        return f"EmailVerification(token={self.token}, user={self.user})"
