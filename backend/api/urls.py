from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check),
    path('status/<str:request_id>/', views.get_status),
    path('requests/', views.list_requests),
    path('requests/<str:request_id>/', views.get_request),
    path('track/<str:request_id>/', views.get_request),
    path('track-request/<str:request_id>/', views.get_request),
    path('summary/', views.get_summary),
    path('appointments/', views.create_appointment),
    path('appointments/<str:request_id>/', views.get_appointment),
    path('timeslots/', views.get_timeslots),
    path('', views.api_not_found),
    path('<path:path>/', views.api_not_found),
]
