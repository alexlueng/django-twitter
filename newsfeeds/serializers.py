from rest_framework import serializers
from .models import NewsFeed
from tweets.serializers import TweetSerializer

class NewsFeedSerializer(serializers.ModelSerializer):
    tweet = TweetSerializer(source='cached_tweet')

    class Meta:
        model = NewsFeed
        fields = ('id', 'created_at', 'user', 'tweet')
