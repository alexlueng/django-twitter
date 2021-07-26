from core.cache import USER_NEWSFEEDS_PATTERN
from testing.testcases import TestCase
from newsfeeds.models import NewsFeed
from friendships.models import Friendships
from rest_framework.test import APIClient
from rest_framework import status
from utils.paginations import EndlessPagination
from .services import NewsFeedService
from utils.redis_client import RedisClient
from django.conf import settings


NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'
class NewsFeedApiTest(TestCase):
    def setUp(self):

        self.clear_cache()

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
        self.assertEqual(len(response.data['results']), 0)
        # can see what myself tweet
        self.alex_client.post(POST_TWEETS_URL,  {'content': 'Hello world!!!!!!!!!!!!'})
        response = self.alex_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 1)
        # can read other while following
        self.alex_client.post(FOLLOW_URL.format(self.bob.id))
        response = self.bob_client.post(POST_TWEETS_URL, {
            'content': 'hello twitter'
        })
        posted_tweet_id = response.data['id']
        response = self.alex_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['tweet']['id'], posted_tweet_id)


    def test_pagination(self):
        page_size = EndlessPagination.page_size
        followed_user = self.create_user('followed')
        newsfeeds = []
        for i in range(page_size * 2):
            tweet = self.create_tweet(followed_user)
            newsfeed = self.create_newsfeed(user=self.alex, tweet=tweet)
            newsfeeds.append(newsfeed)

        newsfeeds = newsfeeds[::-1]

        print('newsfeeds len: ', len(newsfeeds))
        print('newsfeed[page_size-1] id: ', page_size-1, newsfeeds[page_size-1].id)

        

        # pull the first page
        response = self.alex_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[0].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[1].id)
        self.assertEqual(
            response.data['results'][page_size - 1]['id'],
            newsfeeds[page_size - 1].id,
        )

        # pull the second page
        response = self.alex_client.get(
            NEWSFEEDS_URL,
            {'created_at__lt': newsfeeds[page_size - 1].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        results = response.data['results']
        self.assertEqual(len(results), page_size)
        self.assertEqual(results[0]['id'], newsfeeds[page_size].id)
        self.assertEqual(results[1]['id'], newsfeeds[page_size + 1].id)
        self.assertEqual(
            results[page_size - 1]['id'],
            newsfeeds[2 * page_size - 1].id,
        )

        # pull latest newsfeeds
        response = self.alex_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': newsfeeds[0].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        tweet = self.create_tweet(followed_user)
        new_newsfeed = self.create_newsfeed(user=self.alex, tweet=tweet)

        response = self.alex_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': newsfeeds[0].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_newsfeed.id)


    def test_user_cache(self):
        profile = self.bob.profile
        profile.nickname = 'unclebob'
        profile.save()

        self.assertEqual(self.bob.username, 'bob')
        self.create_newsfeed(self.bob, self.create_tweet(self.bob))
        self.create_newsfeed(self.bob, self.create_tweet(self.alex))

        res = self.bob_client.get(NEWSFEEDS_URL)
        results = res.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'alex')
        self.assertEqual(results[1]['tweet']['user']['nickname'], 'unclebob')
        self.assertEqual(results[1]['tweet']['user']['username'], 'bob')

        self.alex.username = 'alexlueng'
        self.alex.save()
        profile.nickname = 'bob martin'
        profile.save()

        res = self.bob_client.get(NEWSFEEDS_URL)
        results = res.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'alexlueng')
        self.assertEqual(results[1]['tweet']['user']['nickname'], 'bob martin')
        self.assertEqual(results[1]['tweet']['user']['username'], 'bob')


    def test_tweet_cache(self):
        tweet = self.create_tweet(self.alex, 'content1')
        self.create_newsfeed(self.bob, tweet)
        response = self.bob_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'alex')
        self.assertEqual(results[0]['tweet']['content'], 'content1')

        # update username
        self.alex.username = 'alexlueng'
        self.alex.save()
        response = self.bob_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'alexlueng')

        # update content
        tweet.content = 'content2'
        tweet.save()
        response = self.bob_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['content'], 'content2')


class NewsfeedServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.alex = self.create_user('alex')
        self.alex_client = APIClient()
        self.alex_client.force_authenticate(self.alex)
        self.bob = self.create_user('bob')

    def test_get_user_newsfeeds(self):
        newsfeed_ids = []
        for i in range(3):
            tweet = self.create_tweet(self.bob)
            newsfeed = self.create_newsfeed(self.alex, tweet)
            newsfeed_ids.append(newsfeed.id)
        newsfeed_ids = newsfeed_ids[::-1]

        # cache miss
        newfeeds = NewsFeedService.get_cached_newsfeeds(self.alex.id)
        self.assertEqual([f.id for f in newfeeds], newsfeed_ids)

        # cache hit
        newfeeds = NewsFeedService.get_cached_newsfeeds(self.alex.id)
        self.assertEqual([f.id for f in newfeeds], newsfeed_ids)

        # cache update
        tweet = self.create_tweet(self.bob)
        new_newsfeed = self.create_newsfeed(self.alex, tweet)
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.alex.id)
        newsfeed_ids.insert(0, new_newsfeed.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

    def test_create_new_newsfeed_before_get_cached_newsfeeds(self):
        feed1 = self.create_newsfeed(self.alex, self.create_tweet(self.alex))

        RedisClient.clear()
        conn = RedisClient.get_connection()

        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.alex.id)
        self.assertEqual(conn.exists(key), False)

        feed2 = self.create_newsfeed(self.alex, self.create_tweet(self.alex))
        self.assertEqual(conn.exists(key), True)

        feeds = NewsFeedService.get_cached_newsfeeds(self.alex.id)
        self.assertEqual([f.id for f in feeds], [feed2.id, feed1.id])


    def _paginate_to_get_newsfeeds(self, client):
        # paginate until the end
        res = client.get(NEWSFEEDS_URL)
        results = res.data['results']
        while res.data['has_next_page']:
            created_at__lt = res.data['results'][-1]['created_at']
            res = client.get(NEWSFEEDS_URL, {'created_at__lt': created_at__lt})
            results.extend(res.data['results'])
        return results

    def test_redis_list_limit(self):
        list_limit = settings.REDIS_LIST_LENGTH_LIMIT
        page_size = 20
        users = [self.create_user('user{}'.format(i)) for i in range(5)]
        newsfeeds = []

        for i in range(list_limit + page_size):
            tweet = self.create_tweet(user=users[i%5], content='feed{}'.format(i))
            feed = self.create_newsfeed(self.alex, tweet)
            newsfeeds.append(feed)

        newsfeeds = newsfeeds[::-1]

        # only cached list_limit objects
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(self.alex.id)
        self.assertEqual(len(cached_newsfeeds), list_limit)
        queryset = NewsFeed.objects.filter(user=self.alex)
        self.assertEqual(queryset.count(), list_limit + page_size)
        
        results = self._paginate_to_get_newsfeeds(self.alex_client)
        self.assertEqual(len(results), list_limit + page_size)
        for i in range(list_limit + page_size):
            self.assertEqual(newsfeeds[i].id, results[i]['id'])

        # a followed user create a new tweet
        self.create_friendships(self.alex, self.bob)
        new_tweet = self.create_tweet(self.bob, 'a new tweet')
        NewsFeedService.fanout_to_followers(new_tweet)

        def _test_newsfeeds_after_new_feed_pushed():
            results = self._paginate_to_get_newsfeeds(self.alex_client)
            self.assertEqual(len(results), list_limit + page_size + 1)
            self.assertEqual(results[0]['tweet']['id'], new_tweet.id)
            for i in range(list_limit + page_size):
                self.assertEqual(newsfeeds[i].id, results[i+1]['id'])

        _test_newsfeeds_after_new_feed_pushed()

        self.clear_cache()
        _test_newsfeeds_after_new_feed_pushed()