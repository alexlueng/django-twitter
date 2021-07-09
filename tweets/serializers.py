from likes.serializers import LikeSerializer
from comments.serializers import CommentSerializer
from friendships.models import Friendships
from accounts.serializers import UserSerializer
from rest_framework import serializers
from .models import Tweet
from likes.services import LikeService

class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()

    def get_comments_count(self, obj):
        return obj.comment_set.count()

    def get_likes_count(self, obj):
        return obj.like_set.count()

    def get_has_liked(self, obj):
        return LikeService.has_liked(self.context['request'].user, obj)
    class Meta:
        model = Tweet
        fields = ('id', 'user', 'content', 'created_at', 'likes_count', 'has_liked', 'comments_count')

class TweetCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)

    class Meta:
        model = Tweet
        fields = ('content', )

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
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
            'has_liked')

