"""Movement journal with a protected many-to-one material relationship."""
from django.core.validators import MinValueValidator
from django.db import models


class Operation(models.Model):
    material = models.ForeignKey('materials_web.Material',
                                 on_delete=models.PROTECT,
                                 related_name='operations')
    kind = models.CharField(max_length=7, choices=[
        ('receipt', 'Поступление'), ('expense', 'Расход'),
    ])
    quantity = models.FloatField(validators=[MinValueValidator(0)])
    date = models.DateField()
    note = models.TextField(blank=True, null=True)
    cancelled = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date', '-id']
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0),
                                   name='operation_quantity_positive'),
            models.CheckConstraint(
                condition=models.Q(kind__in=['receipt', 'expense']),
                name='operation_kind_valid'),
        ]

    @property
    def material_name(self):
        return self.material.name

    @property
    def material_unit(self):
        return self.material.unit

    def __str__(self):
        return f'{self.get_kind_display()} #{self.pk}: {self.material.name}'
