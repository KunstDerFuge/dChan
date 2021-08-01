from django.core.management import BaseCommand
from tqdm import tqdm

from posts.models import Post


class Command(BaseCommand):
    help = "Process replies to posts and store their full URLs for fast retrieval"

    def handle(self, *args, **options):
        posts = Post.objects.all()
        for post in tqdm(posts):
            for link, url in post.links.items():
                try:
                    _, platform, board, _, _ = url.split('/')
                    post_no = int(_.split('.')[0].split('#')[-1])

                    replied_to = posts.get(platform=platform, board=board, post_id=post_no)
                    replied_to.reply_to.add(post)

                except Exception as e:
                    # print(f'Couldn\'t parse link: {url}')
                    # print(e)
                    continue

        Post.objects.bulk_update(posts, ['replied_to'], 10000)
