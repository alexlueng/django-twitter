from .serializers import FollowerSerializer, FollowingSerializer, FriendshipSerializerForCreate
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.decorators import action
from .models import Friendships
from .paginations import FriendshipsPagination
from .services import FriendshipService

# 这个view主要实现4个功能：我关注的人，关注我的人，关注某人，取消关注

class FriendshipViewSet(viewsets.GenericViewSet):
    # post /api/friendship/1/follow user_id=1
    # queryset = User.objects.all()
    # 如果是Friendships.objects.all() 会出现404
    serializer_class = FriendshipSerializerForCreate
    queryset = User.objects.all()
    pagination_class = FriendshipsPagination
    
    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followers(self, request, pk):
        friendships = Friendships.objects.filter(to_user_id=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowerSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followings(self, request, pk):
        friendships = Friendships.objects.filter(from_user_id=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowingSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def follow(self, request, pk):
        if Friendships.objects.filter(from_user=request.user, to_user=pk).exists():
            return Response({
                'success': True,
                'duplicate': True,
            }, status=status.HTTP_201_CREATED)

        serializer = FriendshipSerializerForCreate(data={
            'from_user_id': request.user.id,
            'to_user_id': pk,
        })
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        # FriendshipService.invalidate_following_cache(request.user.id)
        return Response({
                'success': True,
            }, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk):
        if request.user.id == int(pk):
            return Response({
                'success': False,
                'message': 'You cannot unfollow yourself.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted, _ = Friendships.objects.filter(from_user=request.user, to_user=pk).delete()
        # FriendshipService.invalidate_following_cache(request.user.id)
        return Response({
                'success': True,
                'deleted': deleted,
            })