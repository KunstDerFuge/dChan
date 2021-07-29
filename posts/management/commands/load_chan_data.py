import html as html_
import re

import pandas as pd
from django.core.management import BaseCommand
from tqdm import tqdm

from posts.models import Post


def parse_formatting(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Process green text
    for result in soup.find_all(attrs={'class': 'quote'}):
        result.insert(0, '> ')

    # Process red text
    for result in soup.find_all(attrs={'class': 'heading'}):
        result.insert_before('==')
        result.insert_after('==')

    # Process bold text
    for result in soup.find_all('strong'):
        result.insert_before("'''")
        result.insert_after("'''")

    # Process italic text
    for result in soup.find_all('em'):
        if result.get_text() != '//':  # For some reason, the // in URLs is wrapped with <em />
            result.insert_before("''")
            result.insert_after("''")

    # Process underlined text
    for result in soup.find_all('u'):
        result.insert_before("__")
        result.insert_after("__")

    # Process strikethrough text
    for result in soup.find_all('s'):
        result.insert_before("~~")
        result.insert_after("~~")

    # Process spoiler text
    for result in soup.find_all(attrs={'class': 'spoiler'}):
        result.insert_before("**")
        result.insert_after("**")

    final_text = '\n'.join([line.get_text() for line in soup.find_all(attrs={'class': 'body-line'})])
    return final_text


def process_links(row):
    links = dict()
    board_index_links = re.findall(r'\"\/([a-zA-Z0-9]+)\/index\.html\">(&gt;&gt;[0-9]+|&gt;&gt;&gt;/[a-zA-Z]+/)',
                                   row['body_text'])
    matches = re.findall(
        r'\"\/([a-zA-Z0-9]+)\/res\/([0-9]+)\.html#q?([0-9]+)\">(&gt;&gt;[0-9]+|&gt;&gt;&gt;/[a-zA-Z]+/[0-9]+)',
        row['body_text'])
    matches.extend(board_index_links)
    if len(matches) == 0:
        return dict()
    else:
        for match in matches:
            if len(match) == 2:
                # Board index link
                links[html_.unescape(match[-1])] = f"/{match[0]}/"
            elif match[1] == match[2]:
                # Special logic for OP post URLs
                links[html_.unescape(match[-1])] = f"{row['platform']}/{match[0]}/res/{match[1]}.html"
            else:
                links[html_.unescape(match[-1])] = f"{row['platform']}/{match[0]}/res/{match[1]}.html#{match[2]}"
    return links


def split_list(lst, n):
    from itertools import islice
    lst = iter(lst)
    result = iter(lambda: tuple(islice(lst, n)), ())
    return list(result)


class Command(BaseCommand):
    help = "Load data from CSV files scraped from Chan data. Expects three files, 4chan.csv, 8chan.csv, 8kun.csv"

    def handle(self, *args, **options):
        if Post.objects.exists():
            delete = input('Data already in database. Delete all data first? (y/n)\n')
            if delete == 'y':
                Post.objects.all().delete()

        tqdm.pandas()
        import glob

        for platform in ['4chan', '8chan', '8kun']:
            print(f'Loading {platform} data...')
            files = glob.glob(f'data/{platform}/*.csv')
            try:
                for file in files:
                    print(f'Loading {file}...')
                    df = pd.read_csv(file)
                    df['platform'] = platform

                    print('Processing links...')
                    df['links'] = df.progress_apply(process_links, axis=1)

                    print('Parsing HTML to imageboard markup...')
                    df['body_text'] = df.body_text.progress_apply(parse_formatting)
                    df = df.fillna('')

                    print('Committing objects to database...')
                    new_posts = []
                    for index, row in tqdm(df.iterrows(), total=len(df)):
                        post = Post(platform=row['platform'], board=row['board'], thread_id=row['thread_no'],
                                    post_id=row['post_no'], author=row['name'], poster_hash=row['poster_id'],
                                    subject=row['subject'], body=row['body_text'], timestamp=row['timestamp'],
                                    tripcode=row['tripcode'], is_op=(row['post_no'] == row['thread_no']),
                                    links=row['links'])
                        new_posts.append(post)
                        if len(new_posts) >= 10000:
                            Post.objects.bulk_create(new_posts)
                            new_posts = []

                    Post.objects.bulk_create(new_posts)

            except Exception as e:
                print(f'Could not load {platform} data.', e)

        print('Done!')
