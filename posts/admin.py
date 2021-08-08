from django.contrib import admin

from posts.models import Post, ScrapeJob, Board, Platform

admin.site.register(Post)
admin.site.register(ScrapeJob)
admin.site.register(Platform)
admin.site.register(Board)
