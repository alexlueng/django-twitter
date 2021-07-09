from .models import Like
from django.contrib.contenttypes.models import ContentType


class LikeService:

    @classmethod
    def has_liked(self, user, target):
        if user.is_anonymous:
            return False

        return Like.objects.filter(
            user=user,
            content_type=ContentType.objects.get_for_model(target.__class__),
            object_id=target.id
        ).exists()