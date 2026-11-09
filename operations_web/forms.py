from django import forms
from django.utils import timezone
from materials_web.models import Material
from operations_web.models import Operation


class MovementForm(forms.Form):
    material = forms.ModelChoiceField(Material.objects.all(), label='Материал')
    kind = forms.ChoiceField(choices=[
        ('receipt', 'Поступление'), ('expense', 'Расход')], label='Вид')
    quantity = forms.FloatField(label='Количество', min_value=0)
    date = forms.DateField(label='Дата', initial=timezone.localdate,
                           widget=forms.DateInput(attrs={'type': 'date'},
                                                  format='%Y-%m-%d'))
    note = forms.CharField(label='Примечание', required=False,
                           widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_quantity(self):
        value = self.cleaned_data['quantity']
        if value <= 0:
            raise forms.ValidationError('Количество должно быть больше нуля.')
        return value


class NoteForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = ('note',)
        labels = {'note': 'Примечание'}
        widgets = {'note': forms.Textarea(attrs={
            'class': 'form-control', 'rows': 4})}
