import html as html_
import re

import pandas as pd
from bs4 import BeautifulSoup
from django.core.management import BaseCommand
from tqdm import tqdm

from posts import utilities
from posts.models import Platform
from posts.utilities import parse_archive_is


class Command(BaseCommand):
    help = "Load data from CSV files scraped from Chan data. Expects three files, 4chan.csv, 8chan.csv, 8kun.csv"

    def handle(self, *args, **options):
        tqdm.pandas()
        import glob

        for platform in ['4chan', '8chan', '8kun']:
            print(f'Loading {platform} data...')
            platform_obj, created = Platform.objects.get_or_create(name=platform)
            print('Cataloging existing posts in DB...')
            already_archived = set(f'{post[0]}/{post[1]}' for post in
                                   platform_obj.posts.values_list('board__name', 'post_id'))
            files = glob.glob(f'data/{platform}/*.csv')
            try:
                for file in files:
                    print(f'Loading {file}...')
                    df = pd.read_csv(file)
                    if platform == '8chan' and df['board'].loc[0] != 'qresearch':
                        # Scraped from archive.is
                        df = pd.DataFrame(list(df.apply(parse_archive_is, axis=1)))
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df['timestamp'] = df['timestamp'].dt.tz_localize(tz='UTC')  # 8chan timestamps are UTC
                    elif platform == '4chan':
                        # Rename columns
                        df['thread_no'] = df['thread_num']
                        df['post_no'] = df['num']
                        df['poster_id'] = df['poster_hash']
                        df['subject'] = df['title']
                        df['body_text'] = df['comment']
                        df['tripcode'] = df['trip']
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                        df['timestamp'] = df['timestamp'].dt.tz_localize(tz='UTC')  # 4plebs timestamps are UTC
                        df = df[['thread_no', 'post_no', 'poster_id', 'subject', 'body_text', 'tripcode', 'timestamp',
                                 'name', 'board']]

                    before = len(df)
                    df['post_no'] = df['post_no'].astype(str)
                    df['thread_no'] = df['thread_no'].astype(str)
                    df = df.drop_duplicates()
                    after = len(df)
                    if after - before > 0:
                        print(f'Dropped {after - before} duplicates...')
                    df['id'] = df['board'] + '/' + df['post_no'].astype(str)
                    df['platform'] = platform
                    size_before = len(df)
                    # Remove if already archived
                    df = df[~df.id.isin(already_archived)]
                    size_after = len(df)
                    df = df.reset_index()
                    saved = size_before - size_after
                    if size_after == 0:
                        print('Already archived all posts.')
                        continue
                    elif size_after != size_before:
                        print(f'Already archived {saved} of {size_before} posts.')

                    if platform != '4chan':  # No format or link info from 4plebs API
                        print('Processing links...')
                        df['links'] = df.progress_apply(process_links, axis=1)

                        print('Parsing HTML to imageboard markup...')
                        if platform == '8chan' and df['board'].loc[0] != 'qresearch':
                            df['body_text'] = df.body_text.progress_apply(parse_8chan_formatting)
                        else:
                            df['body_text'] = df.body_text.progress_apply(parse_formatting)
                    df = df.fillna('')

                    print('Committing objects to database...')
                    utilities.commit_posts_from_df(df, platform_obj)

            except Exception as e:
                print(f'Could not load {platform} data.', e)
                raise e

        print('Done!')
        print('Remember to re-generate SearchVectors with python manage.py process_search_vectors')
