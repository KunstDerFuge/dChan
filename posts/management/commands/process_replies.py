from django.core.management import BaseCommand
from tqdm import tqdm

from posts.models import Post


class Command(BaseCommand):
    help = "Process replies to posts and store their full URLs for fast retrieval"

    def handle(self, *args, **options):
        threads = Post.objects.values_list('thread_id', flat=True).distinct()
        for thread in tqdm(threads):
            first_post = Post.objects.filter(thread_id=thread).first()
            thread_board = first_post.board
            posts = thread_board.posts.filter(thread_id=thread)
            all_replies = {}
            for post in posts:
                for link, url in post.links.items():
                    try:
                        _, platform, board, _, end = url.split('/')
                        if '#' in end:
                            post_no = int(end.split('.')[-1].split('#')[-1])
                        else:
                            post_no = int(end.split('.')[0])

                        if post_no in all_replies:
                            all_replies[post_no].append([str(post.post_id), post.get_post_url()])
                        else:
                            all_replies[post_no] = [[str(post.post_id), post.get_post_url()]]

                    except Exception as e:
                        continue

            for post in posts:
                if post.post_id in all_replies:
                    post.replies = sorted(all_replies[post.post_id], key=lambda x: x[0])

            Post.objects.bulk_update(posts, ['replies'])
