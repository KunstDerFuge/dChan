import scrapy


class EightKunSpider(scrapy.Spider):
    name = '8kun_spider'

    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 15,
        'DOWNLOAD_DELAY': 0,
    }

    def __init__(self, *args, **kwargs):
        self.start_urls = args
        super(EightKunSpider, self).__init__(*args, **kwargs)

    def parse(self, response, **kwargs):
        board = response.request.url.split('/')[-3]
        thread_no = response.request.url.split('/')[-1].split('.')[0]
        if len(response.css('div.post')) == 0:
            # No data here
            return

        for post in response.css('div.post'):
            post_no = post.css('a.post_no:nth-of-type(3)::text').get()
            if post_no is None:
                post_no = thread_no
            yield {
                    'name': post.css('span.name::text').get(),
                    'subject': post.css('span.subject::text').get(),
                    'timestamp': post.css('time').attrib['datetime'],
                    'poster_id': post.css('span.poster_id::text').get(),
                    'board': board,
                    'thread_no': thread_no,
                    'post_no': post_no,
                    'tripcode': post.css('span.trip::text').get(),
                    'body_text': post.css('div.body').get(),
                    'url': response.request.url
                  }
