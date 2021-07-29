from utils.listeners import invalidate_object_cache

def incr_comments_count(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F

    if not created:
        return 

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        return
    tweet = instance.content_object
    Tweet.objects.filter(id=tweet.id).update(comments_count=F('comments_count')+1)
    invalidate_object_cache(sender=Tweet, instance=instance.tweet)

def decr_comments_count(sender, instance, **kwargs):

    from tweets.models import Tweet
    from django.db.models import F

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        return
    tweet = instance.content_object
    Tweet.objects.filter(id=tweet.id).update(comments_count=F('comments_count')-1)
    invalidate_object_cache(sender=Tweet, instance=instance.tweet)
