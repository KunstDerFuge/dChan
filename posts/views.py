from django.contrib.postgres.search import SearchQuery
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.views.generic import ListView

from posts.models import Post, Board, Platform, Drop


def index(request, platform=None, board=None):
    if board:
        platform_obj = Platform.objects.get(name=platform)
        board_obj = Board.objects.get(platform=platform_obj, name=board)
        thread_list = board_obj.posts.filter(is_op=True).order_by('-timestamp')
    elif platform:
        platform_obj = Platform.objects.get(name=platform)
        thread_list = platform_obj.posts.filter(is_op=True).order_by('-timestamp')
    else:
        thread_list = Post.objects.filter(is_op=True).order_by('-timestamp')

    page = request.GET.get('page', 1)
    paginator = Paginator(thread_list.select_related('platform', 'board'), 40)
    page_range = paginator.get_elided_page_range(number=page)

    try:
        page_threads = paginator.page(page)
    except PageNotAnInteger:
        page_threads = paginator.page(1)
    except EmptyPage:
        page_threads = paginator.page(paginator.num_pages)

    template = loader.get_template('posts/index.html')
    context = {
        'thread_list': page_threads,
        'platform_name': platform,
        'board_name': board,
        'page_range': page_range,
    }
    if platform:
        context['boards_links'] = list(platform_obj.boards.values_list('name', flat=True).distinct())

    return HttpResponse(template.render(context, request))


def thread(request, platform, board, thread_id):
    context = {}
    try:
        platform_obj = Platform.objects.get(name=platform)
        board_obj = Board.objects.get(platform=platform_obj, name=board)
        thread_posts = board_obj.posts.filter(thread_id=thread_id) \
                                      .order_by('post_id') \
                                      .select_related('drop', 'platform')

        thread_drops = Drop.objects.filter(post__thread_id=thread_id) \
                                   .select_related('post__platform', 'post__board') \
                                   .order_by('number')

        drop_links = [(drop_.number, drop_.post.get_post_url()) for drop_ in thread_drops]

        context = {
            'posts': thread_posts,
            'platform_name': platform,
            'board_name': board,
            'thread': thread_id,
            'drop_links': drop_links,
            'boards_links': platform_obj.boards.values_list('name', flat=True).distinct()
        }

    except ObjectDoesNotExist:
        # One of the .gets failed, i.e. this thread is not archived
        pass

    except Exception as e:
        print(e)
        raise e

    finally:
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


class SearchResultsView(ListView):
    model = Post
    template_name = 'posts/search_results.html'
    context_object_name = 'results'

    def get_queryset(self):
        q = self.request.GET.get('q')
        if q == '':
            return []
        query = SearchQuery(q)
        results = Post.objects.filter(search_vector=query)[:100]
        return results


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
