from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from tweets.models import Tweet
from comments.models import Comment
from rest_framework import serializers
from .models import Like
# from django.contrib.auth.models import User
from accounts.serializers import UserSerializerForLike

class LikeSerializer(serializers.ModelSerializer):

    user = UserSerializerForLike(source='cached_user')

    class Meta:
        model = Like
        fields = ('user', 'created_at')


class LikeSerializerForCreateAndCancel(serializers.ModelSerializer):
    content_type = serializers.ChoiceField(choices=['tweet', 'comment'])
    object_id = serializers.IntegerField()

    class Meta:
        model = Like
        fields = ('content_type', 'object_id')

    def _get_model_class(self, data):
        if data['content_type'] == 'comment':
            return Comment
        if data['content_type'] == 'tweet':
            return Tweet

        return None

    def validate(self, data):
        model_class = self._get_model_class(data)
        if model_class is None:
            raise ValidationError({'content_type': 'content type does not exist'})
        liked_object = model_class.objects.filter(id=data['object_id']).first()
        if liked_object is None:
            raise ValidationError({'object_id': 'object does not exist'})
        return data


class LikeSerializerForCreate(LikeSerializerForCreateAndCancel):
    

    def get_or_create(self):
        model_class = self._get_model_class(self.validated_data)
        print('models_class: ', model_class)
        return Like.objects.get_or_create(
            user=self.context['request'].user,
            content_type=ContentType.objects.get_for_model(model_class),
            object_id=self.validated_data['object_id']
        )
        


class LikeSerializerForCancel(LikeSerializerForCreateAndCancel):
    
    def cancel(self):
        model_class = self._get_model_class(self.validated_data)
        Like.objects.filter(
            user=self.context['request'].user,
            content_type=ContentType.objects.get_for_model(model_class),
            object_id=self.validated_data['object_id']
        ).delete()