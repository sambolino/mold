from django.contrib import admin
from .models import \
    Molecule, \
    MoleculeState, \
    RadiativeProcess, \
    DataList, \
    Source, \
    Author \

admin.site.register(Molecule)
admin.site.register(MoleculeState)
admin.site.register(RadiativeProcess)
admin.site.register(DataList)
admin.site.register(Source)
admin.site.register(Author)
