from django.contrib import admin
from materials_web.models import Material
from operations_web.admin import OperationInline


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'quantity', 'unit', 'price',
                    'stock_value')
    list_filter = ('category', 'unit')
    search_fields = ('name', 'category')
    ordering = ('name', 'id')
    readonly_fields = ('stock_value',)
    inlines = [OperationInline]
    list_per_page = 20


admin.site.site_header = 'Склад материалов ИП'
admin.site.site_title = 'Управление складом'
admin.site.index_title = 'Материалы и движение запасов'
