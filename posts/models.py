from django.contrib.postgres.search import SearchVectorField
from django.db import models


class Post(models.Model):
    platform = models.CharField(max_length=12)
    board = models.CharField(max_length=60)
    thread_id = models.IntegerField()
    post_id = models.IntegerField()
    author = models.CharField(max_length=180)
    poster_hash = models.CharField(max_length=12)
    subject = models.CharField(max_length=150)
    body = models.TextField()
    timestamp = models.DateTimeField()
    tripcode = models.CharField(max_length=30, default=None)
    is_op = models.BooleanField(default=False)
    links = models.JSONField(default=dict)
    search_vector = SearchVectorField(null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def get_thread_url(self):
        return f'/{self.platform}/{self.board}/res/{self.thread_id}.html'

    def get_post_url(self):
        return self.get_thread_url() + '#' + str(self.post_id)

    def get_archive_url(self):
        site = {'8chan': 'https://8ch.net', '8kun': 'https://8kun.top'}
        return f'https://archive.is/{site[self.platform]}/{self.board}/res/{self.thread_id}.html'

    def get_8kun_url(self):
        return f'https://8kun.top/{self.board}/res/{self.thread_id}.html#{self.post_id}'

    def process_links(self):
        import re
        matched_links = dict()
        links = re.findall(r'>>([0-9]+)', self.body)
        for link in links:
            # Did we already match this link?
            if link in matched_links:
                continue
            # Have we archived this post?
            try:
                linked_post = Post.objects.get(platform=self.platform, board=self.board, post_id=link)
            except Exception:
                linked_post = None
            if linked_post is not None:
                matched_links[link] = linked_post.get_post_url()
        self.links = matched_links
        self.save()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['platform', 'board', 'post_id'], name='unique_post')
        ]
