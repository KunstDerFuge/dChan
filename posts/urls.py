from django.urls import path
from django.views.decorators.cache import cache_page

from . import views
from .views import SearchResultsView, AdvancedSearch, timeseries_from_keywords, FrontendAppView

urlpatterns = [
    path('', views.index, name='index'),
    path('search/advanced/', AdvancedSearch.as_view(), name='advanced_search'),
    path('search/', SearchResultsView.as_view(), name='search_results'),
    path('data/', timeseries_from_keywords, name='timeseries'),
    path('timeseries/', FrontendAppView.as_view(), name='timeseries_frontend'),
    path('drop/<int:drop_no>', views.drop, name='drop'),
    path('<str:platform>/', cache_page(60 * 60)(views.index), name='index'),
    path('<str:platform>/<str:board>/', cache_page(60 * 60)(views.index), name='index'),
    path('<str:platform>/<str:board>/res/<int:thread_id>.html', views.thread, name='thread'),
    path('<str:board>/res/<int:thread_id>.html/<str:poster_hash>', views.thread, name='thread'),
    path('<str:board>/res/<int:thread_id>.html', views.thread, name='thread'),
]
