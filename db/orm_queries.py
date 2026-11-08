"""ORM equivalents of PR7 queries; no SQLite access during HTTP requests."""
from django.db.models import Avg, Count, F, Max, Min, Q, Sum

from materials_web.models import Material
from operations_web.models import Operation


def fetch_all(name, parameters=()):
    materials = Material.objects.all()
    operations = Operation.objects.select_related('material')
    if name == 'materials_list':
        return materials
    if name == 'materials_search':
        return materials.filter(name__icontains=parameters[0],
                                quantity__gte=parameters[1])
    if name == 'materials_in_stock':
        return materials.filter(quantity__gte=parameters[0], quantity__gt=0
                                ).order_by('-quantity', 'id')
    if name == 'materials_without_expense':
        blocked = Operation.objects.filter(
            date=parameters[1], kind='expense', cancelled=False,
        ).values_list('material_id', flat=True)
        return materials.filter(quantity__gte=parameters[0], quantity__gt=0
                                ).exclude(pk__in=blocked)
    if name == 'operations_list':
        return operations
    if name == 'active_operations':
        return operations.exclude(cancelled=True)
    if name == 'operations_filter':
        kind, _, date, _, state, _ = parameters
        if kind:
            operations = operations.filter(kind=kind)
        if date:
            operations = operations.filter(date=date)
        if state != '':
            operations = operations.filter(cancelled=bool(state))
        return operations
    if name == 'category_statistics':
        return materials.values('category').annotate(
            materials_count=Count('id'),
            stock_value=Sum(F('price') * F('quantity')),
            min_price=Min('price'), max_price=Max('price'),
            average_price=Avg('price'),
        ).order_by('-stock_value', 'category')
    if name == 'material_activity':
        return materials.annotate(
            operations_count=Count('operations', filter=Q(
                operations__cancelled=False)),
            received=Sum('operations__quantity', filter=Q(
                operations__cancelled=False, operations__kind='receipt'),
                default=0.0),
            spent=Sum('operations__quantity', filter=Q(
                operations__cancelled=False, operations__kind='expense'),
                default=0.0),
            last_date=Max('operations__date', filter=Q(
                operations__cancelled=False)),
        ).order_by('-operations_count', 'id')
    if name == 'frequent_materials':
        return materials.annotate(operations_count=Count(
            'operations', filter=Q(operations__cancelled=False),
        )).filter(operations_count__gt=parameters[0]).order_by(
            '-operations_count', 'id')
    if name == 'latest_operations':
        return operations.order_by('-date', '-id')[:5]
    if name == 'materials_without_operations':
        return materials.filter(operations__isnull=True)
    raise KeyError(name)


def fetch_one(name, parameters=()):
    if name == 'material_detail':
        try:
            return Material.objects.annotate(
                total_cost=F('price') * F('quantity'),
            ).get(pk=parameters[0])
        except Material.DoesNotExist:
            return None
    if name == 'operation_detail':
        return Operation.objects.select_related('material').filter(
            pk=parameters[0]).first()
    if name == 'stock_summary':
        return Material.objects.aggregate(
            count=Count('id'), categories=Count('category', distinct=True),
            out_of_stock=Count('id', filter=Q(quantity=0)),
            total_cost=Sum(F('price') * F('quantity'), default=0.0),
        )
    if name == 'operation_summary':
        return Operation.objects.aggregate(
            operations_count=Count('id'),
            active_count=Count('id', filter=Q(cancelled=False)),
            cancelled_count=Count('id', filter=Q(cancelled=True)),
            receipt_value=Sum(F('quantity') * F('material__price'),
                              filter=Q(cancelled=False, kind='receipt'),
                              default=0.0),
            expense_value=Sum(F('quantity') * F('material__price'),
                              filter=Q(cancelled=False, kind='expense'),
                              default=0.0),
        )
    raise KeyError(name)
