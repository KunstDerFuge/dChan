from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchVectorField
from django.db import models

from posts.choices import JobType


class ScrapeJob(models.Model):
    platform = models.CharField(max_length=12, null=True, blank=True)
    board = models.CharField(max_length=60, null=True, blank=True)
    thread_id = models.IntegerField(null=True, blank=True)
    url = models.CharField(max_length=120)
    bounty = models.PositiveIntegerField(default=0)
    error_count = models.PositiveSmallIntegerField(default=0)
    in_progress = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    job_type = models.CharField(
        max_length=3,
        choices=JobType.choices,
        default=JobType.NEW,
    )

    class Meta:
        ordering = ['-bounty']
        constraints = [
            models.UniqueConstraint(fields=['platform', 'board', 'thread_id'], name='unique_thread')
        ]

    def __str__(self):
        out = f'Bounty {self.bounty}: {self.url}'
        if self.job_type != JobType.NEW:
            out += f' ({self.job_type})'

        if self.error_count > 0:
            out += f' Errors: {self.error_count}'
        if self.in_progress:
            out += ' IN PROGRESS'
        return out


class Platform(models.Model):
    name = models.CharField(max_length=12, unique=True)

    def __str__(self):
        return self.name


class Board(models.Model):
    name = models.CharField(max_length=60)
    platform = models.ForeignKey('Platform', on_delete=models.CASCADE, related_name='boards')
    migrated_to_8kun = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.platform.name}/{self.name}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['platform', 'name'], name='unique_board')
        ]


class Drop(models.Model):
    number = models.SmallIntegerField(unique=True)
    post = models.OneToOneField('Post', on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return f'Drop {self.number}'


class Post(models.Model):
    platform = models.ForeignKey('Platform', on_delete=models.CASCADE, related_name='posts')
    board = models.ForeignKey('Board', on_delete=models.CASCADE, related_name='posts')
    thread_id = models.IntegerField()
    post_id = models.IntegerField()
    author = models.CharField(max_length=180)
    poster_hash = models.CharField(max_length=12)
    subject = models.CharField(max_length=150)
    body = models.TextField()
    body_html = models.TextField(default='')
    timestamp = models.DateTimeField()
    tripcode = models.CharField(max_length=30, default=None)
    is_op = models.BooleanField(default=False)
    links = models.JSONField(default=dict)
    search_vector = SearchVectorField(null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    replies = models.JSONField(default=dict)
    source = models.CharField(max_length=6, null=True, blank=True)

    def __str__(self):
        return f'{self.platform.name}/{self.board.name}/{self.post_id}'

    def get_thread_url(self):
        if self.platform.name == '4chan':
            return f'/{self.platform.name}/{self.board.name}/res/{self.thread_id}.html'
        else:
            return f'/{self.board.name}/res/{self.thread_id}.html'

    def get_post_url(self):
        return self.get_thread_url() + '#' + str(self.post_id)

    def get_archive_url(self):
        if self.platform.name == '4chan':
            return f'https://archive.4plebs.org/{self.board.name}/thread/{self.thread_id}/#{self.post_id}'
        site = {'8chan': 'https://8ch.net', '8kun': 'https://8kun.top'}
        return f'https://archive.is/{site[self.platform.name]}/{self.board.name}/res/{self.thread_id}.html'

    def get_8kun_url(self):
        return f'https://8kun.top/{self.board.name}/res/{self.thread_id}.html#{self.post_id}'

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
                matched_links[f'>>{link}'] = linked_post.get_post_url()
        self.links = matched_links
        self.save()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['platform', 'board', 'post_id'], name='unique_post'),
        ]


class RedditPost(models.Model):
    platform = models.ForeignKey('Platform', on_delete=models.CASCADE, related_name='reddit_posts')
    timestamp = models.DateTimeField()  # renamed from "created_utc"
    edited = models.DateTimeField(null=True, blank=True, default=None)  # Unix timestamp
    subreddit = models.ForeignKey('Subreddit', on_delete=models.CASCADE, related_name='posts')
    author_flair_text = models.CharField(max_length=64, null=True, default=None)
    stickied = models.BooleanField()
    scraped_on = models.DateTimeField()
    permalink = models.URLField()
    score = models.IntegerField()
    post_hint = models.CharField(max_length=12, null=True)  # None, link, rich:video, hosted:video, self, image
    subject = models.CharField(max_length=400)  # renamed from "title"
    author = models.CharField(max_length=24)
    author_fullname = models.CharField(max_length=14)
    body = models.TextField()  # renamed from 'text'
    url = models.URLField(null=True, max_length=2000)
    no_follow = models.BooleanField()
    locked = models.BooleanField()
    is_op = models.BooleanField()  # item_type == 'submission'
    is_submitter = models.BooleanField()
    is_self = models.BooleanField()
    num_comments = models.PositiveIntegerField()
    link_id = models.CharField(max_length=10, unique=True)
    parent_id = models.CharField(max_length=10, null=True)
    thread_hash = models.CharField(max_length=10)
    thread_slug = models.CharField(max_length=60)

    def get_thread_url(self):
        url = '/'.join(self.permalink.split('/')[3:])
        return f'/{url}'


class Subreddit(models.Model):
    name = models.CharField(max_length=24)

    def __str__(self):
        return f'/r/{self.name}'


class TextboardPost(models.Model):
    platform = models.ForeignKey('Platform', on_delete=models.CASCADE, related_name='textboard_posts')
    board = models.ForeignKey('Board', on_delete=models.CASCADE, related_name='textboard_posts')
    thread_id = models.IntegerField()
    post_id = models.IntegerField()
    author = models.CharField(max_length=180)
    email = models.CharField(max_length=180, null=True)
    poster_hash = models.CharField(max_length=12, null=True)
    subject = models.CharField(max_length=150, null=True)
    body = models.TextField()
    timestamp = models.DateTimeField(null=True)
    tripcode = models.CharField(max_length=30, default=None, null=True)
    capcode = models.CharField(max_length=30, default=None, null=True)
    is_op = models.BooleanField(default=False)
    sock_of = ArrayField(models.CharField(max_length=30), null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    def get_thread_url(self):
        return f'/{self.platform.name}/read.cgi/{self.board.name}/{self.thread_id}/'

    def get_post_url(self):
        return self.get_thread_url() + f'#{self.post_id}'
