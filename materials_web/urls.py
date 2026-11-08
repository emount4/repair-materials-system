"""Маршруты списка и карточек материалов."""

from django.urls import path

from . import views


app_name = 'materials_web'

urlpatterns = [
    path('', views.materials, name='materials'),
    path('available/', views.available, name='available'),
    path('item/<slug:slug>/', views.material_slug, name='material_slug'),
    path('<int:material_id>/', views.material_detail, name='material_detail'),
]
