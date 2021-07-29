import re
from django.core.management import BaseCommand
from tqdm import tqdm
import pandas as pd

from posts.models import Post


def mark_posts(row):
    post = row['post_info']
    try:
        if post[0] == '8ch.net':
            platform = '8chan'
        elif post[0] == '4plebs.org':
            platform = '4chan'
        else:
            platform = '8kun'

        drop = Post.objects.get(platform=platform, board=post[1], post_id=post[5])
        drop.drop_no = row['drop']
        drop.save()

    except Exception as e:
        pass


def extract_post_info(url):
    post = re.findall(
        r'(8ch\.net|8kun\.[a-z]+|4plebs\.org)\/([a-zA-Z0-9]+)\/(res|thread)\/([0-9]+)(\.html)?/?#q?([0-9]+)', url)
    return post[0]


class Command(BaseCommand):
    help = "Process Q drop number -> post URL map file and mark the drops with their drop numbers"

    def handle(self, *args, **options):
        map = pd.read_csv('missing_Q-Notebook_data.tsv', sep='\t')
        tqdm.pandas()
        map['post_info'] = map.url.apply(extract_post_info)
        map.progress_apply(mark_posts, axis=1)
