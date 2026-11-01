#from django import forms
import floppyforms as forms
from node.models import *

class NumberInput(forms.TextInput):
    input_type = 'number'

class Search_form(forms.Form):
    Molecules = forms.ModelChoiceField(queryset = Molecule.objects.all(), label='Molecule', to_field_name='inchikey')
    QNJ = forms.IntegerField(label='QNJ', min_value=0, required=False, error_messages={'min_value': 'Please enter a non-negative integer'})
    QNv = forms.IntegerField(label='QNv', min_value=0, required=False, error_messages={'min_value': 'Please enter a non-negative integer'})

class Sum_form(forms.Form):
    Molecules1 = forms.ModelChoiceField(queryset = Molecule.objects.all(), label='Molecule', to_field_name='inchikey')
    Wavelength = forms.FloatField(label='Wavelength [nm]', widget=NumberInput(attrs={'step':'any', 'disabled':'disabled'}))
    Temperature = forms.FloatField(label="Temperature [K]", widget=NumberInput(attrs={'step':'any', 'disabled':'disabled'}))

class Plot_form(forms.Form):
    Molecules2 = forms.ModelChoiceField(queryset = Molecule.objects.all(), label='Molecule', to_field_name='inchikey')
    Temperature2 = forms.FloatField(label="Temperature [K]", widget=NumberInput(attrs={'step':'any'}))
