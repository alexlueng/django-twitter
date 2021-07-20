from testing.testcases import TestCase
from rest_framework.test import APIClient
from .models import UserProfile
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'
USER_PROFILE_DETAIL_URL = '/api/profiles/{}/'


class AccountApiTests(TestCase):

    def setUp(self):

        self.clear_cache()

        # 这个函数会在每个 test function 执行的时候被执行
        self.client = APIClient()
        self.user = self.create_user(
            username='admin',
            email='admin@jiuzhang.com',
            password='correct password',
        )

    # def createUser(self, username, email, password):
        # 不能写成 User.objects.create()
        # 因为 password 需要被加密, username 和 email 需要进行一些 normalize 处理
        # return User.objects.create_user(username, email, password)

    def test_login(self):
        # 每个测试函数必须以 test_ 开头，才会被自动调用进行测试
        # 测试必须用 post 而不是 get
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        # 登陆失败，http status code 返回 405 = METHOD_NOT_ALLOWED
        self.assertEqual(response.status_code, 405)

        # 用了 post 但是密码错了
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password',
        })
        self.assertEqual(response.status_code, 400)

        # 验证还没有登录
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)
        # 用正确的密码
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['email'], 'admin@jiuzhang.com')
        # 验证已经登录了
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        # 先登录
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        # 验证用户已经登录
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        # 测试必须用 post
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # 改用 post 成功 logout
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)
        # 验证用户已经登出
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@jiuzhang.com',
            'password': 'any password',
        }
        # 测试 get 请求失败
        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        # 测试错误的邮箱
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'not a correct email',
            'password': 'any password'
        })
        # print(response.data)
        self.assertEqual(response.status_code, 400)

        # 测试密码太短
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@jiuzhang.com',
            'password': '123',
        })
        # print(response.data)
        self.assertEqual(response.status_code, 400)

        # 测试用户名太长
        response = self.client.post(SIGNUP_URL, {
            'username': 'username is tooooooooooooooooo loooooooong',
            'email': 'someone@jiuzhang.com',
            'password': 'any password',
        })
        # print(response.data)
        self.assertEqual(response.status_code, 400)

        # 成功注册
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')

        # 验证userprofile已经创建
        created_user_id = response.data['user']['id']
        profile = UserProfile.objects.filter(user_id=created_user_id).first()
        self.assertNotEqual(profile, None)

        # 验证用户已经登入
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)


class UserProfileTests(TestCase):

    def setUp(self):

        self.clear_cache()

        self.alex = self.create_user('alex')
        self.alex_client = APIClient()
        self.alex_client.force_authenticate(self.alex)

    def test_profile_property(self):
        # alex = self. create_user('alex')
        self.assertEqual(UserProfile.objects.count(), 0)
        p = self.alex.profile
        self.assertEqual(isinstance(p, UserProfile), True)
        self.assertEqual(UserProfile.objects.count(), 1)

    def test_user_update_profile_nickname(self):
        """
            /api/profile/{}/
        """
        p = self.alex.profile
        p.nickname = 'old nickname'
        p.save()
        
        url = USER_PROFILE_DETAIL_URL.format(p.id)
        res = self.alex_client.put(url, {'nickname': 'new nickname'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        p.refresh_from_db()
        self.assertEqual(p.nickname, 'new nickname')

    def test_user_update_profile_avatar(self):
        p = self.alex.profile
        self.assertEqual(p.avatar, None)

        url = USER_PROFILE_DETAIL_URL.format(p.id)
        res = self.alex_client.put(url, {
            'avatar': SimpleUploadedFile(
                name='my-avatar.jpg',
                content=str.encode('a fake image'),
                content_type='image/jpeg'
            )
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual('my-avatar' in res.data['avatar'], True)
        p.refresh_from_db()
        self.assertIsNotNone(p.avatar)
        
        
