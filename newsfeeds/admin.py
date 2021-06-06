from django.contrib import admin
from .models import NewsFeed


@admin.register(NewsFeed)
class NewsFeedAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'created_at',
        'user',
        'tweet',
    )
