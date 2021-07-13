from .models import TweetPhoto

class TweetService(object):

    @classmethod
    def create_photos_from_files(cls, tweet, files):
        photos = []
        for index, file in enumerate(files):
            photo = TweetPhoto(
                user=tweet.user,
                tweet=tweet,
                file=file,
                order=index,
            )
            photos.append(photo)

        TweetPhoto.objects.bulk_create(photos)