from django.db import models


class Post(models.Model):
    platform = models.CharField(max_length=12)
    board = models.CharField(max_length=60)
    thread_id = models.IntegerField()
    post_id = models.IntegerField()
    author = models.CharField(max_length=180)
    subject = models.CharField(max_length=150)
    body = models.TextField()
    timestamp = models.DateTimeField()
    tripcode = models.CharField(max_length=30, default=None)
    is_op = models.BooleanField(default=False)
    links = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['platform', 'board', 'post_id'], name='unique_post')
        ]
