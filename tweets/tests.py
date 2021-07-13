from rest_framework.test import APIClient
from testing.testcases import TestCase
from django.contrib.auth.models import User
from tweets.models import Tweet, TweetPhoto
from datetime import timedelta
from utils.time_helpers import utc_now
from rest_framework import status
from .constants import TweetPhotoStatus
from django.core.files.uploadedfile import SimpleUploadedFile

TWEET_LIST_API = '/api/tweets/'
TWEET_CREATE_API = '/api/tweets/'
TWEET_RETRIEVE_API = '/api/tweets/{}/'
LIKE_BASE_URL = '/api/likes/'


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
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)
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

    def test_tweet_likes(self):
        tweet = self.create_tweet(self.user1,  "test tweet")
        # comment = sample_comment(self.alex, tweet, content='111')
        self.create_like(self.user1, tweet)
        self.assertEqual(tweet.like_set.count(), 1)

        self.create_like(self.user2, tweet)
        self.assertEqual(tweet.like_set.count(), 2)

    def test_tweet_comment_counts(self):
        tweet = self.create_tweet(self.user1,  "test tweet")
        self.create_comment(self.user2, tweet, content='111')

        res = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['tweets'][0]['comments_count'], 1)


        self.create_comment(self.user1, tweet, content='222')
        res = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['tweets'][0]['comments_count'], 2)


    
    def test_tweet_has_liked(self):

        tweet = self.create_tweet(self.user1,  "test tweet")
        # comment = sample_comment(self.alex, tweet, content='111')

        payload = {
            'content_type': 'tweet',
            'object_id': tweet.id,
        }
        self.user2_client.post(LIKE_BASE_URL, payload)

        tweet.refresh_from_db()

        res = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['tweets'][0]['has_liked'], False)

        res = self.user2_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['tweets'][0]['has_liked'], True)

    def test_tweet_likes_count(self):
        tweet = self.create_tweet(self.user1,  "test tweet")
        # comment = self.create_comment(self.user2, tweet, content='111')

        payload = {
            'content_type': 'tweet',
            'object_id': tweet.id,
        }
        self.user2_client.post(LIKE_BASE_URL, payload)

        res = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['tweets'][0]['likes_count'], 1)

        self.user1_client.post(LIKE_BASE_URL, payload)
        res = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['tweets'][0]['likes_count'], 2)

    def test_tweet_retrieve_with_user_profile(self):
        tweet = self.create_tweet(self.user1)
        url = TWEET_RETRIEVE_API.format(tweet.id)
        res = self.anonymous_client.get(url)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        profile = self.user1.profile
        self.assertEqual(res.data['user']['nickname'], profile.nickname)
        self.assertEqual(res.data['user']['avatar_url'], None)


class TweetPhotoApiTests(TestCase):

    def setUp(self):
        self.alex = self.create_user('alex')
        self.alex_client = APIClient()
        self.alex_client.force_authenticate(self.alex)
        self.tweet = self.create_tweet(self.alex)

    def test_tweet_photo_created(self):
        photo = TweetPhoto.objects.create(
            tweet=self.tweet,
            user=self.alex
        )

        self.assertEqual(photo.user, self.alex)
        self.assertEqual(photo.status, TweetPhotoStatus.PENDING)
        self.assertEqual(self.tweet.tweetphoto_set.count(), 1)


    def test_create_with_images(self):
        res = self.alex_client.post(TWEET_CREATE_API, {'content': 'test file upload', 'files': []})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TweetPhoto.objects.count(), 0)

        file = SimpleUploadedFile(
            name='sample.jpg',
            content=str.encode('a fake image'),
            content_type='image/jpeg',
        )

        res = self.alex_client.post(TWEET_CREATE_API, {'content': 'test file upload', 'files': [file]})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TweetPhoto.objects.count(), 1)

        file1 = SimpleUploadedFile(
            name='sample1.jpg',
            content=str.encode('a fake image'),
            content_type='image/jpeg',
        )
        file2 = SimpleUploadedFile(
            name='sample2.jpg',
            content=str.encode('a fake image'),
            content_type='image/jpeg',
        )

        res = self.alex_client.post(TWEET_CREATE_API, {'content': 'test file upload', 'files': [file1, file2]})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TweetPhoto.objects.count(), 3)

        

        files = [SimpleUploadedFile(
            name='sample{i}.jpg',
            content=str.encode('a fake image'),
            content_type='image/jpeg',
        ) for i in range(10)]

        res = self.alex_client.post(TWEET_CREATE_API, {'content': 'test file upload', 'files': [files]})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # self.assertEqual(TweetPhoto.objects.count(), 3)
