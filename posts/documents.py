from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Post, Board, Platform, Drop


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
