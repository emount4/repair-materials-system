"""Warehouse materials managed by Django migrations."""
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
import uuid


class Material(models.Model):
    name = models.CharField('Название', max_length=200)
    price = models.FloatField('Цена', validators=[MinValueValidator(0)])
    quantity = models.FloatField('Остаток', validators=[MinValueValidator(0)])
    unit = models.CharField('Единица', max_length=30)
    category = models.CharField('Категория', max_length=100)
    slug = models.SlugField('Код адреса', unique=True, default=uuid.uuid4)
    stock_value = models.GeneratedField(
        expression=models.F('price') * models.F('quantity'),
        output_field=models.FloatField(), db_persist=True,
        verbose_name='Стоимость остатка')

    class Meta:
        ordering = ['name', 'id']
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gte=0),
                                   name='material_price_nonnegative'),
            models.CheckConstraint(condition=models.Q(quantity__gte=0),
                                   name='material_quantity_nonnegative'),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('materials_web:material_slug',
                       kwargs={'slug': self.slug})
