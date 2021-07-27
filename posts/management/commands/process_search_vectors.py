from csv import DictReader

from django.contrib.postgres.search import SearchVector
from django.core.management import BaseCommand
from tqdm import tqdm
import re

from posts.models import Post


class Command(BaseCommand):
    help = "Create search vectors for performant full-text search."

    def handle(self, *args, **options):
        print('Updating search vectors...')
        Post.objects.update(search_vector=SearchVector('body'))
        print('Done!')
