import scrapy
from scrapy import Request

from posts.models import ScrapeJob


class EightKunSpider(scrapy.Spider):
    name = '8kun_spider'

    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 15,
        'DOWNLOAD_DELAY': 0,
    }

    def __init__(self, *args, **kwargs):
        self.platform = '8kun'
        self.jobs = []
        jobs = kwargs.pop('jobs', [])
        if jobs:
            self.jobs = ScrapeJob.objects.filter(pk__in=jobs.split(','))
            self.jobs.update(in_progress=True)
            self.start_urls = [job.url for job in self.jobs]
        super(EightKunSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        for job in self.jobs:
            yield Request(
                url=job.url,
                callback=self.parse,
                cb_kwargs={
                    'job_id': job.id,
                }
            )

    def parse(self, response, **kwargs):
        try:
            job_id = kwargs.get('job_id')
            job = self.jobs.get(pk=job_id)
            if len(response.css('div.post')) == 0:
                # No data here
                return

            for post in response.css('div.post'):
                post_no = post.css('a.post_no:nth-of-type(3)::text').get()
                if post_no is None:
                    post_no = job.thread_id
                yield {
                        'platform': self.platform,
                        'name': post.css('span.name::text').get(),
                        'subject': post.css('span.subject::text').get(),
                        'timestamp': post.css('time').attrib['datetime'],
                        'poster_id': post.css('span.poster_id::text').get(),
                        'board': job.board,
                        'thread_no': job.thread_id,
                        'post_no': post_no,
                        'tripcode': post.css('span.trip::text').get(),
                        'body_text': post.css('div.body').get(),
                        'url': job.url
                      }

        finally:
            job.in_progress = False
            job.save()
