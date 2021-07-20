from friendships.services import FriendshipService
from rest_framework import serializers
from accounts.serializers import UserSerializerForFriendship
from rest_framework.exceptions import ValidationError
from .models import Friendships


class FollowingUserIdSetMixin:
    @property
    def following_user_id_set(self: serializers.ModelSerializer):
        if self.context['request'].user.is_anonymous:
            return {}
        if hasattr(self, '_cached_following_user_id_set'):
            return self._cached_following_user_id_set
        user_id_set = FriendshipService.get_following_user_id_set(self.context['request'].user.id)
        setattr(self, '_cached_following_user_id_set', user_id_set)
        return user_id_set

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


class FollowerSerializer(serializers.ModelSerializer, FollowingUserIdSetMixin):
    user = UserSerializerForFriendship(source='cached_from_user')
    created_at = serializers.DateTimeField()
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendships
        fields = ('user', 'created_at', 'has_followed')

    def get_has_followed(self, obj):
        return obj.from_user in self.following_user_id_set

class FollowingSerializer(serializers.ModelSerializer, FollowingUserIdSetMixin):
    user = UserSerializerForFriendship(source='cached_to_user')
    created_at = serializers.DateTimeField()
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendships
        fields = ('user', 'created_at', 'has_followed')

    def get_has_followed(self, obj):
        return obj.to_user in self.following_user_id_set
