from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse
from django.template import loader
from django.views.generic import ListView
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
    paginator = Paginator(thread_list, 50)

    try:
        page_threads = paginator.page(page)
    except PageNotAnInteger:
        page_threads = paginator.page(1)
    except EmptyPage:
        page_threads = paginator.page(paginator.num_pages)

    template = loader.get_template('posts/index.html')
    context = {
        'thread_list': page_threads,
    }
    return HttpResponse(template.render(context, request))


def thread(request, platform, board, thread_id):
    thread_posts = Post.objects.filter(platform=platform, board=board, thread_id=thread_id).order_by('post_id')
    template = loader.get_template('posts/posts.html')
    context = {
        'posts': thread_posts,
    }
    return HttpResponse(template.render(context, request))


class SearchResultsView(ListView):
    model = Post
    template_name = 'posts/search_results.html'
    context_object_name = 'results'

    def get_queryset(self):
        query = SearchQuery(self.request.GET.get('q'))
        exact = self.request.GET.get('exact')
        if exact == 'on':
            results = Post.objects.filter(body__search=query)[:100]
        else:
            results = Post.objects.filter(search_vector=query)[:100]
        return results
