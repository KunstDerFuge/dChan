import html
import re

import pandas as pd
from bs4 import BeautifulSoup
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


def process_replies_from_df(df):
    all_replies = {}
    df_with_replies = pd.DataFrame()
    df.to_csv('test_this.csv')

    def aggregate_replies(row):
        def get_post_url(row_):
            return f"/{row_['platform']}/{row_['board']}/res/{row_['thread_no']}.html" + '#' + str(row_['post_no'])

        # At this stage, empty links are encoded like this for some reason
        if row['links'] == '{}':
            return

        try:
            for link, url in dict(row['links']).items():
                try:
                    _, platform, board, _, end = url.split('/')
                    if '#' in end:
                        post_no = int(end.split('.')[-1].split('#')[-1])
                    else:
                        post_no = int(end.split('.')[0])

                    if post_no in all_replies:
                        all_replies[post_no].append([str(row['post_no']), get_post_url(row)])
                    else:
                        all_replies[post_no] = [[str(row['post_no']), get_post_url(row)]]
                except Exception as e:
                    print(e)
                continue
        except Exception as e:
            print(type(row['links']))
            print(row['links'])
            print(e)

    def link_replies(row):
        if str(row['post_no']) in all_replies:
            row['replies'] = sorted(all_replies[row['post_no']], key=lambda x: x[0])
        else:
            row['replies'] = dict()
        return row

    threads = df.thread_no.unique()
    for thread in threads:
        all_replies = {}
        thread_df = df[df.thread_no == thread].copy().reset_index()
        if len(thread_df) == 0:
            continue
        thread_df.apply(aggregate_replies, axis=1)
        df_with_replies = pd.concat([df_with_replies, thread_df.apply(link_replies, axis=1)])
    return df_with_replies.reset_index()


def process_and_commit_from_df(df, platform_obj):
    print('Parsing formatting...')
    df['body_html'] = df.body_text
    df['links'] = df.apply(process_links, axis=1)
    if platform_obj.name == '8chan':
        df['body_text'] = df.body_text.apply(parse_8chan_formatting)
    else:
        df['body_text'] = df.body_text.apply(parse_formatting)

    # Prevent processing as decimal
    df['thread_no'] = pd.to_numeric(df['thread_no'], errors='coerce', downcast='integer')
    df['thread_no'] = df['thread_no'].astype(str)

    print('Processing replies...')
    df = process_replies_from_df(df)
    print('Committing to DB...')
    commit_posts_from_df(df, platform_obj)


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
                    links=row['links'], body_html=row['body_html'], replies=row['replies'])
        new_posts.append(post)
        if len(new_posts) >= 10000:
            Post.objects.bulk_create(new_posts, ignore_conflicts=True)
            new_posts = []

    Post.objects.bulk_create(new_posts, ignore_conflicts=True)
    return threads


def parse_archive_is(row):
    try:
        soup = BeautifulSoup(row['header'], "html.parser")
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
        print(row['header'])
        print(e)
        raise e


def parse_formatting(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Process green text
    for result in soup.find_all(attrs={'class': 'quote'}):
        result.insert(0, '> ')

    # Process red text
    for result in soup.find_all(attrs={'class': 'heading'}):
        result.insert_before('==')
        result.insert_after('==')

    # Process bold text
    for result in soup.find_all('strong'):
        result.insert_before("'''")
        result.insert_after("'''")

    # Process italic text
    for result in soup.find_all('em'):
        if result.get_text() != '//':  # For some reason, the // in URLs is wrapped with <em />
            result.insert_before("''")
            result.insert_after("''")

    # Process underlined text
    for result in soup.find_all('u'):
        result.insert_before("__")
        result.insert_after("__")

    # Process strikethrough text
    for result in soup.find_all('s'):
        result.insert_before("~~")
        result.insert_after("~~")

    # Process spoiler text
    for result in soup.find_all(attrs={'class': 'spoiler'}):
        result.insert_before("**")
        result.insert_after("**")

    final_text = '\n'.join([line.get_text() for line in soup.find_all(attrs={'class': 'body-line'})])
    return final_text


def process_links(row):
    try:
        links = dict()
        if row['platform'] == '8chan':
            board_index_links = re.findall(
                r'\/([a-zA-Z0-9]+)\/index\.html\".{80,95}>(&gt;&gt;[0-9]+|&gt;&gt;&gt;/[a-zA-Z]+/)',
                row['body_text'])
            matches = re.findall(
                r'\/([a-zA-Z0-9]+)\/res\/([0-9]+)\.html%23([0-9]+)\".{80,95}>(&gt;&gt;[0-9]+|&gt;&gt;&gt;\/[a-zA-Z]+\/[0-9]+)',
                row['body_text'])
        else:
            board_index_links = re.findall(
                r'\"\/([a-zA-Z0-9]+)\/index\.html\">(&gt;&gt;[0-9]+|&gt;&gt;&gt;/[a-zA-Z]+/)',
                row['body_text'])
            matches = re.findall(
                r'\"\/([a-zA-Z0-9]+)\/res\/([0-9]+)\.html#q?([0-9]+)\">(&gt;&gt;[0-9]+|&gt;&gt;&gt;\/[a-zA-Z]+\/[0-9]+)',
                row['body_text'])
        matches.extend(board_index_links)
        if len(matches) == 0:
            return dict()
        else:
            for match in matches:
                if len(match) == 2:
                    # Board index link
                    links[html.unescape(match[-1])] = f"/{row['platform']}/{match[0]}/"
                else:
                    links[html.unescape(match[-1])] = f"/{row['platform']}/{match[0]}/res/{match[1]}.html#{match[2]}"
        return links
    except Exception as e:
        print(e)
        return {}


def split_list(lst, n):
    from itertools import islice
    lst = iter(lst)
    result = iter(lambda: tuple(islice(lst, n)), ())
    return list(result)


def parse_8chan_formatting(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Process green text
    for result in soup.find_all(attrs={
        'style': 'text-align:left;color:rgb(120, 153, '
                 '34);direction:ltr;display:block;line-height:1.16em;font-size:13px;min-height:1.16em;margin: 0px; '}):
        result.insert(0, '> ')

    # Process red text
    for result in soup.find_all(
            attrs={'style': 'text-align:left;color:rgb(175, 10, 15);font-size:11pt;font-weight:bold;'}):
        result.insert_before('==')
        result.insert_after('==')

    # Process bold text
    for result in soup.find_all('strong'):
        result.insert_before("'''")
        result.insert_after("'''")

    # Process italic text
    for result in soup.find_all('em'):
        if result.get_text() != '//':  # For some reason, the // in URLs is wrapped with <em />
            result.insert_before("''")
            result.insert_after("''")

    # Process underlined text
    for result in soup.find_all('u'):
        result.insert_before("__")
        result.insert_after("__")

    # Process strikethrough text
    for result in soup.find_all('s'):
        result.insert_before("~~")
        result.insert_after("~~")

    # Process spoiler text
    for result in soup.find_all(attrs={'class': 'spoiler'}):
        result.insert_before("**")
        result.insert_after("**")

    final_text = '\n'.join([line.get_text() for line in soup.find_all('div')])
    return final_text
