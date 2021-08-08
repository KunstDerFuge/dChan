import re
import time
from random import randrange

import pandas as pd
from celery import shared_task
from scrapyd_api import ScrapydAPI
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from posts import utilities
from posts.management.commands.load_chan_data import parse_archive_is, process_links, parse_8chan_formatting
from posts.models import Post, ScrapeJob, Platform, Board

scrapyd = ScrapydAPI('http://localhost:6800')


def scrape_archive(jobs):
    from selenium import webdriver

    threads_data = dict()

    def do_scrape():
        try:
            options = webdriver.FirefoxOptions()
            options.set_headless()
            driver = webdriver.Firefox(firefox_options=options)
            for job in jobs:
                if job.url in threads_data:
                    # Already scraped this thread in a previous iteration
                    continue

                try:
                    thread_scrape = pd.DataFrame(columns=['platform', 'board', 'thread_no', 'header', 'body'])
                    url = job.url
                    driver.get(url)

                    try:
                        # Did we get a Captcha redirect?
                        captcha = driver.find_element_by_css_selector('h2 span:nth-of-type(1)')
                        if 'Please complete the security check' in captcha.text:
                            # Let's try something a lil shady...
                            print('Attempting to bypass Captcha...')
                            element = WebDriverWait(driver, 20).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.recaptcha-checkbox-checkmark")))

                            time.sleep(1)
                            element.click()
                            time.sleep(15)

                    except Exception:
                        # Not captcha
                        pass

                    op = driver.find_element_by_css_selector('form > div:nth-of-type(1) > div:nth-of-type(2)')
                    comments = driver.find_elements_by_css_selector('form > div > div:nth-of-type(n+3)')

                    # OP
                    thread_scrape = thread_scrape.append({
                        'platform': '8chan',
                        'board': job.board,
                        'thread_no': job.thread_id,
                        'header': op.find_element_by_css_selector('div:nth-of-type(1)').get_attribute('innerHTML'),
                        'body': op.find_element_by_css_selector('div:nth-of-type(2)').get_attribute('innerHTML')
                    }, ignore_index=True)

                    # Comments
                    for comment in comments:
                        thread_scrape = thread_scrape.append({
                            'platform': '8chan',
                            'board': job.board,
                            'thread_no': job.thread_id,
                            'header': comment.find_element_by_css_selector('div:nth-of-type(1)').get_attribute(
                                'innerHTML'),
                            'body': comment.find_element_by_css_selector('div:nth-of-type(3)').get_attribute(
                                'innerHTML')
                        }, ignore_index=True)

                    print('Scraped {} posts from {}/{}...'.format(len(thread_scrape), job.board, job.thread_id))
                    threads_data[job.url] = thread_scrape

                    # Delete the job
                    ScrapeJob.objects.get(url=job.url).delete()

                    time.sleep(randrange(1, 4))

                except Exception as e:
                    print('Exception scraping {}/{}...'.format(job.board, job.thread_id))
                    print(e)
                    job.error_count += 1
                    job.save()
                    pass

        except Exception as e:
            print(e)

        finally:
            driver.quit()
            return True

    done = False

    while not done:
        done = do_scrape()

    print('Done!')
    return threads_data


@shared_task
def scrape_posts():
    try:
        # Grab top 30 8kun scrape jobs by bounty
        eightkun_start_urls = ScrapeJob.objects.filter(platform='8kun', error_count__lt=10) \
                                  .order_by('-bounty') \
                                  .values_list('url', flat=True)[:10]

        print('8kun scrape URLs:')
        print(list(eightkun_start_urls))

        # Create scrapyd task to scrape the 8kun posts
        task = scrapyd.schedule('scrapy_project', '8kun_spider', start_urls=','.join(list(eightkun_start_urls)))

        # Grab top 30 archive.is jobs by bounty
        archive_is_jobs = ScrapeJob.objects.filter(url__contains='archive.', error_count__lt=10) \
                                           .order_by('-bounty')[:3]

        print('8chan scrape URLs:')
        print(archive_is_jobs)

        # Scrape archive.is
        scrape_data = scrape_archive(archive_is_jobs)

        # Process archive.is scrape
        df = pd.concat(list(scrape_data.values()))
        df = pd.DataFrame(list(df.apply(parse_archive_is, axis=1)))
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['timestamp'] = df['timestamp'].dt.tz_localize(tz='UTC')  # 8chan timestamps are UTC
        df['links'] = df.apply(process_links, axis=1)
        df['body_text'] = df.body_text.apply(parse_8chan_formatting)
        new_threads = utilities.commit_posts_from_df(df, Platform.objects.get(name='8chan'))
        utilities.process_replies(new_threads)

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
    urls = urls.dropna()

    #                                      url  bounty
    # 0              /8chan/comms/res/283.html   42081
    # 1              /8chan/comms/res/220.html    1422
    # 2         /8chan/qresearch/res/4352.html    1418
    # 3       /8chan/patriotsfight/res/62.html    1323

    # Now change the local URL to an actual scrapeable archive URL and parse out platform, board, and thread number
    pattern = re.compile(r'/([0-9a-z]+)/([a-z]+)/res/([0-9]+)')

    def parse_url_to_archive_url(row_):
        try:
            migrated_boards = Board.objects.filter(platform=Platform.objects.get(name='8chan'),
                                                   migrated_to_8kun=True).values_list('name', flat=True)
            match = re.match(pattern, row_['url']).groups()
            platform = match[0]
            board = match[1]
            if platform == '8chan' and board in migrated_boards:
                # We can scrape this from 8kun much faster than archive.is
                platform = '8kun'
            thread_id = match[2]
            if platform == '4chan':
                return  # Not yet implementing 4plebs auto-scraping
            sites = {'8chan': 'https://archive.today/newest/https://8ch.net', '8kun': 'https://8kun.top'}
            final_url = f'{sites[platform]}/{board}/res/{thread_id}.html'
            return platform, board, thread_id, final_url, row_['bounty']

        except Exception as e:
            print('Failed on row:')
            print(row_)
            print(e)

    archive_info = pd.DataFrame.from_records(urls.apply(parse_url_to_archive_url, axis=1),
                                             columns=['platform', 'board', 'thread_id', 'url', 'bounty'])

    archive_info = archive_info.dropna()

    # Create scrape jobs for these unarchived URLs if not existing; else update bounty
    new_jobs = 0
    for index, row in archive_info.iterrows():
        try:
            obj, created = ScrapeJob.objects.update_or_create(url=row['url'], defaults={
                'bounty': row['bounty'],
                'platform': row['platform'],
                'board': row['board'],
                'thread_id': row['thread_id']
            })
            if created:
                new_jobs += 1

        except Exception as e:
            print(e)

    print(f'Created {new_jobs} new jobs.')
