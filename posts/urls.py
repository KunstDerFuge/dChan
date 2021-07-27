from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:platform>/', views.index, name='index'),
    path('<str:platform>/<str:board>/', views.index, name='index'),
    path('<str:platform>/<str:board>/res/<int:thread_id>.html', views.thread, name='thread'),
]
