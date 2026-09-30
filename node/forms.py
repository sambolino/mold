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
    #Molecules1 = forms.ModelChoiceField(queryset = Molecule.objects.all().filter(id__lt=3), label='Molecule', to_field_name='inchikey')
    Wavelength = forms.ChoiceField(widget = forms.Select(attrs={'disabled':'disabled'}), label='Wavelength [nm]', 
                                 required = True)
    Temperature = forms.FloatField(label="Temperature [K]", widget=NumberInput(attrs={'step':'any', 'disabled':'disabled'}))
    #Wavelength = forms.ChoiceField(widget = forms.Select(), label='Wavelength [nm]', 
    #                             choices = ([('50','50'), ('60','60'), ('70','70'), ('80', '80'), ('90', '90'), ('100', '100'),('200','200'), ('300','300'), ('400','400'), ('500', '500'), ('600', '600'), ('700', '700'), ('800','800'), ('900', '900'), ('1000', '1000'), ('1100', '1100'), ('1200','1200'), ('1300', '1300'), ('1400', '1400'), ('1500', '1500'), ('1600','1600'), ('1700', '1700'), ('1800', '1800'), ('1900', '1900'), ('2000', '2000') ]), required = True)
    #Temperature = forms.FloatField(label="Temperature [K]", widget=NumberInput(attrs={'step':'any'}))

class Plot_form(forms.Form):
    Molecules2 = forms.ModelChoiceField(queryset = Molecule.objects.all().filter(id__lt=3), label='Molecule', to_field_name='inchikey')
    Temperature2 = forms.FloatField(label="Temperature [K]", widget=NumberInput(attrs={'step':'any'}))
