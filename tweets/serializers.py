from django.core.exceptions import ValidationError
from likes.serializers import LikeSerializer
from comments.serializers import CommentSerializer
from friendships.models import Friendships
from accounts.serializers import UserSerializerForTweet
from rest_framework import serializers
from .models import Tweet
from likes.services import LikeService
from .services import TweetService
from utils.redis_helper import RedisHelper


TWEET_PHOTOS_UPLOAD_LIMIT = 9

class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet(source='cached_user')
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()
    photo_urls = serializers.SerializerMethodField()

    def get_comments_count(self, obj):
        # return obj.comment_set.count()
        return RedisHelper.get_count(obj, 'comments_count')

    def get_likes_count(self, obj):
        # return obj.like_set.count()
        return RedisHelper.get_count(obj, 'likes_count')

    def get_has_liked(self, obj):
        return LikeService.has_liked(self.context['request'].user, obj)

    def get_photo_urls(self, obj):
        photo_urls = []
        for photo in obj.tweetphoto_set.all().order_by('order'):
            photo_urls.append(photo.file.url)
        return photo_urls
    class Meta:
        model = Tweet
        fields = ('id', 'user', 'content', 'created_at', 'likes_count', 'has_liked', 'comments_count', 'photo_urls')

class TweetCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = Tweet
        fields = ('content', 'files')

    def validate(self, data):
        if len(data.get('files', [])) > TWEET_PHOTOS_UPLOAD_LIMIT:
            raise ValidationError({
                'message': f'You can upload {TWEET_PHOTOS_UPLOAD_LIMIT} photos',
            })
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        if validated_data.get('files'):
            TweetService.create_photos_from_files(tweet, validated_data['files'])
        return tweet


class TweetSerializerForDetail(TweetSerializer):
    comments = CommentSerializer(source='comment_set', many=True)
    likes = LikeSerializer(source='like_set', many=True)

    class Meta:
        model = Tweet
        fields = (
            'id', 
            'user', 
            'comments', 
            'created_at', 
            'content', 
            'likes',
            'likes_count',
            'comments_count',
            'has_liked',
            'photo_urls')

