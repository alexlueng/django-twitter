from newsfeeds.models import NewsFeed
from friendships.models import Friendships

class FriendshipService(object):

    @classmethod
    def get_followers(cls, user):
        friendships = Friendships.objects.filter(to_user=user).prefetch_related('from_user')
        return [friendship.from_user for friendship in friendships ]

class NewsFeedService(object):
    @classmethod
    def fanout_to_followers(cls, tweet):
        newsfeeds = [
            NewsFeed(user=follower, tweet=tweet)
            for follower in FriendshipService.get_followers(tweet.user)
        ]
        newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
        NewsFeed.objects.bulk_create(newsfeeds)
