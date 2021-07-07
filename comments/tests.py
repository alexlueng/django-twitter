from django.http import response
from rest_framework.test import APIClient
from testing.testcases import TestCase

from rest_framework import status

from .models import Comment

COMMENT_URL = '/api/comments/'

class CommentModelTests(TestCase):
    def test_comment_str(self):
        user = self.create_user('alex')
        tweet = self.create_tweet(user=user)
        comment = Comment.objects.create(
            user=user,
            tweet=tweet,
            content='test comment content'
        )

        self.assertEqual(str(comment), f'{comment.created_at} - {comment.user} says {comment.content} at tweet {comment.tweet.id}')


# class PublicCommentApiTests(TestCase):
#     def test_auth_required(self):
#         res = self.anonymous_client.get(COMMENT_URL)
#         self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class CommentApiTests(TestCase):
    def setUp(self):
        self.alex = self.create_user('alex')
        self.alex_client = APIClient()
        self.bob = self.create_user('bob')
        self.bob_client = APIClient()
        self.alex_client.force_authenticate(self.alex)
        self.bob_client.force_authenticate(self.bob)

        self.tweet = self.create_tweet(self.alex)

    # 不允许匿名评论
    def test_add_comment_anonymous(self):
        res = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 不能不带参数
    def test_add_comment_without_params(self):
        res = self.alex_client.post(COMMENT_URL)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 只带tweet_id不行
    def test_add_comment_only_with_tweet_id(self):
        res = self.alex_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 只带content不行
    def test_add_comment_only_with_content(self):
        res = self.alex_client.post(COMMENT_URL, {'content': '111'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # content不能过长
    def test_add_comment_with_long_content(self):
        payload = {
            'tweet_id': self.tweet.id,
            'content': '1' *141
        }
        res = self.alex_client.post(COMMENT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('content' in res.data['errors'], True)

    # 带tweet_id和content创建成功
    def test_add_comment_with_tweet_id_and_content(self):
        payload = {
            'tweet_id': self.tweet.id,
            'content': '111'
        }
        res = self.alex_client.post(COMMENT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        print(res.data['user'])
        self.assertEqual(res.data['user']['id'], self.alex.id)
        self.assertEqual(res.data['tweet_id'], self.tweet.id)
        self.assertEqual(res.data['content'], '111')


