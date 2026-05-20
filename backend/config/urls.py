from django.contrib import admin
from django.urls import path, include
from api.views import handler404, handler500

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

handler404 = handler404
handler500 = handler500
