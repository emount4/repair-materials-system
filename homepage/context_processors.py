from materials_web.models import Material


def inventory_context(request):
    return {'inventory_title': 'Материалы ИП',
            'inventory_material_count': Material.objects.count()}
