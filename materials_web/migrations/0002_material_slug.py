import uuid
from django.db import migrations, models


def populate(apps, schema_editor):
    material = apps.get_model('materials_web', 'Material')
    for item in material.objects.all().iterator():
        item.slug = f'material-{item.pk}'
        item.save(update_fields=['slug'])


class Migration(migrations.Migration):
    dependencies = [('materials_web', '0001_initial')]
    operations = [
        migrations.AddField('material', 'slug', models.SlugField(null=True)),
        migrations.RunPython(populate, migrations.RunPython.noop),
        migrations.AlterField('material', 'slug', models.SlugField(
            'Код адреса', unique=True, default=uuid.uuid4)),
    ]
