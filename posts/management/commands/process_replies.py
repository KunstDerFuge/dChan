from django.core.management import BaseCommand
from tqdm import tqdm

from posts.models import Post


class Command(BaseCommand):
    help = "Process replies to posts and store their full URLs for fast retrieval"

    def handle(self, *args, **options):
        posts = Post.objects.all()
        threads = Post.objects.values_list('thread_id').distinct()
        through_model = Post.reply_to.through
        for thread in tqdm(threads):
            posts = Post.objects.filter(thread_id=thread[0])
            replies = []
            for post in posts:
                for link, url in post.links.items():
                    try:
                        _, platform, board, _, end = url.split('/')
                        if '#' in end:
                            post_no = int(end.split('.')[-1].split('#')[-1])
                        else:
                            post_no = int(end.split('.')[0])

                        replied_to = posts.get(platform=platform, board=board, post_id=post_no)
                        replies.append(through_model(from_post_id=post.pk, to_post_id=replied_to.pk))

                    except Exception as e:
                        if not 'does not exist' in str(e):
                            print(f'Couldn\'t parse link: {url}')
                            print(e)
                        continue

            through_model.objects.bulk_create(replies, ignore_conflicts=True)
