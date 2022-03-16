import glob
import json
import os
from urllib.parse import urlparse

import numpy as np
from django.contrib.postgres.search import SearchQuery
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import PageNotAnInteger, EmptyPage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template import loader
from django.views.generic import ListView
from django_elasticsearch_dsl.search import Search

from posts.DSEPaginator import DSEPaginator
from posts.documents import PostDocument, RedditPostDocument
from posts.models import Post, Platform, Drop, Subreddit, Board, RedditPost


def board_links(platform):
    if not platform:
        return None, None
    try:
        platform_obj = Platform.objects.get(name=platform)
    except Platform.DoesNotExist:
        return None, None

    if platform == '8kun':
        q_boards = list(Drop.objects.filter(post__platform=platform_obj)
                        .values_list('post__board__name', flat=True)
                        .distinct())
        other_boards = sorted(list(platform_obj.boards.values_list('name', flat=True).distinct()))
        other_boards = sorted([board for board in other_boards if board not in q_boards])
        return q_boards, other_boards

    else:
        return list(platform_obj.boards.values_list('name', flat=True).distinct()), None


def subreddit_list():
    return sorted(list(Subreddit.objects.values_list('name', flat=True)))


def index(request, platform=None, board=None):
    s = PostDocument.search()
    if board:
        threads = s.query('match', is_op=True) \
            .query('match', platform__name=platform) \
            .query('match', board__name=board) \
            .sort('-timestamp')
    elif platform:
        threads = s.query('match', is_op=True) \
            .query('match', platform__name=platform) \
            .sort('-timestamp')
    else:
        threads = s.query('match', is_op=True) \
            .sort('-timestamp')

    page = int(request.GET.get('page', 1))
    results_per_page = 40
    start = (page - 1) * results_per_page
    end = start + results_per_page
    threads = threads[start:end]
    try:
        queryset = threads.to_queryset().select_related('platform', 'board')
    except Exception as e:
        template = loader.get_template('posts/elasticsearch_error.html')
        return HttpResponse(template.render({}, request), status=500)

    response = threads.execute()
    paginator = DSEPaginator(response, results_per_page)
    paginator.set_queryset(queryset)
    page_range = paginator.get_elided_page_range(number=page)

    try:
        page_threads = paginator.page(page)
    except PageNotAnInteger:
        page_threads = paginator.page(1)
    except EmptyPage:
        page_threads = paginator.page(paginator.num_pages)

    if board:
        try:
            # Attempt to fetch this board just to see if we need to 404
            board = Board.objects.get(name=board)
        except Board.DoesNotExist:
            template = loader.get_template('posts/404.html')
            return HttpResponse(template.render({}, request), status=404)
        except Board.MultipleObjectsReturned:
            # This just means there is more than one board by this name, like 4pol/8pol, all good
            pass

    boards, other_boards = board_links(platform)
    if boards is None and platform is not None:
        template = loader.get_template('posts/404.html')
        return HttpResponse(template.render({}, request), status=404)

    context = {
        'thread_list': page_threads,
        'platform_name': platform,
        'board_name': board,
        'page_range': page_range,
        'boards_links': boards,
        'other_boards': other_boards
    }

    template = loader.get_template('posts/index.html')
    return HttpResponse(template.render(context, request))


def thread(request, platform='8kun', board=None, thread_id=None):
    context = {}
    poster_hash = request.GET.get('poster_hash')
    try:
        s = PostDocument.search()
        thread_posts = s.query('match', platform__name=platform) \
            .query('match', board__name=board) \
            .query('match', thread_id=thread_id) \
            .sort('post_id') \
            .extra(size=800)

        if poster_hash:
            thread_posts = thread_posts.query('match', poster_hash=poster_hash)

        try:
            thread_posts = thread_posts.to_queryset().select_related('drop', 'platform', 'board')
        except Exception as e:
            print(e)
            template = loader.get_template('posts/elasticsearch_error.html')
            return HttpResponse(template.render(context, request), status=500)

        try:
            # Attempt to fetch this board just to see if we need to 404
            board = Board.objects.get(name=board)
        except Board.DoesNotExist:
            template = loader.get_template('posts/404.html')
            return HttpResponse(template.render({}, request), status=404)
        except Board.MultipleObjectsReturned:
            # This just means there is more than one board by this name, like 4pol/8pol, all good
            pass

        thread_drops = Drop.objects.filter(post__board__name=board, post__thread_id=thread_id) \
            .select_related('post__platform', 'post__board') \
            .order_by('number')

        drop_links = [(drop_.number, drop_.post.get_post_url()) for drop_ in thread_drops]

        boards, other_boards = board_links(platform)

        try:
            definitions = cache.get('definitions', [])
        except Exception as e:
            definitions = []

        context = {
            'posts': thread_posts,
            'platform_name': platform,
            'board_name': board,
            'thread': thread_id,
            'drop_links': drop_links,
            'boards_links': boards,
            'other_boards': other_boards,
            'definitions': json.dumps(definitions)
        }

        if len(thread_posts) == 0:
            raise ObjectDoesNotExist

    except ObjectDoesNotExist:
        # One of the .gets failed, i.e. this thread is not archived
        template = loader.get_template('posts/thread.html')
        return HttpResponse(template.render(context, request), status=404)

    except Exception as e:
        print(e)
        template = loader.get_template('posts/thread.html')
        return HttpResponse(template.render(context, request), status=500)

    template = loader.get_template('posts/thread.html')
    return HttpResponse(template.render(context, request))


