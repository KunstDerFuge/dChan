import pandas as pd

from posts import utilities
from posts.models import Platform, JobType
from posts.utilities import process_replies


class ArchiveIsPipeline(object):
    def process_item(self, item, spider):
        if 'archive.' not in spider.jobs.first().url:
            return item
        else:
            return utilities.parse_archive_is(item)


class ScrapyPostPipeline(object):
    def __init__(self, *args, **kwargs):
        self.start_urls = []
        self.posts = []
        self.scraped_urls = set()
        self.df = pd.DataFrame()

    def open_spider(self, spider):
        self.start_urls = spider.start_urls

    def process_item(self, item, spider):
        if 'url' in item:
            self.scraped_urls.add(item['url'])
        self.df = self.df.append(item, ignore_index=True)
        return item

    def close_spider(self, spider):
        try:
            if len(self.df) == 0:
                return
            self.df['platform'] = spider.platform
            platform_obj = Platform.objects.get(name=spider.platform)
            if spider.platform == '8chan':
                self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
                self.df['timestamp'] = self.df['timestamp'].dt.tz_localize(tz='UTC')  # 8chan timestamps are UTC
            utilities.process_and_commit_from_df(self.df, platform_obj)

        finally:
            failed_urls = [url for url in self.start_urls if url not in self.scraped_urls]
            failed_jobs = spider.jobs.filter(url__in=failed_urls)
            spider.jobs.update(in_progress=False)
            for job in failed_jobs:
                job.error_count += 1
                job.save()

            print('Deleting finished jobs...')
            finished_jobs = spider.jobs.filter(url__in=self.scraped_urls)
            threads_to_reprocess = []
            for job in finished_jobs:
                if job.job_type == JobType.REVISIT:
                    threads_to_reprocess.append((job.platform, job.board, job.thread_id))
            process_replies(threads_to_reprocess)
            finished_jobs.delete()
            print('Done!')
