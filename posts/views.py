from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.views.generic import ListView, RedirectView
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

from posts.models import Post


def index(request, platform=None, board=None):
    if board:
        thread_list = Post.objects.filter(is_op=True, platform=platform, board=board).order_by('-timestamp')
    elif platform:
        thread_list = Post.objects.filter(is_op=True, platform=platform).order_by('-timestamp')
    else:
        thread_list = Post.objects.filter(is_op=True).order_by('-timestamp')

    page = request.GET.get('page', 1)
    paginator = Paginator(thread_list, 40)

    try:
        page_threads = paginator.page(page)
    except PageNotAnInteger:
        page_threads = paginator.page(1)
    except EmptyPage:
        page_threads = paginator.page(paginator.num_pages)

    template = loader.get_template('posts/index.html')
    context = {
        'thread_list': page_threads,
        'platform': platform,
        'board': board
    }
    return HttpResponse(template.render(context, request))


def thread(request, platform, board, thread_id):
    thread_posts = Post.objects.filter(platform=platform, board=board, thread_id=thread_id).order_by('post_id')
    template = loader.get_template('posts/posts.html')
    context = {
        'posts': thread_posts,
    }
    return HttpResponse(template.render(context, request))


def drop(request, drop_no):
    q_drop = Post.objects.get(drop_no=drop_no)
    return redirect(q_drop.get_post_url())


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