def drop(request, drop_no):
    try:
        q_drop = Drop.objects.get(number=drop_no)
    except ObjectDoesNotExist:
        print('Drop is not archived: ', drop_no)
        template = loader.get_template('posts/index.html')
        context = {
            'posts': [],
        }
        return HttpResponse(template.render(context, request))
    return redirect(q_drop.post.get_post_url())


def search_results(request):
    q = request.GET.get('q')
    thread_no = request.GET.get('thread_no')
    subject = request.GET.get('subject')
    name = request.GET.get('name')
    tripcode = request.GET.get('tripcode')
    user_id = request.GET.get('user_id')
    date_start = request.GET.get('date_start')
    date_end = request.GET.get('date_end')
    sort = request.GET.get('sort')
    if (not q or q == '') and not any([thread_no, subject, name, tripcode, user_id, date_start, date_end]):
        return []

    if q and q != '':
        s = Search(index='posts', model=Post).from_dict({
            'query': {
                'simple_query_string': {
                    'query': q,
                    'fields': ['subject^2', 'body'],
                    'default_operator': 'and',
                    'analyze_wildcard': True
                }
            }
        })
        # Setting _model has to be done to use .to_queryset() since we are creating the search from a dict,
        # not PostDocument
        # There is almost definitely a better, less ugly way but this works
        s._model = Post
    else:
        s = PostDocument.search()

    if thread_no:
        s = s.query('match', thread_id=thread_no)
    if subject:
        s = s.query('match', subject=subject)
    if name:
        s = s.query('match', author=name)
    if tripcode:
        s = s.query('match', tripcode=tripcode)
    if user_id:
        s = s.query('match', poster_hash=user_id)
    if date_start:
        s = s.query('range', timestamp={'gte': date_start})
    if date_end:
        s = s.query('range', timestamp={'lte': date_end})
    if sort:
        if sort == 'newest':
            s = s.sort('-timestamp')
        if sort == 'oldest':
            s = s.sort('timestamp')
        if sort == 'relevance':
            # Already sorted by relevance
            pass
    else:
        s = s.sort('-timestamp')

    page = int(request.GET.get('page', 1))
    results_per_page = 50
    start = (page - 1) * results_per_page
    end = start + results_per_page
    results = s[start:end]
    queryset = results.to_queryset().select_related('platform', 'board')
    response = results.execute()
    paginator = DSEPaginator(response, results_per_page)
    paginator.set_queryset(queryset)
    page_range = paginator.get_elided_page_range(number=page)

    try:
        page_results = paginator.page(page)
    except PageNotAnInteger:
        page_results = paginator.page(1)
    except EmptyPage:
        page_results = paginator.page(paginator.num_pages)

    context = {
        'results': page_results,
        'page_range': page_range,
        'hits': s.count()
    }

    template = loader.get_template('posts/search_results.html')
    return HttpResponse(template.render(context, request))


class AdvancedSearch(ListView):
    model = Post
    template_name = 'posts/advanced_search.html'
    context_object_name = 'results'

    def get_queryset(self):
        query = SearchQuery(self.request.GET.get('q'))
        results = Post.objects.filter(search_vector=query)[:100]
        return results

    def get_context_data(self, **kwargs):
        context = super(AdvancedSearch, self).get_context_data(**kwargs)
        boards = Post.objects.values_list('platform', 'board').distinct()
        context['boards'] = boards
        return context


