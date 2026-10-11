"""Конфигурация приложения операций."""

from django.apps import AppConfig


class OperationsWebConfig(AppConfig):
    """Настройки приложения операций."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'operations_web'
