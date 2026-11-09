"""Authenticated website workflows, shared by the PR9 and PR10 branches."""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.test.utils import setup_databases, teardown_databases
from materials_web.models import Material
from operations_web.models import Operation


@pytest.fixture(scope='module', autouse=True)
def workflow_database():
    config = setup_databases(verbosity=0, interactive=False)
    yield
    teardown_databases(config, verbosity=0)


@pytest.fixture
def client():
    Operation.objects.all().delete()
    Material.objects.all().delete()
    user, _ = get_user_model().objects.get_or_create(username='workflow-admin')
    user.is_superuser = True
    user.is_staff = True
    user.save()
    client = Client()
    client.force_login(user)
    return client


def test_material_creation_edit_and_deletion(client):
    response = client.post('/materials/new/', {
        'name': 'Штукатурка',
        'category': 'Смеси', 'unit': 'кг', 'price': 10, 'quantity': 5})
    assert response.status_code == 302
    item = Material.objects.get(name='Штукатурка')
    response = client.post(f'/materials/{item.pk}/edit/', {
        'name': 'Смесь', 'category': 'Смеси', 'unit': 'кг',
        'price': 12, 'quantity': 999})
    assert response.status_code == 302
    item.refresh_from_db()
    assert item.quantity == 5 and item.price == 12
    assert client.get(f'/materials/{item.pk}/delete/').status_code == 200
    assert Material.objects.filter(pk=item.pk).exists()
    assert client.post(f'/materials/{item.pk}/delete/').status_code == 302
    assert not Material.objects.exists()


def test_movements_cancel_history_and_note(client):
    item = Material.objects.create(name='Краска', category='Краски',
                                   unit='л', price=100, quantity=10)
    data = {'material': item.pk, 'kind': 'expense', 'quantity': 3,
            'date': '2026-11-09', 'note': 'Стены'}
    assert client.post('/operations/new/', data).status_code == 302
    operation = Operation.objects.get()
    item.refresh_from_db()
    assert item.quantity == 7
    assert client.post(f'/materials/{item.pk}/delete/').status_code == 409
    assert client.post(f'/operations/{operation.pk}/edit/',
                       {'note': 'Потолок'}).status_code == 302
    assert client.get(f'/operations/{operation.pk}/cancel/').status_code == 200
    item.refresh_from_db()
    assert item.quantity == 7
    url = f'/operations/{operation.pk}/cancel/'
    assert client.post(url).status_code == 302
    item.refresh_from_db()
    assert item.quantity == 10
    operation.refresh_from_db()
    assert operation.cancelled and operation.note == 'Потолок'
    assert client.post(url).status_code == 409
    assert Operation.objects.count() == 1


def test_overspending_and_input_validation(client):
    item = Material.objects.create(name='Краска', category='Краски',
                                   unit='л', price=100, quantity=1)
    for quantity in (99, 0, -1, 'nan', 'inf', 'abc'):
        response = client.post('/operations/new/', {
            'material': item.pk, 'kind': 'expense', 'quantity': quantity,
            'date': '2026-11-09'})
        assert response.status_code == 200
        assert not Operation.objects.exists()
    item.refresh_from_db()
    assert item.quantity == 1
    assert client.post('/materials/new/', {'price': -1}).status_code == 200


def test_authorization_and_csrf(client):
    anonymous = Client()
    assert anonymous.post('/materials/new/', {}).status_code == 302
    ordinary, _ = get_user_model().objects.get_or_create(username='reader')
    anonymous.force_login(ordinary)
    assert anonymous.post('/operations/new/', {}).status_code == 302
    csrf_client = Client(enforce_csrf_checks=True)
    user = get_user_model().objects.get(username='workflow-admin')
    csrf_client.force_login(user)
    assert csrf_client.post('/materials/new/', {}).status_code == 403


def test_receipt_cannot_be_cancelled_after_spending(client):
    item = Material.objects.create(name='Смесь', category='Смеси',
                                   unit='кг', price=10, quantity=0)
    data = {'material': item.pk, 'kind': 'receipt', 'quantity': 5,
            'date': '2026-11-09'}
    assert client.post('/operations/new/', data).status_code == 302
    receipt = Operation.objects.get()
    data.update(kind='expense', quantity=4)
    assert client.post('/operations/new/', data).status_code == 302
    assert client.post(f'/operations/{receipt.pk}/cancel/').status_code == 409
    item.refresh_from_db()
    assert item.quantity == 1