def first_to_say(request, phrase):
    s = PostDocument.search()
    s = s.query('match_phrase', body=phrase)
    results = s.sort('timestamp').extra(size=100).to_queryset()
    template = loader.get_template('posts/thread.html')
    return HttpResponse(template.render({'posts': results}, request))


def timeseries_from_keywords(request):
    keywords = request.GET.get('keywords')
    agg = request.GET.get('agg')
    syntax = request.GET.get('syntax')
    start_date = request.GET.get('start_date', '2017-10-28')
    end_date = request.GET.get('end_date', None)
    timezone = request.GET.get('timezone', 'America/Los_Angeles')
    if start_date == '':
        start_date = '2017-10-28'
    if end_date == '':
        end_date = None
    if syntax == 'simple':
        query_type = 'simple_query_string'
        query = {
            query_type: {
                'query': keywords,
                'default_operator': 'AND',
                'fields': ['subject', 'body'],
                'analyze_wildcard': True
            }
        }
    else:
        query_type = 'query_string'
        query = {
            query_type: {
                'query': keywords,
                'default_field': 'body',
                'default_operator': 'AND',
                'analyze_wildcard': True
            }
        }

    s = Search(index='posts', model=Post).from_dict({
        'query': {
            'range': {
                'timestamp': {
                    'time_zone': timezone,
                    'gte': start_date,
                    'lte': end_date
                }
            }
        },
        'aggs': {
            "posts_over_time": {
                "date_histogram": {
                    "field": "timestamp",
                    "calendar_interval": agg,
                    "time_zone": timezone
                },
                'aggs': {
                    'total': {
                        'value_count': {'field': '_id'}
                    },
                    'keywords_filter': {
                        'filter': {
                            'bool': {
                                'must': [
                                    query
                                ]
                            }
                        },
                    },
                    'per_mille': {
                        'bucket_script': {
                            'buckets_path': {
                                'matches': 'keywords_filter._count',
                                'total': 'total',
                            },
                            'script': 'params.matches / params.total * 1000'
                        }
                    }
                },
            },
        },
    })
    results = s.execute().aggregations.to_dict()
    return JsonResponse({'data': results})


def timeseries_frontend(request):
    try:
        print(os.listdir())
        os.chdir(os.path.join('visualizations', 'build'))
        js_chunks = glob.glob(os.path.join('static', 'js', '*.js'))
        template = loader.get_template('posts/timeseries.html')
        return HttpResponse(template.render({'js_chunks': js_chunks}, request))
    finally:
        os.chdir(os.path.join('..', '..'))


def about(request):
    template = loader.get_template('posts/about.html')
    return HttpResponse(template.render({}, request))


def reddit_index(request, subreddit=None):
    s = RedditPostDocument.search()
    sort = request.GET.get('sort')
    if subreddit:
        threads = s.query('match', platform__name='reddit') \
            .query('match', is_op=True) \
            .query('match', subreddit__name=subreddit)
    else:
        threads = s.query('match', platform__name='reddit') \
            .query('match', is_op=True)

    if sort == 'newest':
        threads = threads.sort('-score') \
            .sort('-timestamp')
    elif sort == 'oldest':
        threads = threads.sort('-score') \
            .sort('timestamp')
    else:
        sort = 'top'
        threads = threads.sort('-timestamp') \
            .sort('-score')

    page = int(request.GET.get('page', 1))
    results_per_page = 40
    start = (page - 1) * results_per_page
    end = start + results_per_page
    threads = threads[start:end]

    try:
        queryset = threads.to_queryset().select_related('subreddit')
    except Exception as e:
        print(e)
        template = loader.get_template('posts/elasticsearch_error.html')
        return HttpResponse(template.render({}, request), status=500)

    response = threads.execute()
    paginator = DSEPaginator(response, results_per_page)
    paginator.set_queryset(queryset)
    page_range = paginator.get_elided_page_range(number=page)

    try:
        page_threads = paginator.page(page)
    except PageNotAnInteger:
        page_threads = paginator.page(1)
    except EmptyPage:
        page_threads = paginator.page(paginator.num_pages)

    context = {
        'sort': sort,
        'thread_list': page_threads,
        'subreddit_name': subreddit,
        'subreddits': subreddit_list(),
        'page_range': page_range,
        'subreddits_links': list(Subreddit.objects.values_list('name', flat=True).distinct())
    }

    template = loader.get_template('posts/reddit_index.html')
    return HttpResponse(template.render(context, request))


