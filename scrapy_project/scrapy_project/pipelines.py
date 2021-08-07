from posts.management.commands.load_chan_data import process_links, parse_formatting
from posts.models import Post, Platform, Board, ScrapeJob


class ScrapyPostPipeline(object):
    def __init__(self, *args, **kwargs):
        self.start_urls = []
        self.posts = []
        self.scraped_urls = set()

    def open_spider(self, spider):
        self.start_urls = spider.start_urls

    def process_item(self, item, spider):
        platform_obj = Platform.objects.get(name='8kun')
        board_obj, created = Board.objects.get_or_create(platform=platform_obj, name=item['board'])
        item['links'] = process_links(item)
        item['body_text'] = parse_formatting(item['body_text'])
        self.scraped_urls.add(item['url'])

        post = Post(platform=platform_obj, board=board_obj, thread_id=item['thread_no'],
                    post_id=item['post_no'], author=item['name'], poster_hash=item['poster_id'],
                    subject=item['subject'], body=item['body_text'], timestamp=item['timestamp'],
                    tripcode=item['tripcode'], is_op=(item['post_no'] == item['thread_no']),
                    links=item['links'])
        self.posts.append(post)
        return item

    def close_spider(self, spider):
        try:
            # Create Posts from scraped data
            Post.objects.bulk_create(self.posts, batch_size=10000, ignore_conflicts=True)
        except Exception as e:
            print('Exception in pipeline...')
            print(e)

        finally:
            ScrapeJob.objects.filter(url__in=self.scraped_urls).delete()
            failed_urls = [url for url in self.start_urls if url not in self.scraped_urls]
            failed_jobs = ScrapeJob.objects.filter(url__in=failed_urls)
            for job in failed_jobs:
                job.error_count += 1
                job.save()

