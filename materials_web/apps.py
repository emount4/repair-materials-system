"""Конфигурация приложения материалов."""

from django.apps import AppConfig


class MaterialsWebConfig(AppConfig):
    """Настройки приложения материалов."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'materials_web'
