"""Маршруты списка и карточек материалов."""

from django.urls import path

from . import views
from . import actions


app_name = 'materials_web'

urlpatterns = [
    path('new/', actions.create, name='create'),
    path('<int:material_id>/edit/', actions.edit, name='edit'),
    path('<int:material_id>/delete/', actions.delete, name='delete'),
    path('', views.materials, name='materials'),
    path('available/', views.available, name='available'),
    path('<int:material_id>/', views.material_detail, name='material_detail'),
]
