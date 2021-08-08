from django.core.management import BaseCommand
from tqdm import tqdm

from posts.models import Post
from posts.utilities import process_replies


class Command(BaseCommand):
    help = "Process replies to posts and store their full URLs for fast retrieval"

    def handle(self, *args, **options):
        process_replies()
