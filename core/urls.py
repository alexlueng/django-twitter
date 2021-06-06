from friendships.models import Friendships
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from accounts.views import AccountViewSet, UserViewSet
from tweets.views import TweetViewSet
from friendships.views import FriendshipViewSet
from newsfeeds.views import NewsFeedViewSet

router = routers.DefaultRouter()
router.register(r'api/users', UserViewSet)
router.register(r'api/accounts', AccountViewSet, basename='accounts')
router.register(r'api/tweets', TweetViewSet, basename='tweets')
router.register(r'api/friendships', FriendshipViewSet, basename='friendships')
router.register(r'api/newsfeed', NewsFeedViewSet, basename='newsfeed')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]