from rest_framework import serializers, viewsets, status
from .models import NewsFeed
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import NewsFeedSerializer
from rest_framework.response import Response

class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        serializer = NewsFeedSerializer(self.get_queryset(), context={'request': request}, many=True)
        return Response({
            'newsfeeds': serializer.data,
        }, status=status.HTTP_200_OK)
