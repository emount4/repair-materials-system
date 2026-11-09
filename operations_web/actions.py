from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from operations_web.forms import MovementForm, NoteForm
from operations_web.models import Operation
from operations_web.services import record_operation, cancel_operation
from materials_web.models import Material


@permission_required('operations_web.add_operation')
@require_http_methods(['GET', 'POST'])
def create(request):
    initial = {'kind': request.GET.get('kind', 'receipt'),
               'material': request.GET.get('material')}
    form = MovementForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            item = record_operation(data['material'].pk, data['kind'],
                                    data['quantity'], data['date'],
                                    data['note'])
        except (ValueError, ValidationError, Material.DoesNotExist):
            form.add_error(None, 'Операция не выполнена. Проверьте остаток '
                           'материала и введённые данные.')
        else:
            messages.success(request, 'Операция сохранена. Остаток обновлён.')
            return redirect('operations_web:operation_detail', item.pk)
    return render(request, 'includes/editor.html', {
        'title': 'Новое движение материала', 'form': form,
        'back_url': 'operations_web:operations'})


@permission_required('operations_web.change_operation')
@require_http_methods(['GET', 'POST'])
def edit(request, operation_id):
    item = get_object_or_404(Operation, pk=operation_id)
    form = NoteForm(request.POST or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.save(update_fields=['note'])
        messages.success(request, 'Примечание сохранено.')
        return redirect('operations_web:operation_detail', item.pk)
    return render(request, 'includes/editor.html', {
        'title': 'Примечание к операции', 'form': form,
        'back_url': 'operations_web:operations'})


@permission_required('operations_web.change_operation')
@require_http_methods(['GET', 'POST'])
def cancel(request, operation_id):
    item = get_object_or_404(Operation.objects.select_related('material'),
                             pk=operation_id)
    error = ''
    if request.method == 'POST':
        try:
            cancel_operation(item.pk)
        except ValueError:
            error = ('Отмена невозможна: операция уже отменена или '
                     'остатка недостаточно для отмены поступления.')
        else:
            messages.success(request, 'Операция отменена. Остаток обновлён.')
            return redirect('operations_web:operation_detail', item.pk)
    return render(request, 'includes/confirm.html', {
        'title': 'Отменить операцию?', 'object': item, 'error': error,
        'back_url': 'operations_web:operations'}, status=409 if error else 200)
