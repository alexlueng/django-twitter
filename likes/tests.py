from django.test import testcases
from rest_framework import status
from testing.testcases import TestCase
from django.contrib.contenttypes.models import ContentType
from .models import Like
from rest_framework.test import APIClient

LIKE_BASE_URL = '/api/likes/'
LIKE_CANCEL_URL = '/api/likes/cancel/'
class LikeModelTest(TestCase):

    def test_like_str(self):
        user = self.create_user('alex')
        tweet = self.create_tweet(user)
        comment = self.create_comment(user, tweet, 'like comment')

        like_tweet_instance, _ = Like.objects.get_or_create(
            user=user,
            content_type=ContentType.objects.get_for_model(tweet),
            object_id=tweet.id
        )
        like_comment_instance, _ = Like.objects.get_or_create(
            user=user,
            content_type=ContentType.objects.get_for_model(comment),
            object_id=comment.id
        )

        # print(like_comment_instance)

        self.assertEqual(str(like_tweet_instance), f'{like_tweet_instance.created_at} - {like_tweet_instance.user} liked {like_tweet_instance.content_type} {like_tweet_instance.object_id}')
        self.assertEqual(str(like_comment_instance), f'{like_comment_instance.created_at} - {like_comment_instance.user} liked {like_comment_instance.content_type} {like_comment_instance.object_id}')


class LikeApiTests(TestCase):

    def setUp(self):
        self.alex = self.create_user('alex')
        self.alex_client = APIClient()
        self.bob = self.create_user('bob')
        self.bob_client = APIClient()
        self.alex_client.force_authenticate(self.alex)
        self.bob_client.force_authenticate(self.bob)

        self.tweet = self.create_tweet(self.alex)
        self.comment = self.create_comment(self.alex, self.tweet, 'test comment')

    def test_like_anonymous(self):
        res = self.anonymous_client.get(LIKE_BASE_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_like_get_method_not_allow(self):
        payload = {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        }
        res = self.alex_client.get(LIKE_BASE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_like_tweet_success(self):
        payload = {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        }
        res = self.alex_client.post(LIKE_BASE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.tweet.like_set.count(), 1)

    def test_like_comment_with_wrong_content_type(self):
        payload = {
            'content_type': 'coment',
            'object_id': self.tweet.id,
        }
        res = self.alex_client.post(LIKE_BASE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_like_comment_with_wrong_object_id(self):
        payload = {
            'content_type': 'comment',
            'object_id': -1,
        }
        res = self.alex_client.post(LIKE_BASE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_like_comment_success(self):
        payload = {
            'content_type': 'comment',
            'object_id': self.comment.id,
        }
        res = self.alex_client.post(LIKE_BASE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.comment.like_set.count(), 1)

    def test_like_comment_cancel(self):
        payload = {
            'content_type': 'comment',
            'object_id': self.comment.id,
        }
        res = self.alex_client.post(LIKE_BASE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.comment.like_set.count(), 1)

        res = self.alex_client.post(LIKE_CANCEL_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.comment.like_set.count(), 0)


    