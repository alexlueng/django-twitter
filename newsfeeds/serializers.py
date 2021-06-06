from rest_framework import serializers
from .models import NewsFeed
from tweets.serializers import TweetSerializer

class NewsFeedSerializer(serializers.ModelSerializer):
    tweet = TweetSerializer()

    class Meta:
        model = NewsFeed
        fields = ('id', 'created_at', 'user', 'tweet')
