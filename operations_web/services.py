"""Transactional ORM writes preserving warehouse business rules."""
from decimal import Decimal
from django.db import transaction
from materials_web.models import Material
from operations_web.models import Operation
from utils import validate_number


@transaction.atomic
def record_operation(material_id, kind, quantity, date, note=''):
    validate_number(quantity, positive=True)
    if kind not in ('receipt', 'expense'):
        raise ValueError('Unknown movement kind')
    material = Material.objects.select_for_update().get(pk=material_id)
    change = quantity if kind == 'receipt' else -quantity
    balance = float(Decimal(str(material.quantity)) + Decimal(str(change)))
    validate_number(balance)
    operation = Operation(material=material, kind=kind, quantity=quantity,
                          date=date, note=note)
    operation.full_clean()
    material.quantity = balance
    material.save(update_fields=['quantity'])
    operation.save()
    return operation


@transaction.atomic
def cancel_operation(operation_id):
    operation = Operation.objects.select_for_update().get(pk=operation_id)
    if operation.cancelled:
        raise ValueError('Operation is already cancelled')
    material = Material.objects.select_for_update().get(
        pk=operation.material_id)
    change = (-operation.quantity if operation.kind == 'receipt'
              else operation.quantity)
    balance = float(Decimal(str(material.quantity)) + Decimal(str(change)))
    validate_number(balance)
    material.quantity = balance
    material.save(update_fields=['quantity'])
    operation.cancelled = True
    operation.save(update_fields=['cancelled'])
    return operation
