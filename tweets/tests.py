from rest_framework.test import APIClient
from testing.testcases import TestCase
from django.contrib.auth.models import User
from tweets.models import Tweet
from datetime import timedelta
from utils.time_helpers import utc_now
from rest_framework import status

TWEET_LIST_API = '/api/tweets/'
TWEET_CREATE_API = '/api/tweets/'
TWEET_RETRIEVE_API = '/api/tweets/{}/'

class TweetTests(TestCase):
    def test_hours_to_now(self):
        alex = User.objects.create_user(username='alex')
        tweet = Tweet.objects.create(user=alex, content='alexleng is god')
        tweet.created_at = utc_now() - timedelta(hours=10)
        tweet.save()
        self.assertEqual(tweet.hours_to_now, 10)


class TweetApiTests(TestCase):

    def setUp(self):
        # self.anonymous_client = APIClient()
        
        self.user1 = self.create_user('user1', 'user1@example.com')
        self.tweet1 = [self.create_tweet(self.user1, "hello world") for i in range(3)]
        
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2', 'user2@example.com')
        self.tweet2 = [self.create_tweet(self.user2, "hello world") for i in range(2)]


    def test_list_api(self):
        response = self.anonymous_client.get(TWEET_LIST_API)
        self.assertEqual(response.status_code, 400)

        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tweets']), 3)
        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user2.id})
        # self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tweets']), 2)
        self.assertEqual(response.data['tweets'][0]['id'], self.tweet2[1].id)
        self.assertEqual(response.data['tweets'][1]['id'], self.tweet2[0].id)

    def test_create_api(self):
        response = self.anonymous_client.post(TWEET_CREATE_API)
        print(response)
        self.assertEqual(response.status_code, 403)

        response = self.user1_client.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 400)

        response = self.user1_client.post(TWEET_CREATE_API, {'content': '1'})
        self.assertEqual(response.status_code, 400)

        response = self.user1_client.post(TWEET_CREATE_API, {'content': '0'*141})
        self.assertEqual(response.status_code, 400)

        tweets_count = Tweet.objects.count()
        response = self.user1_client.post(TWEET_CREATE_API, {'content': 'Hello world, this is my first post!'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(Tweet.objects.count(), tweets_count+1)

    def test_get_tweet_with_comments_with_invalid_tweet_id(self):
        url = TWEET_RETRIEVE_API.format(-1)
        res = self.anonymous_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


    def test_get_tweet_with_comments(self):
        tweet = self.create_tweet(self.user1)
        url = TWEET_RETRIEVE_API.format(tweet.id)
        res = self.anonymous_client.get(url)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['comments']), 0)
        
        self.create_comment(self.user1, tweet, content='comment test1')
        self.create_comment(self.user2, tweet, content='comment test2')

        res = self.anonymous_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['comments']), 2)









