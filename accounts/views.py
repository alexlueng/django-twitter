from accounts.models import UserProfile
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.serializers import LoginSerializer, SignupSerializer, UserProfileSerializerForUpdate, UserSerializer
from django.contrib.auth import (
    authenticate as django_authenticate,
    login as django_login,
    logout as django_logout,
)
from utils.permissions import IsObjectOwner
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit

# Create your views here.
#TODO: 加入jwt djangorestframework auth加强认证

class UserViewSet(viewsets.ModelViewSet):

    """
        API endpoint that allows users to be viewed or edited
    """
    
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    # permission_classes = [permissions.IsAuthenticated]


class AccountViewSet(viewsets.ViewSet):

    serializer_class = SignupSerializer
    
    @action(methods=['GET'], detail=False)
    def login_status(self, request):
        data = {'has_logged_in': request.user.is_authenticated}
        if request.user.is_authenticated:
            data['user'] = UserSerializer(request.user).data
        return Response(data)

    @action(methods=['POST'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def logout(self, request):
        django_logout(request)
        return Response({'success': True})


    @action(methods=['POST'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Please check input",
                "errors": serializer.errors,
            }, status=400)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = django_authenticate(username=username, password=password)

        if not User.objects.filter(username=username).exists():
            return Response({
                "success": False,
                "message": "User does not exists.",
                "errors": serializer.errors,
            }, status=400)


        if not user or user.is_anonymous:
            return Response({
                "success": False,
                "message": "Username and password does not match.",
                "errors": serializer.errors,
            }, status=400)

        django_login(request, user)
        return Response({
                "success": True,
                "user": UserSerializer(user).data,
            }, status=200) 


    @action(methods=['POST'], detail=False)
    def signup(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Please check input.",
                "errors": serializer.errors,
            }, status=400)
        user = serializer.save()

        user.profile

        django_login(request, user)
        return Response({
                "success": True,
                "user": UserSerializer(user).data,
            }, status=201)

    @action(methods=['GET'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='GET', block=True))
    def login_status(self, request, *args, **kwargs):
        data = {'has_logged_in': request.user.is_authenticated}
        if request.user.is_authenticated:
            data['user'] = UserSerializer(request.user).data
        return Response(data)


class UserProfileViewSet(viewsets.GenericViewSet,
                        viewsets.mixins.UpdateModelMixin):

    queryset = UserProfile
    permission_classes = (IsObjectOwner,)
    serializer_class = UserProfileSerializerForUpdate