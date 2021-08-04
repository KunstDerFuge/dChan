from csv import DictReader
from django.core.management import BaseCommand
from tqdm import tqdm
import re

from posts.models import Post, Platform


class Command(BaseCommand):
    help = "Process >>links and store their full URLs for fast retrieval"

    def handle(self, *args, **options):
        fourch = Platform.objects.get(name='4chan')
        posts = Post.objects.filter(platform=fourch)
        for post in tqdm(posts):
            post.process_links()
