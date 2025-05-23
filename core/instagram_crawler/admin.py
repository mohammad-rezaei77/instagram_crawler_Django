from django.contrib import admin

from .models import Log, Post, PostItem, Session


class SessionAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "is_block",
        "is_temp_block",
        "is_challenge",
        "number_of_use",
        "create_at",
        "last_use_at",
    )
    list_filter = ("is_block", "is_temp_block", "is_challenge")
    search_fields = ("username",)
    actions = ["block_sessions", "temp_block_sessions", "hit_challenge_sessions"]

    @admin.action(description="Block selected sessions")
    def block_sessions(self, request, queryset):
        queryset.update(is_block=True)

    @admin.action(description="Temporarily block selected sessions")
    def temp_block_sessions(self, request, queryset):
        queryset.update(is_temp_block=True)

    @admin.action(description="Mark selected sessions as challenge")
    def hit_challenge_sessions(self, request, queryset):
        queryset.update(is_challenge=True)


class PostAdmin(admin.ModelAdmin):
    list_display = ("profile", "session", "loading_time", "create_at")
    list_filter = ("session", "create_at")
    search_fields = ("profile", "session__username")


class LogAdmin(admin.ModelAdmin):
    list_display = ("spot", "content", "create_date")
    search_fields = ("spot", "content")


class PostItemAdmin(admin.ModelAdmin):
    list_display = ("content",)
    list_filter = ("post",)


admin.site.register(PostItem, PostItemAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Log, LogAdmin)
