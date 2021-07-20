from tweets.constants import TWEET_PHOTO_STATUS_CHOICES, TweetPhotoStatus
from django.db import models
from django.contrib.auth.models import User
from likes.models import Like
from django.contrib.contenttypes.models import ContentType
from utils.time_helpers import utc_now
from utils.memcached_helper import MemcachedHelper
from django.db.models.signals import post_save, pre_delete
from utils.listeners import invalidate_object_cache

class Tweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (('user', 'created_at'),)
        ordering = ('user', '-created_at')

    @property
    def hours_to_now(self):
        return (utc_now() - self.created_at).seconds // 3600

    def __str__(self):
        return f'{self.created_at} {self.user}: {self.content}'

    @property
    def like_set(self):
        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Tweet),
            object_id=self.id,
        ).order_by('-created_at')

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.user_id)

class TweetPhoto(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    file = models.FileField()
    order = models.IntegerField(default=0)

    status = models.IntegerField(
        default=TweetPhotoStatus.PENDING,
        choices=TWEET_PHOTO_STATUS_CHOICES,
    )

    has_deleted = models.BooleanField(default=False) # 软删除，真正的删除在后台异步执行
    deleted_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        index_together = (
            ('user', 'created_at'),
            ('has_deleted', 'created_at'),
            ('status', 'created_at'),
            ('tweet', 'order'),
        )

    def __srt__(self):
        return f'{self.tweet_id}: {self.file}'


pre_delete.connect(invalidate_object_cache, sender=Tweet)
post_save.connect(invalidate_object_cache, sender=Tweet)