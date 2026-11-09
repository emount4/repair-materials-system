"""Material data; existing stock is changed only through movements."""
from django import forms
from materials_web.models import Material


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ('name', 'category', 'unit', 'price', 'quantity')
        labels = {'name': 'Название', 'category': 'Категория',
                  'unit': 'Единица измерения', 'price': 'Цена за единицу',
                  'quantity': 'Начальный остаток'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields.pop('quantity')
            if self.instance.operations.exists():
                self.fields['unit'].disabled = True
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
