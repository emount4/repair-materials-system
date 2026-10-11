"""Маршруты списка и карточек операций."""

from django.urls import path

from . import views


app_name = 'operations_web'

urlpatterns = [
    path('', views.operations, name='operations'),
    path(
        '<int:operation_id>/',
        views.operation_detail,
        name='operation_detail',
    ),
]
