from django.urls import path
from django.views.decorators.cache import cache_page

from . import views
from .views import AdvancedSearch, timeseries_from_keywords, timeseries_frontend, search_results, about

urlpatterns = [
    path('', views.index, name='index'),
    path('search/advanced/', AdvancedSearch.as_view(), name='advanced_search'),
    path('search/', search_results, name='search_results'),
    path('<str:platform>/search/', search_results, name='platform_search'),
    path('<str:platform>/<str:board>/search/', search_results, name='board_search'),
    path('data/', timeseries_from_keywords, name='timeseries'),
    path('timeseries/', timeseries_frontend, name='timeseries_frontend'),
    path('about/', about, name='about'),
    path('drop/<int:drop_no>', views.drop, name='drop'),
    path('first/<str:phrase>', views.first_to_say, name='index'),
    path('reddit/', views.reddit_index, name='reddit_index'),
    path('r/<str:subreddit>/', views.reddit_index, name='reddit_index'),
    # Reddit threads:
    path('r/<str:subreddit>/comments/<str:thread_hash>/', views.reddit_thread, name='reddit_index'),
    path('r/<str:subreddit>/comments/<str:thread_hash>/<str:thread_slug>/', views.reddit_thread, name='reddit_index'),
    # Comments:
    path('r/<str:subreddit>/comments/<str:thread_hash>/<str:thread_slug>/<str:link_id>/', views.reddit_thread,
         name='reddit_thread'),
    path('r/<str:subreddit>/comments/<str:thread_hash>/comment/<str:link_id>/', views.reddit_thread,
         name='reddit_thread'),
    # Reddit user page:
    path('u/<str:username>/', views.reddit_user_page, name='reddit_thread'),

    # Chan platforms:
    path('<str:board>/index.html', views.redirect_board, name='index'),
    path('<str:board>/catalog.html', views.redirect_board, name='index'),
    path('<str:platform>/', cache_page(15 * 60)(views.index), name='index'),
    path('<str:platform>/<str:board>/', cache_page(60 * 60)(views.index), name='index'),
    path('<str:platform>/<str:board>/res/<int:thread_id>.html', views.thread, name='thread'),
    path('<str:board>/res/<int:thread_id>.html', views.thread, name='thread'),
    path('<str:platform>/read.cgi/<str:board>/<int:thread_id>/', views.textboard_thread, name='thread'),
    path('<str:platform>/read.cgi/<str:board>/<int:thread_id>/<str:selected>', views.textboard_thread, name='thread'),
]
