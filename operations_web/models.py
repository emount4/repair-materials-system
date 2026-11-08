"""Movement journal with a protected many-to-one material relationship."""
from django.core.validators import MinValueValidator
from django.db import models


class OperationQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=Operation.Status.ACTIVE)

    def cancelled(self):
        return self.filter(status=Operation.Status.CANCELLED)

    def completed(self):
        return self.filter(status=Operation.Status.COMPLETED)

    def for_date(self, value):
        return self.filter(date=value)

    def effective(self):
        return self.exclude(status=Operation.Status.CANCELLED)


class Operation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Действует'
        CANCELLED = 'cancelled', 'Отменена'
        COMPLETED = 'completed', 'Завершена'

    objects = OperationQuerySet.as_manager()
    material = models.ForeignKey('materials_web.Material',
                                 on_delete=models.PROTECT,
                                 related_name='operations',
                                 verbose_name='Материал')
    kind = models.CharField('Вид', max_length=7, choices=[
        ('receipt', 'Поступление'), ('expense', 'Расход'),
    ])
    quantity = models.FloatField('Количество',
                                 validators=[MinValueValidator(0)])
    date = models.DateField('Дата')
    note = models.TextField('Примечание', blank=True, null=True)
    status = models.CharField('Статус', max_length=10, choices=Status.choices,
                              default=Status.ACTIVE)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = 'Операция'
        verbose_name_plural = 'Операции'
        constraints = [
            models.CheckConstraint(condition=models.Q(status__in=[
                'active', 'cancelled', 'completed']),
                name='operation_status_valid'),
            models.CheckConstraint(condition=models.Q(quantity__gt=0),
                                   name='operation_quantity_positive'),
            models.CheckConstraint(
                condition=models.Q(kind__in=['receipt', 'expense']),
                name='operation_kind_valid'),
        ]

    @property
    def cancelled(self):
        return self.status == self.Status.CANCELLED

    @cancelled.setter
    def cancelled(self, value):
        self.status = self.Status.CANCELLED if value else self.Status.ACTIVE

    @property
    def material_name(self):
        return self.material.name

    @property
    def material_unit(self):
        return self.material.unit

    def __str__(self):
        return f'{self.get_kind_display()} #{self.pk}: {self.material.name}'
