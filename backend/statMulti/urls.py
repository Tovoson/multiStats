from rest_framework.routers import DefaultRouter
from django.contrib import admin
from django.urls import include, path

router = DefaultRouter()

urlpatterns = [
    path('api/', include('stats.urls')),
    path('admin/', admin.site.urls),
    path('', include('stats.urls')),
]
