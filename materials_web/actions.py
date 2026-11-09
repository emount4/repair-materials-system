"""Authenticated POST workflows; read-only public pages remain available."""
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from materials_web.forms import MaterialForm
from materials_web.models import Material


@permission_required('materials_web.add_material')
@require_http_methods(['GET', 'POST'])
def create(request):
    form = MaterialForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save()
        messages.success(request, 'Материал добавлен.')
        return redirect('materials_web:material_detail', item.pk)
    return render(request, 'includes/editor.html', {
        'form': form, 'title': 'Новый материал',
        'back_url': 'materials_web:materials'})


@permission_required('materials_web.change_material')
@require_http_methods(['GET', 'POST'])
def edit(request, material_id):
    item = get_object_or_404(Material, pk=material_id)
    form = MaterialForm(request.POST or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.save(update_fields=list(form.fields))
        messages.success(request, 'Материал сохранён.')
        return redirect('materials_web:material_detail', item.pk)
    return render(request, 'includes/editor.html', {
        'form': form, 'title': 'Изменение материала',
        'back_url': 'materials_web:materials'})


@permission_required('materials_web.delete_material')
@require_http_methods(['GET', 'POST'])
def delete(request, material_id):
    item = get_object_or_404(Material, pk=material_id)
    error = ''
    if request.method == 'POST':
        try:
            with transaction.atomic():
                item = Material.objects.select_for_update().get(pk=item.pk)
                item.delete()
            messages.success(request, 'Материал удалён.')
            return redirect('materials_web:materials')
        except ProtectedError:
            error = 'У материала есть история операций. Удаление запрещено.'
    return render(request, 'includes/confirm.html', {
        'title': 'Удалить материал?', 'object': item, 'error': error,
        'back_url': 'materials_web:materials'}, status=409 if error else 200)
