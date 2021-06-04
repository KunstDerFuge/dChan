from django.http import HttpResponse
from django.template import loader
from posts.models import Post


def index(request):
    thread_list = Post.objects.filter(is_op=True).order_by('-timestamp')[:50]
    template = loader.get_template('posts/index.html')
    context = {
        'thread_list': thread_list,
    }
    return HttpResponse(template.render(context, request))


def thread(request, thread_id):
    thread_posts = Post.objects.filter(thread_id=thread_id).order_by('timestamp')
    template = loader.get_template('posts/posts.html')
    context = {
        'posts': thread_posts,
    }
    return HttpResponse(template.render(context, request))
