import pandas as pd

from posts import utilities
from posts.management.commands.load_chan_data import process_links, parse_formatting
from posts.models import Platform, ScrapeJob


class ScrapyPostPipeline(object):
    def __init__(self, *args, **kwargs):
        self.start_urls = []
        self.posts = []
        self.scraped_urls = set()
        self.df = pd.DataFrame()
        self.platform = Platform.objects.get(name='8kun')

    def open_spider(self, spider):
        self.start_urls = spider.start_urls

    def process_item(self, item, spider):
        self.scraped_urls.add(item['url'])

        self.df = self.df.append(item, ignore_index=True)
        return item

    def close_spider(self, spider):
        self.df['platform'] = '8kun'
        self.df['links'] = self.df.apply(process_links, axis=1)
        self.df['body_text'] = self.df.body_text.apply(parse_formatting)
        new_threads = utilities.commit_posts_from_df(self.df, self.platform)
        utilities.process_replies(new_threads)

        ScrapeJob.objects.filter(url__in=self.scraped_urls).delete()
        failed_urls = [url for url in self.start_urls if url not in self.scraped_urls]
        failed_jobs = ScrapeJob.objects.filter(url__in=failed_urls)
        for job in failed_jobs:
            job.error_count += 1
            job.save()
