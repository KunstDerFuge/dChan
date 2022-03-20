from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Post, Board, Platform, Drop, Subreddit, RedditPost, BBSPinkPost


@registry.register_document
class PostDocument(Document):
    
    platform = fields.ObjectField(properties={
        'name': fields.TextField()
    })
    board = fields.ObjectField(properties={
        'name': fields.TextField()
    })
    drop = fields.NestedField(properties={
        'number': fields.IntegerField()
    })

    def get_queryset(self):
        return super(PostDocument, self).get_queryset().select_related('platform', 'board', 'drop')

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Platform) or isinstance(related_instance, Board):
            return related_instance.posts.all()

        if isinstance(related_instance, Drop):
            return related_instance.post

    class Index:
        # Name of the Elasticsearch index
        name = 'posts'
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = Post  # The model associated with this Document

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'thread_id',
            'post_id',
            'is_op',
            'author',
            'poster_hash',
            'subject',
            'body',
            'timestamp',
            'tripcode',
            'created_at',
            'last_modified'
        ]
        related_models = [Platform, Board, Drop]


@registry.register_document
class RedditPostDocument(Document):
    platform = fields.ObjectField(properties={
        'name': fields.TextField()
    })
    subreddit = fields.ObjectField(properties={
        'name': fields.TextField()
    })

    def get_queryset(self):
        return super(RedditPostDocument, self).get_queryset().select_related('subreddit')

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Subreddit):
            return related_instance.posts.all()

    class Index:
        # Name of the Elasticsearch index
        name = 'reddit_posts'
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = RedditPost  # The model associated with this Document

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'timestamp',
            'edited',
            'link_id',
            'parent_id',
            'thread_hash',
            'score',
            'is_op',
            'author',
            'subject',
            'body',
            'locked',
            'post_hint'
        ]
        related_models = [Subreddit]


@registry.register_document
class BBSPinkPostDocument(Document):
    platform = fields.ObjectField(properties={
        'name': fields.TextField()
    })
    board = fields.ObjectField(properties={
        'name': fields.TextField()
    })

    def get_queryset(self):
        return super(BBSPinkPostDocument, self).get_queryset().select_related('board')

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Board):
            return related_instance.posts.all()

    class Index:
        # Name of the Elasticsearch index
        name = 'bbspink_posts'
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = BBSPinkPost  # The model associated with this Document

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'thread_id',
            'post_id',
            'author',
            'poster_hash',
            'subject',
            'body',
            'timestamp',
            'tripcode',
            'capcode',
            'is_op'
        ]
        related_models = [Board]
