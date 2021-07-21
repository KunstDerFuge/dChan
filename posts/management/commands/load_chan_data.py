from csv import DictReader
from django.core.management import BaseCommand

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

        print('Loading chan data...')

        new_posts = []

        for platform in ['4chan', '8chan', '8kun']:
            try:
                for row in DictReader(open(platform + '.csv')):
                    processed_body = parse_formatting(row['body_text'])
                    post = Post(platform=platform, board=row['board'], thread_id=row['thread_no'],
                                post_id=row['post_no'], author=row['name'], subject=row['subject'], body=processed_body,
                                timestamp=row['timestamp'], tripcode=row['tripcode'],
                                is_op=(row['post_no'] == row['thread_no']))
                    new_posts.append(post)
            except Exception as e:
                print(f'Could not load {platform} data.', e)

        num_objects = len(new_posts)
        print(f'Finished creating post objects. Committing {num_objects} objects to database...')

        # Split list into groups of 10,000
        # from https://www.w3resource.com/python-exercises/itertools/python-itertools-exercise-40.php
        post_chunks = split_list(new_posts, 10000)
        for chunk in post_chunks:
            Post.objects.bulk_create(chunk)
            num_objects -= 10000
            if num_objects > 0:
                print(f'{num_objects} objects remaining...')

        print('Done!')
