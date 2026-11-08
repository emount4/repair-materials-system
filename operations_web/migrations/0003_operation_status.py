from django.db import migrations, models


def forward(apps, schema_editor):
    operation = apps.get_model('operations_web', 'Operation')
    operation.objects.filter(cancelled=True).update(status='cancelled')


def backward(apps, schema_editor):
    operation = apps.get_model('operations_web', 'Operation')
    operation.objects.filter(status='cancelled').update(cancelled=True)


class Migration(migrations.Migration):
    dependencies = [('operations_web', '0002_alter_operation_quantity')]
    operations = [
        migrations.AddField('operation', 'status', models.CharField(
            'Статус', max_length=10, default='active', choices=[
                ('active', 'Действует'), ('cancelled', 'Отменена'),
                ('completed', 'Завершена')])),
        migrations.RunPython(forward, backward),
        migrations.RemoveField('operation', 'cancelled'),
    ]
