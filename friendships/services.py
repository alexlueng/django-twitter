from django.core.cache import caches
from .models import Friendships
from django.conf import settings
from core.cache import FOLLOWINGS_PATTERN

cache = caches['testing'] if settings.TESTING else caches['default']

class FriendshipService(object):

    @classmethod
    def get_followers(cls, user):
        friendships = Friendships.objects.filter(to_user=user).prefetch_related('from_user')
        return [friendship.from_user for friendship in friendships ]

    @classmethod
    def get_follower_ids(cls, to_user_id):
        friendships = Friendships.objects.filter(to_user_id=to_user_id)
        return [friendship.from_user_id for friendship in friendships]

    @classmethod
    def get_following_user_id_set(cls, from_user_id):
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        user_id_set = cache.get(key)
        if user_id_set is not None:
            return user_id_set

        friendships = Friendships.objects.filter(from_user_id=from_user_id)
        user_id_set = set([
            fs.to_user_id for fs in friendships
        ])
        cache.set(key, user_id_set)
        return user_id_set

    @classmethod
    def invalidate_following_cache(cls, from_user_id):
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        cache.delete(key)

    