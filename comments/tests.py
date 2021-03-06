from rest_framework.test import APIClient
from testing.testcases import TestCase

from rest_framework import status

from .models import Comment

COMMENT_URL = '/api/comments/'
LIKE_BASE_URL = '/api/likes/'

def sample_comment(user, tweet, content="sample content"):
    return Comment.objects.create(
        user=user,
        tweet=tweet,
        content=content
    )

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

        self.clear_cache()

        self.alex = self.create_user('alex')
        self.alex_client = APIClient()
        self.bob = self.create_user('bob')
        self.bob_client = APIClient()
        self.alex_client.force_authenticate(self.alex)
        self.bob_client.force_authenticate(self.bob)

        self.tweet = self.create_tweet(self.alex)

    
    # ================== add comment =====================
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
        self.assertEqual(res.data['user']['id'], self.alex.id)
        self.assertEqual(res.data['tweet_id'], self.tweet.id)
        self.assertEqual(res.data['content'], '111')


    # ==================== update comment ===============================
    
    # 不能匿名修改
    def test_update_comment_anonymous(self):
        tweet = self.create_tweet(self.alex, "test tweet")
        comment = sample_comment(self.bob, tweet=tweet)
        # url = detail_url(comment.id)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        res = self.anonymous_client.put(url, {'content': 'update content'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 不能被非创建者修改
    def test_update_comment_by_noncreater(self):
        tweet = self.create_tweet(self.alex, "test tweet")
        comment = sample_comment(self.bob, tweet=tweet)
        # url = detail_url(comment.id)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        res = self.alex_client.put(url, {'content': 'update content'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 成功修改
    def test_update_comment_success(self):
        tweet = self.create_tweet(self.alex,  "test tweet")
        comment = sample_comment(self.bob, tweet=tweet)
        # url = detail_url(comment.id)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        res = self.bob_client.put(url, {'content': 'update content'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(res.data['content'], 'update content')

    # 其余测试：修改内容不能为空等

    #===================== delete comment ===============================

    #===================== comment list =================================
    def test_get_comment_list_without_tweet_id(self):
        res = self.anonymous_client.get(COMMENT_URL)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_comment_list_with_a_new_tweet(self):
        tweet = self.create_tweet(self.alex,  "test tweet")
        res = self.anonymous_client.get(COMMENT_URL, {'tweet_id': tweet.id})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['comments']), 0)

    def test_comment_list_ordered_by_timestamp(self):
        tweet = self.create_tweet(self.alex,  "test tweet")
        comment1 = sample_comment(self.bob, tweet, content='111')
        comment2 = sample_comment(self.bob, tweet, content='222')

        res = self.anonymous_client.get(COMMENT_URL, {'tweet_id': tweet.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['comments'][0]['content'], comment1.content)
        self.assertEqual(res.data['comments'][1]['content'], comment2.content)

    def test_comment_list_only_effect_by_tweet_id(self):
        tweet = self.create_tweet(self.alex,  "test tweet")
        sample_comment(self.alex, tweet, content='111')
        sample_comment(self.bob, tweet, content='222')

        res = self.anonymous_client.get(COMMENT_URL, {'tweet_id': tweet.id, 'user_id': self.bob.id})
        self.assertEqual(len(res.data['comments']), 2)

    
    def test_like_set(self):
        tweet = self.create_tweet(self.alex,  "test tweet")
        comment = sample_comment(self.alex, tweet, content='111')
        self.create_like(self.alex, comment)
        self.assertEqual(comment.like_set.count(), 1)

        self.create_like(self.bob, comment)
        self.assertEqual(comment.like_set.count(), 2)


    def test_comment_has_liked(self):

        tweet = self.create_tweet(self.alex,  "test tweet")
        comment = sample_comment(self.alex, tweet, content='111')

        payload = {
            'content_type': 'comment',
            'object_id': comment.id,
        }
        self.bob_client.post(LIKE_BASE_URL, payload)

        comment.refresh_from_db()

        res = self.anonymous_client.get(COMMENT_URL, {'tweet_id': tweet.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['comments'][0]['has_liked'], False)

        res = self.bob_client.get(COMMENT_URL, {'tweet_id': tweet.id, 'user_id': self.bob.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['comments'][0]['has_liked'], True)

    def test_comment_likes_count(self):
        tweet = self.create_tweet(self.alex,  "test tweet")
        comment = sample_comment(self.alex, tweet, content='111')

        payload = {
            'content_type': 'comment',
            'object_id': comment.id,
        }
        self.bob_client.post(LIKE_BASE_URL, payload)

        res = self.anonymous_client.get(COMMENT_URL, {'tweet_id': tweet.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['comments'][0]['likes_count'], 1)

        self.alex_client.post(LIKE_BASE_URL, payload)
        res = self.anonymous_client.get(COMMENT_URL, {'tweet_id': tweet.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['comments'][0]['likes_count'], 2)

    
    def test_comments_count_with_cache(self):
        tweet_url = '/api/tweets/{}/'.format(self.tweet.id)
        res = self.alex_client.get(tweet_url)
        self.assertEqual(self.tweet.comments_count, 0)
        self.assertEqual(res.data['comments_count'], 0)

        data = {'tweet_id': self.tweet.id, 'content': 'a comment'}
        for i in range(2):
            user = self.create_user('user{}'.format(i))
            user_client = APIClient()
            user_client.force_authenticate(user)

            user_client.post(COMMENT_URL, data)

            res = user_client.get(tweet_url)
            self.assertEqual(res.data['comments_count'], i+1)
            self.tweet.refresh_from_db()
            self.assertEqual(self.tweet.comments_count, i+1)

        comment_data = self.bob_client.post(COMMENT_URL, data).data
        res = self.bob_client.get(tweet_url)
        self.assertEqual(res.data['comments_count'], 3)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 3)

        # update comment shouldn't update comments_count
        comment_url = '{}{}/'.format(COMMENT_URL, comment_data['id'])
        res = self.bob_client.put(comment_url, {'content': 'updated'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)    
        res = self.bob_client.get(tweet_url)
        self.assertEqual(res.data['comments_count'], 3)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 3)

        # delete a comment will update comments_count
        res = self.bob_client.delete(comment_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.bob_client.get(tweet_url)
        self.assertEqual(res.data['comments_count'], 2)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 2)
