import re
from datetime import datetime, timedelta

import pandas as pd
from celery import shared_task
from scrapyd_api import ScrapydAPI

from posts.documents import PostDocument
from posts.models import Post, ScrapeJob, Platform, Board

scrapyd = ScrapydAPI('http://localhost:6800')


@shared_task
def scrape_posts():
    try:
        # Grab top 30 8kun scrape jobs by bounty
        eightkun_jobs = ScrapeJob.objects.filter(platform='8kun', error_count__lt=2, in_progress=False) \
                            .order_by('-bounty')[:25]

        # Grab top 30 archive.is jobs by bounty
        archive_is_jobs = ScrapeJob.objects.filter(url__contains='archive.', error_count__lt=2, in_progress=False) \
                              .order_by('-bounty')[:5]

        # Create scrapyd task to scrape the 8kun posts
        task = scrapyd.schedule('scrapy_project', '8kun_spider', jobs=','
                                .join([f'{pk}' for pk in eightkun_jobs.values_list('pk', flat=True)]))

        # Create scrapyd task to scrape the archive.is posts
        task = scrapyd.schedule('scrapy_project', 'archive_is_spider', jobs=','
                                .join([f'{pk}' for pk in archive_is_jobs.values_list('pk', flat=True)]))

    except Exception as e:
        print(e)


@shared_task
def create_scrape_jobs():
    # Have archived threads been updated since we last created scrape jobs?
    try:
        last_scrape_job = ScrapeJob.objects.order_by('-created_at').first().created_at
        last_data_update = Post.objects.order_by('-last_modified').first().last_modified

        if last_scrape_job > last_data_update:
            print('No new jobs needed.')
            return

    except Exception as e:
        # Either no Posts or no ScrapeJobs, which is fine, let's move on
        pass

    existing_threads = pd.DataFrame(
        Post.objects.all()
            .filter(is_op=True)
            .values_list('platform__name', 'board__name', 'thread_id')
            .distinct(), columns=['platform', 'board', 'thread_id'])

    def to_local_url(row_):
        if row_.platform == '8chan' or row_.platform == '8kun':
            # Ignore platform; treat 8chan/8kun as single platform
            return f'/{row_.board}/res/{row_.thread_id}.html'
        return f'/{row_.platform}/{row_.board}/res/{row_.thread_id}.html'

    # Query all posts in the database and construct their thread URLs
    existing_threads['url'] = existing_threads.apply(to_local_url, axis=1)
    existing_threads_set = set(existing_threads.url.unique())

    # existing_threads now looks like this:
    #   platform    board   thread_id   url
    #   4chan       pol     146981635   /4chan/pol/res/146981635.html
    #   ...         ...     ...         ...

    total_posts = Post.objects.count()
    num_batches = 8
    batch_size = total_posts // num_batches
    unarchived_threads = []

    for i in range(num_batches):
        # Aggregate links from all threads
        all_links = Post.objects.values_list('links', flat=True)[i * batch_size: i * batch_size + batch_size]
        all_links = [list(links.values()) for links in all_links]
        all_threads = []
        for links in all_links:
            all_threads.extend(links)

        def get_thread_url(url):
            return url.split('#')[0]

        # We're going to check if we need to scrape this thread, so if it comes from 8chan/8kun,
        # we'll check if we've already scraped it from the other site.
        def process_if_8kun(thread):
            if thread.startswith('/8chan') or thread.startswith('/8kun'):
                without_first_slash = thread[1:]
                slash_index = without_first_slash.find('/')
                return without_first_slash[slash_index:]
            return thread

        # Find every thread link that isn't already in the database
        all_threads = pd.Series(all_threads).to_frame('url')
        all_threads['url'] = all_threads.url.apply(get_thread_url)  # Strip off the hash part of the URLs
        all_threads['processed'] = all_threads.url.apply(process_if_8kun)
        unarchived = all_threads[~all_threads.processed.isin(existing_threads_set)]
        unarchived_threads.extend(unarchived.url)

    # Find the link count of each unarchived thread; this becomes its "bounty"
    urls = pd.Series(unarchived_threads).value_counts().rename_axis('url').reset_index(name='bounty')
    urls = urls.dropna()
    print('URLs to scrape:')
    print(urls)

    #                                      url  bounty
    # 0              /8chan/comms/res/283.html   42081
    # 1              /8chan/comms/res/220.html    1422
    # 2         /8chan/qresearch/res/4352.html    1418
    # 3       /8chan/patriotsfight/res/62.html    1323

    # Now change the local URL to an actual scrapeable archive URL and parse out platform, board, and thread number
    migrated_boards = Board.objects.filter(platform=Platform.objects.get(name='8chan'),
                                           migrated_to_8kun=True).values_list('name', flat=True)
    echan_boards = Board.objects.filter(platform=Platform.objects.get(name='8chan')).values_list('name', flat=True)
    pattern = re.compile(r'/([a-z]+)/res/([0-9]+)')

    def parse_url_to_archive_url(row_):
        try:
            match = re.match(pattern, row_['url']).groups()
            board = match[0]
            platform = '8kun'
            thread_id = match[1]
            sites = {'8chan': 'https://archive.today/newest/https://8ch.net', '8kun': 'https://8kun.top'}
            final_url = f'{sites[platform]}/{board}/res/{thread_id}.html'
            return platform, board, thread_id, final_url, row_['bounty']

        except Exception as e:
            print('Failed on row:')
            print(row_)
            print(e)

    try:
        urls = urls.apply(parse_url_to_archive_url, axis=1)
        urls = urls.dropna().reset_index(drop=True)
        archive_info = pd.DataFrame.from_records(urls, columns=['platform', 'board', 'thread_id', 'url', 'bounty'])

        archive_info = archive_info.dropna()

    except Exception as e:
        print('Exception creating dataframe. Data:')
        print(urls)
        print(e)
        raise e

    # Create scrape jobs for these unarchived URLs if not existing; else update bounty
    new_jobs = 0
    for index, row in archive_info.iterrows():
        try:
            obj, created = ScrapeJob.objects.update_or_create(platform=row['platform'], board=row['board'],
                                                              thread_id=row['thread_id'],
                                                              defaults={
                                                                  'bounty': row['bounty'],
                                                                  'url': row['url'],
                                                              })
            if created:
                new_jobs += 1

        except Exception as e:
            print(e)

    print(f'Created {new_jobs} new jobs.')


