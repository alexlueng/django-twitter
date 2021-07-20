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
NOTIFICATION_URL = '/api/notifications/'
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


class NotificationApiTests(TestCase):

    def setUp(self):

        self.clear_cache()
        
        self.alex = self.create_user('alex')
        self.alex_client = APIClient()
        self.bob = self.create_user('bob')
        self.bob_client = APIClient()
        self.alex_client.force_authenticate(self.alex)
        self.bob_client.force_authenticate(self.bob)

        self.tweet = self.create_tweet(self.alex)
        self.comment = self.create_comment(self.bob, self.tweet, "test comment")


    def test_user_notification_list(self):
        payload = {
            'tweet_id': self.tweet.id,
            'content': '111'
        }
        self.bob_client.post(COMMENT_URL, payload)
        res = self.alex_client.get(NOTIFICATION_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)

        payload = {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        }
        res = self.bob_client.post(LIKE_BASE_URL, payload)

        res = self.alex_client.get(NOTIFICATION_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 2)

    def test_unread_count(self):

        payload = {
            'tweet_id': self.tweet.id,
            'content': '111'
        }
        self.bob_client.post(COMMENT_URL, payload)
        url = '/api/notifications/unread-count/'
        res = self.alex_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['unread_count'], 1)

        payload = {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        }
        res = self.bob_client.post(LIKE_BASE_URL, payload)

        res = self.alex_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['unread_count'], 2)

    
    def test_mark_all_as_read(self):
        payload = {
            'tweet_id': self.tweet.id,
            'content': '111'
        }
        self.bob_client.post(COMMENT_URL, payload)
        unread_url = '/api/notifications/unread-count/'
        payload = {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        }
        res = self.bob_client.post(LIKE_BASE_URL, payload)

        res = self.alex_client.get(unread_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['unread_count'], 2)

        url = '/api/notifications/mark-all-as-read/'
        res = self.alex_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED) #　get method is not allowed
        res = self.alex_client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['marked_count'], 2)
        res = self.alex_client.get(unread_url)
        self.assertEqual(res.data['unread_count'], 0)


    def test_user_update_notifications(self):
        payload = {
            'tweet_id': self.tweet.id,
            'content': '111'
        }
        res = self.bob_client.post(COMMENT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.alex.notifications.all()), 1)
        self.assertEqual(len(self.alex.notifications.unread()), 1)
        self.assertEqual(len(self.alex.notifications.read()), 0)

        payload = {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        }
        res = self.bob_client.post(LIKE_BASE_URL, payload)
        self.assertEqual(len(self.alex.notifications.all()), 2)
        self.assertEqual(len(self.alex.notifications.unread()), 2)
        self.assertEqual(len(self.alex.notifications.read()), 0)


        # /api/notifications/1/
        notification = self.alex.notifications.first()
        # print("*****************notification id: ", notification.id)
        url = '/api/notifications/{}/'.format(notification.id)

        # not post, but put
        res = self.alex_client.post(url, {'unread':False})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # can not update notifications by others
        res = self.anonymous_client.put(url, {'unread': False})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        res = self.bob_client.put(url, {'unread': False})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # read notification succeed
        print(url)
        res = self.alex_client.put(url, {'unread': False})
        # print(res.data['message'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.alex.notifications.unread()), 1)

        # mark the notification unread again
        res = self.alex_client.put(url, {'unread': True})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.alex.notifications.unread()), 2)

        # the params must contain 'unread'
        res = self.alex_client.put(url, {'verb': 'new verb'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # can not update other params
        res = self.alex_client.put(url, {'unread': False, 'verb': 'newwwwwww verb'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertNotEqual(notification.verb, 'newwwwwww verb')