from testing.testcases import TestCase
from newsfeeds.models import NewsFeed
from friendships.models import Friendships
from rest_framework.test import APIClient
from rest_framework import status

NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'
class NewsFeedApiTest(TestCase):
    def setUp(self):
        self.alex = self.create_user('alex')
        self.alex_client = APIClient()
        self.alex_client.force_authenticate(self.alex)

        self.bob = self.create_user('bob')
        self.bob_client = APIClient()
        self.bob_client.force_authenticate(self.bob)

        for i in range(2):
            follower = self.create_user('alex_follower{}'.format(i))
            Friendships.objects.create(from_user=follower, to_user=self.alex)
        
        for i in range(3):
            following = self.create_user('alex_following{}'.format(i))
            Friendships.objects.create(from_user=self.alex, to_user=following)

    def test_list(self):
        # need login
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # can't not use post
        response = self.alex_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        # empty at the beginning
        response = self.bob_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['newsfeeds']), 0)
        # can see what myself tweet
        self.alex_client.post(POST_TWEETS_URL,  {'content': 'Hello world!!!!!!!!!!!!'})
        response = self.alex_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 1)
        # can read other while following
        self.alex_client.post(FOLLOW_URL.format(self.bob.id))
        response = self.bob_client.post(POST_TWEETS_URL, {
            'content': 'hello twitter'
        })
        posted_tweet_id = response.data['id']
        response = self.alex_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)
