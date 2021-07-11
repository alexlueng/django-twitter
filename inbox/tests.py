from comments.tests import sample_comment
from testing.testcases import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from notifications.models import Notification
from .services import NotificationService
# 测试用例：
# 本人发的推特，评论点赞不需要通知
# 对评论点赞，推特点赞都需要通知
# 查看本人的消息列表

LIKE_BASE_URL = '/api/likes/'
NOTIFICATION_URL = 'api/notifications/'
COMMENT_URL = '/api/comments/'


class NotificationTests(TestCase):

    def setUp(self):
        
        self.alex = self.create_user('alex')
        self.alex_client = APIClient()
        self.bob = self.create_user('bob')
        self.bob_client = APIClient()
        self.alex_client.force_authenticate(self.alex)
        self.bob_client.force_authenticate(self.bob)

        self.tweet = self.create_tweet(self.alex)
        self.comment = self.create_comment(self.bob, self.tweet, "test comment")

    def test_user_empty_notifications(self):
        """
            All users have an empty inbox when they created
        """

        self.assertEqual(len(self.alex.notifications.all()), 0)
        self.assertEqual(len(self.bob.notifications.all()), 0)

    def test_user_receive_like_notifications(self):
        payload = {
            'content_type': 'comment',
            'object_id': self.comment.id,
        }
        res = self.alex_client.post(LIKE_BASE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 1)
        
        like = self.create_like(self.bob, self.tweet)
        NotificationService.send_like_notification(like)

        self.assertEqual(Notification.objects.count(), 2)
        

    def test_user_receive_comment_notifications(self):
        payload = {
            'tweet_id': self.tweet.id,
            'content': '111'
        }
        res = self.bob_client.post(COMMENT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 1)

