"""Маршруты списка и карточек материалов."""

from django.urls import path

from . import views


app_name = 'materials_web'

urlpatterns = [
    path('', views.materials, name='materials'),
    path('<int:material_id>/', views.material_detail, name='material_detail'),
]
