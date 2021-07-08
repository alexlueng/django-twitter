from django.contrib import admin
from .models import Like

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'user', 'object_id', 'created_at', 'content_object')
    list_filter = ('content_type',)
    date_hierarchy = 'created_at'
