from django.contrib import admin

from posts.models import Post, ScrapeJob

admin.site.register(Post)
admin.site.register(ScrapeJob)
