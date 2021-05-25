from rest_framework import serializers
from rest_framework import exceptions
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):

    # url = serializers.HyperlinkedIdentityField(view_name="accounts:user-detail")

    class Meta:
        model = User

        # url是默认值， 可在settings.py中设置URL_FIELD_NAME使全局生效

        fields = ('id', 'username', 'email')


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class SignupSerializer(serializers.Serializer):

    username = serializers.CharField(max_length=20, min_length=6)
    password = serializers.CharField()
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def validate(self, data):
        if User.objects.filter(username=data['username'].lower()).exists():
            raise exceptions.ValidationError({
                'message': 'This username has been occupied.'
            })

        if User.objects.filter(email=data['email'].lower()).exists():
            raise exceptions.ValidationError({
                'message': 'This email address has been occupied'
            })

        return data

    def create(self, validated_data):
        username = validated_data['username'].lower()
        email = validated_data['email'].lower()
        password = validated_data['password']

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        return user