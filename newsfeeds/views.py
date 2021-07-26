from newsfeeds.services import NewsFeedService
from rest_framework import serializers, viewsets, status
from .models import NewsFeed
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import NewsFeedSerializer
from rest_framework.response import Response
from utils.paginations import EndlessPagination
from .models import NewsFeed
class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    # def get_queryset(self):
    #     return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(request.user.id)
        page = self.paginator.paginate_cached_list(cached_newsfeeds, request)
        if page is None:
            queryset = NewsFeed.objects.filter(user=request.user)
            page = self.paginate_queryset(queryset)
        serializer = NewsFeedSerializer(page, context={'request': request}, many=True)
        
        return self.get_paginated_response(serializer.data)
