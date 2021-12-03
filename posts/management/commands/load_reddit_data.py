import pandas as pd
from django.core.management import BaseCommand
from tqdm import tqdm

from posts import utilities
from posts.models import Platform
from posts.utilities import parse_archive_is, process_links, parse_8chan_formatting, parse_formatting


class Command(BaseCommand):
    help = "Load data from CSV files scraped from Reddit data."

    def handle(self, *args, **options):
        tqdm.pandas()
        import glob

        files = glob.glob(f'data/reddit/*.csv')
        try:
            for file in files:
                print(f'Loading {file}...')

                df = pd.read_csv(file)
                # Rename columns
                df['is_op'] = df['item_type'] == 'submission'
                df['edited'] = pd.to_datetime(df['edited'], unit='s')
                df['created_utc'] = df['created_utc'].dt.tz_localize(tz='UTC')
                df['edited'] = df['edited'].dt.tz_localize(tz='UTC')
                if 'link_id' not in df or not df['link_id']:
                    df['link_id'] = df['url'].split('/')[6]
                else:
                    df['link_id'] = df['link_id'].split('_')[-1]

                if 'parent_id' not in df:
                    df['parent_id'] = None
                print('Committing objects to database...')
                utilities.commit_reddit_posts_from_df(df)

        except Exception as e:
            print(f'Could not load Reddit data.', e)
            raise e

        print('Done!')
