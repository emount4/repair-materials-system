"""Administration of stock movements through the transactional services."""
from django import forms
from django.contrib import admin, messages

from operations_web.models import Operation
from operations_web.services import cancel_operation, record_operation


class OperationAdminForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = '__all__'

    def clean(self):
        data = super().clean()
        if not self.instance.pk:
            material, quantity = data.get('material'), data.get('quantity')
            if data.get('status') == Operation.Status.CANCELLED:
                raise forms.ValidationError('Создайте действующую операцию.')
            if (material and quantity and data.get('kind') == 'expense'
                    and quantity > material.quantity):
                raise forms.ValidationError(
                    'Недостаточно материала на складе.')
        else:
            old = Operation.objects.get(pk=self.instance.pk)
            if old.cancelled and data.get('status') != old.status:
                raise forms.ValidationError(
                    'Нельзя возобновить отменённую запись.')
            if (not old.cancelled
                    and data.get('status') == Operation.Status.CANCELLED
                    and old.kind == 'receipt'
                    and old.material.quantity < old.quantity):
                raise forms.ValidationError(
                    'Поступление уже израсходовано.')
        return data


class OperationInline(admin.TabularInline):
    model = Operation
    extra = 0
    fields = ('date', 'kind', 'quantity', 'status', 'note')
    readonly_fields = fields
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    form = OperationAdminForm
    list_display = ('id', 'material', 'kind', 'quantity', 'date', 'status')
    list_filter = ('status', 'kind', 'date', 'material__category')
    search_fields = ('material__name', 'note')
    ordering = ('-date', '-id')
    list_select_related = ('material',)
    autocomplete_fields = ('material',)
    date_hierarchy = 'date'
    list_per_page = 20
    actions = ['cancel_selected']

    def get_readonly_fields(self, request, obj=None):
        return ('material', 'kind', 'quantity', 'date') if obj else ()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            created = record_operation(obj.material_id, obj.kind, obj.quantity,
                                       obj.date, obj.note)
            obj.pk = created.pk
            obj._state.adding = False
        elif (obj.status == Operation.Status.CANCELLED
              and not Operation.objects.get(pk=obj.pk).cancelled):
            cancel_operation(obj.pk)
        super().save_model(request, obj, form, change)

    @admin.action(description='Отменить выбранные операции')
    def cancel_selected(self, request, queryset):
        for item in queryset:
            try:
                cancel_operation(item.pk)
            except ValueError as error:
                self.message_user(request, f'#{item.pk}: {error}',
                                  level=messages.WARNING)
