from django.urls import path
from django.views.decorators.cache import cache_page

from . import views
from .views import AdvancedSearch, timeseries_from_keywords, timeseries_frontend, search_results

urlpatterns = [
    path('', views.index, name='index'),
    path('search/advanced/', AdvancedSearch.as_view(), name='advanced_search'),
    path('search/', search_results, name='search_results'),
    path('data/', timeseries_from_keywords, name='timeseries'),
    path('timeseries/', timeseries_frontend, name='timeseries_frontend'),
    path('drop/<int:drop_no>', views.drop, name='drop'),
    path('first/<str:phrase>', views.first_to_say, name='index'),
    path('<str:platform>/', cache_page(15 * 60)(views.index), name='index'),
    path('<str:platform>/<str:board>/', cache_page(60 * 60)(views.index), name='index'),
    path('<str:platform>/<str:board>/res/<int:thread_id>.html', views.thread, name='thread'),
    path('<str:board>/res/<int:thread_id>.html', views.thread, name='thread'),
]
