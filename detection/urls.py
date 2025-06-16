from django.urls import path
from . import views

app_name = 'crop_detection'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('upload/', views.UploadImageView.as_view(), name='upload'),
    path('result/<int:pk>/', views.ResultView.as_view(), name='result'),
    path('history/', views.HistoryView.as_view(), name='history'),
    path('api/upload/', views.APIUploadView.as_view(), name='api_upload'),
    path('api/results/<int:pk>/', views.APIResultView.as_view(), name='api_result'),
]