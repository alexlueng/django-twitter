from friendships.services import FriendshipService
from django.http import response
from testing.testcases import TestCase
from rest_framework.test import APIClient
from .models import Friendships
from rest_framework import status
from .paginations import FriendshipsPagination

FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipsApiTests(TestCase):

    def setUp(self):
        # self._anonymous_client = APIClient()
        self.clear_cache()

        self.alex = self.create_user('alex')
        self.alex_client = APIClient()
        self.alex_client.force_authenticate(self.alex)

        self.bob = self.create_user('bob')
        self.bob_client = APIClient()
        self.bob_client.force_authenticate(self.bob)

        # create followings and followers for bob
        for i in range(2):
            follower = self.create_user('bob_follower{}'.format(i))
            Friendships.objects.create(from_user=follower, to_user=self.bob)
        for i in range(3):
            following = self.create_user('bob_following{}'.format(i))
            Friendships.objects.create(from_user=self.bob, to_user=following)

    def test_follow(self):
        url = FOLLOW_URL.format(self.alex.id)

        # 需要登录才能 follow 别人
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # 要用 get 来 follow
        response = self.bob_client.get(url)
        self.assertEqual(response.status_code, 405)
        # 不可以 follow 自己
        response = self.alex_client.post(url)
        self.assertEqual(response.status_code, 400)
        # follow 成功
        response = self.bob_client.post(url)
        self.assertEqual(response.status_code, 201)
        # 重复 follow 静默成功
        response = self.bob_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['duplicate'], True)
        # 反向关注会创建新的数据
        count = Friendships.objects.count()
        response = self.alex_client.post(FOLLOW_URL.format(self.bob.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendships.objects.count(), count + 1)
    
    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.alex.id)

        # 需要登录才能 unfollow 别人
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # 不能用 get 来 unfollow 别人
        response = self.bob_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        # 不能用 unfollow 自己
        response = self.alex_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # unfollow 成功
        Friendships.objects.create(from_user=self.bob, to_user=self.alex)
        count = Friendships.objects.count()
        response = self.bob_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(Friendships.objects.count(), count - 1)
        # 未 follow 的情况下 unfollow 静默处理
        count = Friendships.objects.count()
        response = self.bob_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(Friendships.objects.count(), count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.bob.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        # 确保按照时间倒序
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        ts2 = response.data['results'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'bob_following2',
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'bob_following1',
        )
        self.assertEqual(
            response.data['results'][2]['user']['username'],
            'bob_following0',
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.bob.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        # 确保按照时间倒序
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'bob_follower1',
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'bob_follower0',
        )


    def test_followers_pagination(self):
        max_page_size = FriendshipsPagination.max_page_size
        page_size = FriendshipsPagination.page_size
        for i in range(page_size * 2):
            follower = self.create_user('alex_follower{}'.format(i))
            Friendships.objects.create(from_user=follower, to_user=self.alex)
            if follower.id % 2 == 0:
                Friendships.objects.create(from_user=self.bob, to_user=follower)
        url = FOLLOWERS_URL.format(self.alex.id)
        self._test_friendships_pagination(url, page_size, max_page_size)

        # anonymous hasn't followed any users
        res = self.anonymous_client.get(url, {'page': 1})
        for result in res.data['results']:
            self.assertEqual(result['has_followed'], False)
        
        # bob has followed users with even id
        res = self.bob_client.get(url, {'page': 1})
        for result in res.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def test_followings_pagination(self):
        max_page_size = FriendshipsPagination.max_page_size
        page_size = FriendshipsPagination.page_size
        for i in range(page_size * 2):
            following = self.create_user('alex_follower{}'.format(i))
            Friendships.objects.create(from_user=self.alex, to_user=following)
            if following.id % 2 == 0:
                Friendships.objects.create(from_user=self.bob, to_user=following)
        url = FOLLOWINGS_URL.format(self.alex.id)

        res = self.anonymous_client.get(url, {'page': 1})
        for result in res.data['results']:
            self.assertEqual(result['has_followed'], False)
        
        res = self.bob_client.get(url, {'page': 1})
        for result in res.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

        res = self.alex_client.get(url, {'page': 1})
        for result in res.data['results']:
            self.assertEqual(result['has_followed'], True)


    def _test_friendships_pagination(self, url, page_size, max_page_size):
        res = self.anonymous_client.get(url, {'page': 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), page_size)
        self.assertEqual(res.data['total_pages'], 2)
        self.assertEqual(res.data['total_results'], page_size * 2)
        self.assertEqual(res.data['page_number'], 1)
        self.assertEqual(res.data['has_next_page'], True)

        res = self.anonymous_client.get(url, {'page': 2})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), page_size)
        self.assertEqual(res.data['total_pages'], 2)
        self.assertEqual(res.data['total_results'], page_size * 2)
        self.assertEqual(res.data['page_number'], 2)
        self.assertEqual(res.data['has_next_page'], False)

        res = self.anonymous_client.get(url, {'page': 3})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        res = self.anonymous_client.get(url, {'page': 1, 'size': max_page_size+1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), max_page_size)
        self.assertEqual(res.data['total_pages'], 2)
        self.assertEqual(res.data['total_results'], page_size * 2)
        self.assertEqual(res.data['page_number'], 1)
        self.assertEqual(res.data['has_next_page'], True)

        res = self.anonymous_client.get(url, {'page': 1, 'size': 2})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 2)
        self.assertEqual(res.data['total_pages'], page_size)
        self.assertEqual(res.data['total_results'], page_size * 2)
        self.assertEqual(res.data['page_number'], 1)
        self.assertEqual(res.data['has_next_page'], True)


class FriendshipServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.alex = self.create_user('alex')
        self.bob = self.create_user('bob')

    def test_get_followings(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')

        for to_user in [user1, user2, self.bob]:
            Friendships.objects.create(from_user=self.alex, to_user=to_user)
        # FriendshipService.invalidate_following_cache(self.alex.id)

        user_id_set = FriendshipService.get_following_user_id_set(self.alex.id)
        self.assertEqual(user_id_set, {user1.id, user2.id, self.bob.id})

        Friendships.objects.filter(from_user=self.alex, to_user=self.bob).delete()
        # FriendshipService.invalidate_following_cache(self.alex.id)
        user_id_set = FriendshipService.get_following_user_id_set(self.alex.id)
        self.assertEqual(user_id_set, {user1.id, user2.id})
