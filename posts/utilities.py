from bs4 import BeautifulSoup
from tqdm import tqdm

from posts.management.commands.load_chan_data import parse_formatting
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
    df = df.fillna('')
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
                    links=row['links'], body_html=row['body_html'])
        new_posts.append(post)
        if len(new_posts) >= 10000:
            Post.objects.bulk_create(new_posts, ignore_conflicts=True)
            new_posts = []

    Post.objects.bulk_create(new_posts, ignore_conflicts=True)
    return threads


def parse_archive_is(row):
    try:
        soup = BeautifulSoup(row.header, "html.parser")
        name = soup.find('span', attrs={'style': 'text-align:left;color:rgb(17, 119, 67);font-weight:bold;'})
        if name is None:
            name = soup.find('span', attrs={'style': 'text-align:left;font-weight:bold;color:rgb(52, 52, 92);'})
        name = name.text.rstrip()
        subject = soup.find('span', attrs={'style': 'text-align:left;color:rgb(15, 12, 93);font-weight:bold;'})
        if subject is None:
            subject = ''
        else:
            subject = subject.text.rstrip()
        timestamp = soup.find('time').text.rstrip()
        poster_id = \
            soup.find('span', attrs={'style': 'text-align:left;cursor:pointer;white-space:nowrap;'})
        if poster_id is None:  # /patriotsfight/ apparently had poster IDs turned off
            poster_id = ''
        else:
            poster_id = poster_id.text.split()[-1]
        tripcode = soup.find('span', attrs={'style': 'text-align:left;color:rgb(34, 136, 84);'})
        if tripcode is None:
            tripcode = ''
        else:
            tripcode = tripcode.text.rstrip()
        post_id = soup.find_all('a', attrs={
            'style': 'text-align:left;text-decoration:none;color:inherit;margin: 0px; padding: 0px; '})[1].text.rstrip()
        return {
            'name': name,
            'subject': subject,
            'timestamp': timestamp.split('(')[0] + timestamp.split(') ')[-1],
            'poster_id': poster_id,
            'tripcode': tripcode,
            'post_no': post_id,
            'board': row['board'],
            'platform': row['platform'],
            'thread_no': row['thread_no'],
            'body_text': row['body']
        }

    except Exception as e:
        print('Failed on header:')
        print(row.header)
        print(e)
        raise e
