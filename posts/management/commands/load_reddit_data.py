import numpy as np
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

                def convert_bool(val):
                    if not val:
                        return False
                    return val == 'TRUE'

                def convert_int(val):
                    if not val:
                        return 0
                    return val

                def process_link_id_and_parent(row):
                    try:
                        if 'link_id' in row and row['link_id'] is not np.nan:
                            row['link_id'] = row['link_id'].split('_')[-1]
                        else:
                            row['link_id'] = row['permalink'].split('/')[6]

                        if 'parent_id' in row and row['parent_id'] is not np.nan:
                            row['parent_id'] = row['parent_id'].split('_')[-1]
                        else:
                            row['parent_id'] = row['permalink'].split('/')[6]

                        return row

                    except Exception as e:
                        print(row)
                        print(e)

                df = pd.read_csv(file, converters={'num_comments': convert_int, 'is_submitter': convert_bool,
                                                   'is_self': convert_bool, 'locked': convert_bool,
                                                   'over_18': convert_bool, 'stickied': convert_bool,
                                                   'no_follow': convert_bool})
                df = df.replace('None', None)

                df['subreddit'] = df.loc[0].subreddit
                df['is_op'] = df['item_type'] == 'submission'
                df['edited'] = pd.to_datetime(df['edited'], unit='s')
                df['created_utc'] = pd.to_datetime(df['created_utc'])
                df['created_utc'] = df['created_utc'].dt.tz_localize(tz='UTC')
                df['edited'] = df['edited'].dt.tz_localize(tz='UTC')
                df['scraped_on'] = pd.to_datetime(df['scraped_on'])
                df['scraped_on'] = df['scraped_on'].dt.tz_localize(tz='UTC')
                df = df.apply(process_link_id_and_parent, axis=1)
                df['edited'] = df['edited'].astype(object).where(df['edited'].notnull(), None)

                print('Committing objects to database...')
                utilities.commit_reddit_posts_from_df(df)

        except Exception as e:
            print(f'Could not load Reddit data.', e)
            raise e

        print('Done!')
