from rest_framework import serializers
from accounts.serializers import UserSerializer
from rest_framework.exceptions import ValidationError
from .models import Friendships

class FriendshipSerializerForCreate(serializers.ModelSerializer):
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()

    class Meta:
        model = Friendships
        fields = ('from_user_id', 'to_user_id')

    def validate(self, attrs):
        if attrs['from_user_id'] == attrs['to_user_id']:
            raise ValidationError({
                'message': 'from user id and to user id must be different'
            })
        return attrs

    def create(self, validated_data):
        from_user_id = validated_data['from_user_id']
        to_user_id = validated_data['to_user_id']
        return Friendships.objects.create(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
        )


class FollowerSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='from_user')
    created_at = serializers.DateTimeField()

    class Meta:
        model = Friendships
        fields = ('user', 'created_at')


class FollowingSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='to_user')
    created_at = serializers.DateTimeField()

    class Meta:
        model = Friendships
        fields = ('user', 'created_at')
