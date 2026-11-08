"""Warehouse materials managed by Django migrations."""
from django.core.validators import MinValueValidator
from django.db import models


class Material(models.Model):
    name = models.CharField(max_length=200)
    price = models.FloatField(validators=[MinValueValidator(0)])
    quantity = models.FloatField(validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=30)
    category = models.CharField(max_length=100)

    class Meta:
        ordering = ['name', 'id']
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gte=0),
                                   name='material_price_nonnegative'),
            models.CheckConstraint(condition=models.Q(quantity__gte=0),
                                   name='material_quantity_nonnegative'),
        ]

    def __str__(self):
        return self.name
