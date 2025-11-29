from rest_framework import serializers


class AnimeAddSerializer(serializers.Serializer):
    """Serializer for adding an anime to a list."""
    anilist_id = serializers.IntegerField(required=True, min_value=1)
    note = serializers.CharField(required=False, allow_blank=True, default='')


class AnimeNoteUpdateSerializer(serializers.Serializer):
    """Serializer for updating anime note in a list."""
    note = serializers.CharField(required=True, allow_blank=True)
