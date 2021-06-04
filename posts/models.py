from django.db import models


class Post(models.Model):
    platform = models.CharField(max_length=12)
    thread_id = models.IntegerField()
    post_id = models.IntegerField(primary_key=True)
    author = models.CharField(max_length=180)
    subject = models.CharField(max_length=150)
    body = models.TextField()
    timestamp = models.DateTimeField()
    is_op = models.BooleanField(default=False)
