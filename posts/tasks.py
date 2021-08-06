import re

from celery import shared_task
import pandas as pd

from posts.models import Post, ScrapeJob


@shared_task
def scrape_posts():
    pass


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
            .values_list('platform__name', 'board__name', 'thread_id')
            .distinct(), columns=['platform', 'board', 'thread_id'])

    def to_local_url(row_):
        return f'/{row_.platform}/{row_.board}/res/{row_.thread_id}.html'

    # Query all posts in the database and construct their thread URLs
    existing_threads['url'] = existing_threads.apply(to_local_url, axis=1)

    # existing_threads now looks like this:
    #   platform    board   thread_id   url
    #   4chan       pol     146981635   /4chan/pol/res/146981635.html
    #   ...         ...     ...         ...

    # Aggregate links from all threads
    all_links = Post.objects.values_list('links', flat=True)
    all_links = [list(links.values()) for links in all_links]
    all_threads = []
    for links in all_links:
        all_threads.extend(links)

    # Find every thread link that isn't already in the database
    all_threads = pd.Series([thread.split('#')[0] for thread in all_threads if thread not in existing_threads['url']])

    # Find the link count of each unarchived thread; this becomes its "bounty"
    urls = all_threads.value_counts().rename_axis('url').reset_index(name='bounty')

    #                                      url  bounty
    # 0              /8chan/comms/res/283.html   42081
    # 1              /8chan/comms/res/220.html    1422
    # 2         /8chan/qresearch/res/4352.html    1418
    # 3       /8chan/patriotsfight/res/62.html    1323

    # Now change the local URL to an actual scrapeable archive URL and parse out platform, board, and thread number
    pattern = re.compile(r'/([0-9a-z]+)/([a-z]+)/res/([0-9]+)')

    def parse_url_to_archive_url(row_):
        try:
            match = re.match(pattern, row_['url']).groups()
            platform = match[0]
            board = match[1]
            thread_id = match[2]
            if platform == '4chan':
                return  # Not yet implementing 4plebs auto-scraping
            sites = {'8chan': 'https://8ch.net', '8kun': 'https://8kun.top'}
            final_url = f'https://archive.today/newest/{sites[platform]}/{board}/res/{thread_id}.html'
            return platform, board, thread_id, final_url, row_['bounty']

        except Exception as e:
            print('Failed on row:')
            print(row_)
            print(e)

    archive_info = pd.DataFrame.from_records(urls.apply(parse_url_to_archive_url, axis=1),
                                             columns=['platform', 'board', 'thread_id', 'url', 'bounty'])

    # Create scrape jobs for these unarchived URLs if not existing; else update bounty
    new_jobs = 0
    for index, row in archive_info.iterrows():
        obj, created = ScrapeJob.objects.update_or_create(url=row['url'], defaults={
            'bounty': row['bounty'],
            'platform': row['platform'],
            'board': row['board'],
            'thread_id': row['thread_id']
        })
        if created:
            new_jobs += 1

    print(f'Created {new_jobs} new jobs.')
