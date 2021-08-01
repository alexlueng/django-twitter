from newsfeeds.constants import FANOUT_BATCH_SIZE
from celery import shared_task
from friendships.services import FriendshipService
from .models import NewsFeed
from tweets.models import Tweet
from utils.time_constants import ONE_HOUR

@shared_task(routing_key='newsfeeds', time_limit=ONE_HOUR)
def fanout_newsfeeds_batch_task(tweet_id, follower_ids):
    from newsfeeds.services import NewsFeedService

    # tweet = Tweet.objects.get(id=tweet_id)
    newsfeeds = [
        NewsFeed(user_id=follower_id, tweet_id=tweet_id)
        for follower_id in follower_ids
    ]

    print('created newsfeeeeeeds: ', newsfeeds)
    # newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
    NewsFeed.objects.bulk_create(newsfeeds)

    for newsfeed in newsfeeds:
        NewsFeedService.push_newsfeed_to_cache(newsfeed)

    return "{} newsfeeds created".format(len(newsfeeds))

@shared_task(routing_key='default', time_limit=ONE_HOUR)
def fanout_newsfeeds_main_task(tweet_id, tweet_user_id):
    NewsFeed.objects.create(user_id=tweet_user_id, tweet_id=tweet_id)

    follower_ids = FriendshipService.get_follower_ids(tweet_user_id)
    # print('follower_ids: ', follower_ids)
    index = 0
    while index < len(follower_ids):
        batch_ids = follower_ids[index: index+FANOUT_BATCH_SIZE]
        fanout_newsfeeds_batch_task.delay(tweet_id, batch_ids)
        index += FANOUT_BATCH_SIZE

    return '{} newsfeeds going to fanout, {} batches created.'.format(
        len(follower_ids),
        (len(follower_ids)-1) // FANOUT_BATCH_SIZE + 1,
    )