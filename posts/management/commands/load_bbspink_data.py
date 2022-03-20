import html

import pandas as pd
from django.core.management import BaseCommand
from tqdm import tqdm

from posts import utilities
from posts.documents import BBSPinkPostDocument
from posts.models import Board, Platform, BBSPinkPost


class Command(BaseCommand):
    help = "Load data from CSV files scraped from BBSPink data."

    def handle(self, *args, **options):
        tqdm.pandas()
        import glob

        files = glob.glob(f'data/bbspink/*.tsv')
        try:
            for file in files:
                print(f'Loading {file}...')

                df = pd.read_csv(file, sep='\t')

                print('Committing objects to database...')
                commit_bbspink_posts_from_df(df)

        except Exception as e:
            print(f'Could not load BBSPink data.', e)
            raise e

        print('Done!')


def commit_bbspink_posts_from_df(df):
    new_posts = []
    for index, row in tqdm(df.iterrows(), total=len(df)):
        bbspink, created = Platform.objects.get_or_create(name='bbspink')
        erobbs, created = Board.objects.get_or_create(name='erobbs', platform=bbspink)

        post = BBSPinkPost(platform=bbspink, board=erobbs, thread_id=row['thread_no'], post_id=row['post_no'],
                           author=row['author'], email=None, poster_hash=row['user_id'], subject=row['subject'],
                           body=row['body'], timestamp=row['date'], tripcode=row['tripcode'], capcode=row['capcode'],
                           is_op=int(row['post_no']) == 1)

    # Source on ES bulk update pattern:
    # https://github.com/django-es/django-elasticsearch-dsl/issues/32#issuecomment-736046572
    posts_created = BBSPinkPost.objects.bulk_create(new_posts)
    posts_ids = [post.id for post in posts_created]
    new_posts_qs = BBSPinkPost.objects.filter(id__in=posts_ids)
    BBSPinkPostDocument().update(new_posts_qs)

    return posts_ids
