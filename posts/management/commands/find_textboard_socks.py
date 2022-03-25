from datetime import datetime

import pandas as pd
from django.core.management import BaseCommand
from tqdm import tqdm
from pytz import timezone

from posts.documents import TextboardPostDocument
from posts.models import Board, Platform, TextboardPost


class Command(BaseCommand):
    help = "Find posts which may be socks of trip posters"

    def handle(self, *args, **options):
        thread_ids = TextboardPost.objects.values_list('thread_id', flat=True).distinct()
        for thread in tqdm(thread_ids):
            posts = TextboardPostDocument.search().query('match', thread_id=thread).extra(size=1000).to_queryset()
            hashes_and_tripcodes = set(posts.values_list('poster_hash', 'tripcode'))
            hash_tripcodes_map = dict()
            for poster_hash, tripcode in hashes_and_tripcodes:
                if tripcode is None:
                    continue
                if poster_hash not in hash_tripcodes_map:
                    hash_tripcodes_map[poster_hash] = [tripcode]
                else:
                    hash_tripcodes_map[poster_hash].append(tripcode)

            for post in posts:
                if not post.tripcode:
                    if post.poster_hash in hash_tripcodes_map:
                        if post.poster_hash not in ['???', '???0', 'CAP_USER', '', None]:
                            post.sock_of = hash_tripcodes_map[post.poster_hash]
                            post.save()
