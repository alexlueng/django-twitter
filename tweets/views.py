from rest_framework import serializers, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Tweet
from .serializers import TweetSerializer, TweetCreateSerializer, TweetSerializerWithComments
from newsfeeds.services import NewsFeedService
from utils.decorator import required_params


class TweetViewSet(viewsets.GenericViewSet, 
                    viewsets.mixins.CreateModelMixin,
                    viewsets.mixins.ListModelMixin):
    queryset = Tweet.objects.all()
    serializer_class = TweetCreateSerializer

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
        return Response(TweetSerializer(tweet).data, status=201)

    # 获取一个用户的所有推文
    @required_params(params=['user_id'])
    def list(self, request, *args, **kwargs):
        # if 'user_id' not in request.query_params:
        #     return Response('missing user_id', status=400)

        tweets = Tweet.objects.filter(user_id=request.query_params['user_id']).order_by('-created_at')
        serializer = TweetSerializer(tweets, many=True)
        return Response({'tweets': serializer.data})


    # 获取一条带评论的tweet
    def retrieve(self, request, *args, **kwargs):
        tweet = self.get_object()
        return Response(TweetSerializerWithComments(tweet).data)