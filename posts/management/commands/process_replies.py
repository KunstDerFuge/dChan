from django.core.management import BaseCommand
from tqdm import tqdm

from posts.models import Post


class Command(BaseCommand):
    help = "Process replies to posts and store their full URLs for fast retrieval"

    def handle(self, *args, **options):
        threads = Post.objects.values_list('thread_id', flat=True).distinct()
        through_model = Post.reply_to.through
        for thread in tqdm(threads):
            first_post = Post.objects.filter(thread_id=thread)[0]
            thread_board = first_post.board
            thread_platform = first_post.platform
            posts = thread_board.posts.filter(thread_id=thread)
            replies = []
            for post in posts:
                for link, url in post.links.items():
                    try:
                        if url.count('/') == 3:
                            # Board index link, ignore
                            continue

                        _, platform, board, _, end = url.split('/')
                        if '#' in end:
                            post_no = int(end.split('.')[-1].split('#')[-1])
                        else:
                            post_no = int(end.split('.')[0])

                        replied_to = posts.get(platform=thread_platform, board=thread_board, post_id=post_no)
                        replies.append(through_model(from_post_id=post.pk, to_post_id=replied_to.pk))

                    except Exception as e:
                        continue

            through_model.objects.bulk_create(replies, ignore_conflicts=True)
