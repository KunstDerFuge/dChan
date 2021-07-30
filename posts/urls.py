from django.urls import path

from . import views
from .views import SearchResultsView, AdvancedSearch

urlpatterns = [
    path('', views.index, name='index'),
    path('search/advanced/', AdvancedSearch.as_view(), name='advanced_search'),
    path('search/', SearchResultsView.as_view(), name='search_results'),
    path('drop/<int:drop_no>', views.drop, name='drop'),
    path('<str:platform>/', views.index, name='index'),
    path('<str:platform>/<str:board>/', views.index, name='index'),
    path('<str:platform>/<str:board>/res/<int:thread_id>.html', views.thread, name='thread'),
]
