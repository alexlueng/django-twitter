from rest_framework import serializers, viewsets, status
from .models import NewsFeed
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import NewsFeedSerializer
from rest_framework.response import Response
from utils.paginations import EndlessPagination
class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def get_queryset(self):
        return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        page = self.paginate_queryset(self.get_queryset())
        serializer = NewsFeedSerializer(page, context={'request': request}, many=True)
        
        return self.get_paginated_response(serializer.data)
