"""Корневые маршруты веб-приложения."""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings


handler404 = 'homepage.views.page_not_found'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('homepage.urls')),
    path('materials/', include('materials_web.urls')),
    path('operations/', include('operations_web.urls')),
]

if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
