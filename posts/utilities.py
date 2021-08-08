from django.db.models import QuerySet
from tqdm import tqdm

from posts.models import Post, Board


def process_replies(threads=None):
    if not threads:
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


def commit_posts_from_df(df, platform_obj):
    new_posts = []
    threads = set()
    for index, row in tqdm(df.iterrows(), total=len(df)):
        if platform_obj.name == '4chan':
            row['links'] = dict()

        board, created = Board.objects.get_or_create(platform=platform_obj, name=row['board'])

        threads.add(row['thread_no'])
        post = Post(platform=platform_obj, board=board, thread_id=row['thread_no'],
                    post_id=row['post_no'], author=row['name'], poster_hash=row['poster_id'],
                    subject=row['subject'], body=row['body_text'], timestamp=row['timestamp'],
                    tripcode=row['tripcode'], is_op=(row['post_no'] == row['thread_no']),
                    links=row['links'])
        new_posts.append(post)
        if len(new_posts) >= 10000:
            Post.objects.bulk_create(new_posts)
            new_posts = []

    Post.objects.bulk_create(new_posts)
    return threads
