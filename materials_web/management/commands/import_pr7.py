"""Copy PR7 data into migrated Django tables, retaining IDs and references."""
from contextlib import closing

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from db.database import DB_PATH, get_connection
from materials import Material as LegacyMaterial
from operations import Operation as LegacyOperation
from materials_web.models import Material
from operations_web.models import Operation


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('--source', default=str(DB_PATH))
        parser.add_argument('--replace', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        if Material.objects.exists() or Operation.objects.exists():
            if not options['replace']:
                raise CommandError('Target is not empty; '
                                   'use --replace explicitly')
        with closing(get_connection(options['source'])) as connection:
            materials = [dict(row) for row in connection.execute(
                'SELECT * FROM materials ORDER BY id')]
            operations = [dict(row) for row in connection.execute(
                'SELECT * FROM operations ORDER BY id')]
        legacy = [LegacyMaterial.from_data(row) for row in materials]
        for row in operations:
            row['note'] = row['note'] or ''
            row['cancelled'] = bool(row['cancelled'])
            LegacyOperation.from_data(row, legacy)
            row['status'] = (Operation.Status.CANCELLED if row.pop('cancelled')
                             else Operation.Status.ACTIVE)
        Operation.objects.all().delete()
        Material.objects.all().delete()
        Material.objects.bulk_create([Material(**row) for row in materials])
        Operation.objects.bulk_create([Operation(**row) for row in operations])
        self.stdout.write(f'Imported {len(materials)} materials, '
                          f'{len(operations)} operations')
