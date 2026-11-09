"""Маршруты списка и карточек операций."""

from django.urls import path

from . import views
from . import actions


app_name = 'operations_web'

urlpatterns = [
    path('new/', actions.create, name='create'),
    path('<int:operation_id>/edit/', actions.edit, name='edit'),
    path('<int:operation_id>/cancel/', actions.cancel, name='cancel'),
    path('', views.operations, name='operations'),
    path(
        '<int:operation_id>/',
        views.operation_detail,
        name='operation_detail',
    ),
]