def reddit_thread(request, subreddit, thread_hash, thread_slug=None, link_id=None):
    context = {}
    try:
        s = RedditPostDocument.search()
        thread_posts = s.query('match', subreddit__name=subreddit) \
            .query('match', thread_hash=thread_hash) \
            .sort('-timestamp') \
            .sort('-score') \
            .extra(size=800)

        try:
            thread_replies = thread_posts.query('match', is_op=False).to_queryset()
        except Exception as e:
            print(e)
            template = loader.get_template('posts/elasticsearch_error.html')
            return HttpResponse(template.render(context, request), status=500)

        for post in thread_replies:
            post.replies = [reply for reply in thread_replies if reply.parent_id == post.link_id]

        op = thread_posts.query('match', is_op=True).to_queryset().first()
        if link_id:
            # Focusing on one comment
            focused_post = [post for post in thread_replies if post.link_id == link_id][0]

            if focused_post.parent_id == op.link_id:
                # This post is a top-level reply to the OP
                top_level_replies = [post for post in thread_replies if post.link_id == link_id]
            else:
                # This post's parent is not the OP, so show its parent as well
                top_level_replies = [post for post in thread_replies if post.link_id == focused_post.parent_id]
        else:
            top_level_replies = [post for post in thread_replies if post.parent_id == op.link_id]

        context = {
            'subreddits': subreddit_list(),
            'op': op,
            'posts': top_level_replies,
            'subreddit_name': subreddit,
            'thread': thread_hash,
            'viewing_comment': link_id is not None,
            'subreddits_links': list(Subreddit.objects.values_list('name', flat=True).distinct())
        }

        if not op:
            raise ObjectDoesNotExist

    except ObjectDoesNotExist:
        # One of the .gets failed, i.e. this thread is not archived
        template = loader.get_template('posts/404.html')
        return HttpResponse(template.render(context, request), status=404)

    except Exception as e:
        print(e)
        template = loader.get_template('posts/reddit_thread.html')
        return HttpResponse(template.render(context, request), status=500)

    template = loader.get_template('posts/reddit_thread.html')
    return HttpResponse(template.render(context, request))


def reddit_user_page(request, username):
    try:
        s = RedditPostDocument.search()
        if len(username) <= 2:
            raise
        user_posts = s.query('match_phrase', author=username) \
            .sort('-score') \
            .sort('-timestamp')

        if user_posts.count() == 0:
            raise

    except Exception as e:
        print(e)
        template = loader.get_template('posts/404.html')
        return HttpResponse(template.render({}, request), status=500)

    page = int(request.GET.get('page', 1))
    domain = request.GET.get('domain', None)
    results_per_page = 50
    start = (page - 1) * results_per_page
    end = start + results_per_page
    user_posts = user_posts[start:end]

    try:
        queryset = user_posts.to_queryset().select_related('subreddit')
        if domain:
            queryset = RedditPost.objects.filter(author=username, is_op=True, url__contains=domain)
        
        op_posts = s.query('match_phrase', author=username).query(is_op=True).extra(size=10000).to_queryset()
        urls = op_posts.values_list('url', flat=True)
        parsed = [urlparse(url) for url in urls]
        domains = [url.netloc for url in parsed]
        counts = dict(zip(domains, [domains.count(i) for i in domains]))
        counts = [{'domain': key, 'count': value} for key, value in counts.items() if key is not '']
        counts = sorted(counts, key=lambda x: x['count'], reverse=True)

    except Exception as e:
        print(e)
        template = loader.get_template('posts/elasticsearch_error.html')
        return HttpResponse(template.render({}, request), status=500)

    response = user_posts.execute()
    paginator = DSEPaginator(response, results_per_page)
    paginator.set_queryset(queryset)
    page_range = paginator.get_elided_page_range(number=page)

    try:
        page_posts = paginator.page(page)
    except PageNotAnInteger:
        page_posts = paginator.page(1)
    except EmptyPage:
        page_posts = paginator.page(paginator.num_pages)

    context = {
        'subreddits': subreddit_list(),
        'post_list': page_posts,
        'page_range': page_range,
        'username': username,
        'total_posts': user_posts.count(),
        'domain_counts': counts,
        'paginate': domain is None
    }

    template = loader.get_template('posts/reddit_user_page.html')
    return HttpResponse(template.render(context, request))


def redirect_board(request, board):
    return redirect(f'/8kun/{board}/')
