from .models import Comment
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import CommentSerializerForCreate, CommentSerializer


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

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        return [AllowAny()]

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

        
