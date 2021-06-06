from django.contrib import admin
from .models import Friendships

@admin.register(Friendships)
class FriendshipAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'id',
        'from_user',
        'to_user',
        'created_at',
    )