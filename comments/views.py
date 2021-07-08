from .models import Comment
from rest_framework import serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import CommentSerializerForCreate,\
                        CommentSerializer,\
                        CommentSerializerForUpdate
from .permissions import IsObjectOwner


# POST    /api/comments/ -> create
# GET     /api/comments/?tweet_id=1 -> list
# GET     /api/comments/1/ -> retrieve 
# DELETE  /api/comments/1/ -> destroy 
# PATCH   /api/commnets/1/ -> partial_update
# PUT     /api/comments/1/ -> update

class CommentViewSet(viewsets.GenericViewSet):
    """
        只实现 list, create, update, destroy方法
        不实现 retrieve（查询单个comment）的方法，因为没有这个需求
    """
    serializer_class = CommentSerializerForCreate
    queryset = Comment.objects.all()
    filterset_fields = ('tweet_id',)

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['destroy', 'update']:
            return [IsObjectOwner(), IsAuthenticated()]
        return [AllowAny()]


    def list(self, request, *args, **kwargs):
        if 'tweet_id' not in request.query_params:
            return Response({
                'message': 'missing tweet_id in request',
                'success': False,
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset()
        comments = self.filter_queryset(queryset).order_by('created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response({'comments': serializer.data}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        # 1. 获取传过来的参数
        # 2. 序列化验证参数是否合法
        # 3. 返回对应的状态码给客户端

        # 1
        data = {
            'user_id': request.user.id,
            'tweet_id': request.data.get('tweet_id'),
            'content': request.data.get('content'),
        }

        # 2
        serializer = CommentSerializerForCreate(data=data)

        # 3
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors, 
            }, status=status.HTTP_400_BAD_REQUEST)

        comment = serializer.save()
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        serializer = CommentSerializerForUpdate(
            instance=self.get_object(),
            data=request.data,
        )
        if not serializer.is_valid():
            return Response({
                'message': 'Please check the input',
                'errors': serializers.errors,
            })

        comment = serializer.save()
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        return Response({'success': True}, status=status.HTTP_200_OK)
        
