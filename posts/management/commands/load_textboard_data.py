from datetime import datetime

import pandas as pd
from django.core.management import BaseCommand
from tqdm import tqdm
from pytz import timezone

from posts.documents import TextboardPostDocument
from posts.models import Board, Platform, TextboardPost


class Command(BaseCommand):
    help = "Load data from CSV files scraped from textboard data."

    def handle(self, *args, **options):
        tqdm.pandas()
        import glob

        for platform in ['2ch', 'bbspink']:
            files = glob.glob(f'data/{platform}/*.tsv')
            if platform == '2ch':
                board_name = 'operate'
            else:
                board_name = 'erobbs'
            try:
                for file in files:
                    print(f'Loading {file}...')

                    df = pd.read_csv(file, sep='\t')
                    df = df.astype(object).where(pd.notnull(df), None)
                    df['author'] = df.author.where(pd.notnull(df.author), '')
                    df['body'] = df.body.where(pd.notnull(df.body), '')

                    print('Committing objects to database...')
                    commit_textboard_posts_from_df(df, platform, board_name)

            except Exception as e:
                print(f'Could not load BBSPink data.', e)
                raise e

            print('Done!')


def commit_textboard_posts_from_df(df, platform_name, board_name):
    new_posts = []
    for index, row in tqdm(df.iterrows(), total=len(df)):
        platform, created = Platform.objects.get_or_create(name=platform_name)
        board, created = Board.objects.get_or_create(name=board_name, platform=platform)

        jst = timezone('Asia/Tokyo')
        if type(row['date']) != str:
            date = None
        else:
            try:
                date = jst.localize(datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S'))
            except Exception as e:
                print('Failed on date')
                print(row['date'])
                raise

        post = TextboardPost(platform=platform, board=board, thread_id=row['thread_no'], post_id=row['post_no'],
                             author=row['author'], email=None, poster_hash=row['user_id'], subject=row['subject'],
                             body=row['body'], timestamp=date, tripcode=row['tripcode'], capcode=row['capcode'],
                             is_op=int(row['post_no']) == 1)

        new_posts.append(post)

    # Source on ES bulk update pattern:
    # https://github.com/django-es/django-elasticsearch-dsl/issues/32#issuecomment-736046572
    try:
        posts_created = TextboardPost.objects.bulk_create(new_posts, ignore_conflicts=True)
    except Exception as e:
        print(e)
        print('Failed on row:')
        print(row)
        raise e
    posts_ids = [post.id for post in posts_created]
    new_posts_qs = TextboardPost.objects.filter(id__in=posts_ids)
    TextboardPostDocument().update(new_posts_qs)

    return posts_ids
