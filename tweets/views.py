from rest_framework import serializers, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Tweet
from .serializers import TweetSerializer, TweetCreateSerializer, TweetSerializerForDetail
from newsfeeds.services import NewsFeedService
from utils.decorator import required_params
from utils.paginations import EndlessPagination
from .services import TweetService

class TweetViewSet(viewsets.GenericViewSet):
    queryset = Tweet.objects.all()
    serializer_class = TweetCreateSerializer
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    # 用户创建一条推文
    def create(self, request, *args, **kwargs):
        serializer = TweetCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=400)
        tweet = serializer.save()
        NewsFeedService.fanout_to_followers(tweet)
        return Response(TweetSerializer(tweet, context={'request': request}).data, status=201)

    # 获取一个用户的所有推文
    @required_params(params=['user_id'])
    def list(self, request, *args, **kwargs):
        # if 'user_id' not in request.query_params:
        #     return Response('missing user_id', status=400)

        user_id = request.query_params['user_id']
        cached_tweets = TweetService.get_cached_tweets(user_id)

        # tweets = TweetService.get_cached_tweets(user_id=request.query_params['user_id'])
        page = self.paginator.paginate_cached_list(cached_tweets, request)
        if page is None:
            queryset = Tweet.objects.filter(user_id=user_id)
            page = self.paginate_queryset(queryset)
        serializer = TweetSerializer(page, context={'request': request}, many=True)
        return self.get_paginated_response(serializer.data)


    # 获取一条带评论的tweet
    def retrieve(self, request, *args, **kwargs):
        tweet = self.get_object()
        return Response(TweetSerializerForDetail(tweet, context={'request': request}).data)