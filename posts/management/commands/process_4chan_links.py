from csv import DictReader
from django.core.management import BaseCommand
from tqdm import tqdm
import re

from posts.models import Post


class Command(BaseCommand):
    help = "Process >>links and store their full URLs for fast retrieval"

    def handle(self, *args, **options):
        posts = Post.objects.filter(platform='4chan')
        for post in tqdm(posts):
            post.process_links()