@shared_task
def revisit_recent_threads(days=14):
    now = datetime.now()
    two_weeks_ago = now - timedelta(days=days)
    s = PostDocument().search()
    needs_revisited = pd.DataFrame(s.query('range', timestamp={'gte': two_weeks_ago})
                                   .query('match', is_op=True)
                                   .extra(size=10000)
                                   .to_queryset()
                                   .values_list('board__name', 'thread_id'), columns=['board', 'thread_id'])

    def get_scrape_url(_row):
        return f'https://8kun.top/{_row.board}/res/{_row.thread_id}.html'

    def check_if_full(_row):
        archived_posts_count = s.query('match', board__name=_row.board) \
            .query('match', thread_id=_row.thread_id).count()
        if archived_posts_count >= 752:
            return True
        return False

    needs_revisited['full'] = needs_revisited.apply(check_if_full, axis=1)
    needs_revisited['url'] = needs_revisited.apply(get_scrape_url, axis=1)

    new_jobs = 0
    for index, row in needs_revisited.iterrows():
        if row['full']:
            continue
        try:
            obj, created = ScrapeJob.objects.update_or_create(url=row['url'], defaults={
                'bounty': 10,
                'platform': '8kun',
                'board': row['board'],
                'thread_id': row['thread_id']
            })
            if created:
                new_jobs += 1

        except Exception as e:
            print(e)

    print(f'Created {new_jobs} new jobs.')


@shared_task
def sync_elasticsearch():
    now = datetime.now()
    half_hour_ago = now - timedelta(minutes=30)
    recently_scraped = Post.objects.filter(created_at__gte=half_hour_ago)
    PostDocument().update(recently_scraped)
