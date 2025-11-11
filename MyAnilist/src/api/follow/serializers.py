from rest_framework import serializers


class FollowSerializer(serializers.Serializer):
    """Serializer for creating/updating an AnimeFollow entry.

    - Parses and validates inputs coming from the client (JSON body).
    - Accepts partial updates when used with `partial=True`.
    """

    notify_email = serializers.BooleanField(required=False)
    episode_progress = serializers.IntegerField(required=False, min_value=0)
    watch_status = serializers.ChoiceField(choices=[], required=False)
    isFavorite = serializers.BooleanField(required=False)
    start_date = serializers.DateField(required=False, allow_null=True)
    finish_date = serializers.DateField(required=False, allow_null=True)
    total_rewatch = serializers.IntegerField(required=False, min_value=0)
    user_note = serializers.CharField(required=False, allow_blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from src.models.anime_follow import AnimeFollow
            self.fields['watch_status'].choices = [c[0] for c in AnimeFollow.WATCH_STATUS_CHOICES]
        except Exception:
            pass

    def validate(self, attrs):
        start = attrs.get('start_date')
        finish = attrs.get('finish_date')
        if start and finish and start > finish:
            raise serializers.ValidationError('finish_date must be the same or after start_date')

        return attrs
