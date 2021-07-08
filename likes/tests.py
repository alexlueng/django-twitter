from testing.testcases import TestCase
from django.contrib.contenttypes.models import ContentType
from .models import Like

class LikeModelTest(TestCase):

    def test_like_str(self):
        user = self.create_user('alex')
        tweet = self.create_tweet(user)
        comment = self.create_comment(user, tweet, 'like comment')

        like_tweet_instance, _ = Like.objects.get_or_create(
            user=user,
            content_type=ContentType.objects.get_for_model(tweet),
            object_id=tweet.id
        )
        like_comment_instance, _ = Like.objects.get_or_create(
            user=user,
            content_type=ContentType.objects.get_for_model(comment),
            object_id=comment.id
        )

        print(like_comment_instance)

        self.assertEqual(str(like_tweet_instance), f'{like_tweet_instance.created_at} - {like_tweet_instance.user} liked {like_tweet_instance.content_type} {like_tweet_instance.object_id}')
        self.assertEqual(str(like_comment_instance), f'{like_comment_instance.created_at} - {like_comment_instance.user} liked {like_comment_instance.content_type} {like_comment_instance.object_id}')