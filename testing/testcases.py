from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User
from tweets.models import Tweet
from comments.models import Comment
from likes.models import Like
from newsfeeds.models import NewsFeed
from django.contrib.contenttypes.models import ContentType
from django.core.cache import caches

from rest_framework.test import APIClient

class TestCase(DjangoTestCase):

    @property
    def anonymous_client(self):
        if hasattr(self, '_anonymous_client'):
            return self._anonymous_client
        self._anonymous_client = APIClient()
        return self._anonymous_client

    def clear_cache(self):
        caches['testing'].clear()

    def create_user(self, username, email=None, password=None):
        if password is None:
            password = '123456'
        if email is None:
            email = '{}@example.com'.format(username)
        return User.objects.create_user(username, email, password)

    def create_tweet(self, user, content=None):
        if content is None:
            content = 'default content'
        return Tweet.objects.create(user=user, content=content)

    def create_comment(self, user, tweet, content=None):
        if content is None:
            content = 'default content'

        return Comment.objects.create(
            user=user,
            tweet=tweet,
            content=content
        )

    def create_like(self, user, target):
        instance, _ = Like.objects.get_or_create(
            user=user,
            content_type=ContentType.objects.get_for_model(target.__class__),
            object_id=target.id,
        )
        return instance

    def create_newsfeed(self, user, tweet):
        return NewsFeed.objects.create(user=user, tweet=tweet)