# -*- coding: utf-8 -*-
"""
ExampleNode dictionary definitions.
"""

# The returnable dictionary is used internally by the node and defines
# all the ways the VAMDC standard keywords (left-hand side) maps to
# the internal database representation queryset (right-hand side)
#
# When writing this, it helps to remember that dictionary is applied
# in a loop to every matching *instance* of the queryset variables
# returned from queryfunc.py. So in the example below, all 'AtomStates'
# will be looped over by the node software, using the name 'AtomState'
# (singular). 'AtomState' will be one single instance of a matching
# database object, from which we extract everything we need by parsing
# the VAMDC_standard LHS of this dictionary to how it maps to our specific
# database on the RHS. So, when looping through all AtomState objects
# matching the given query, the generator will for example know that
# to get the AtomStateEnergy VAMDC value, it will need to look at
# the AtomState.energy, i.e. the "energy" property of the current
# database object being worked on.
#
# (if you look at queryfuncs.py, you'll see 'AtomStates' being
#  assigned)

RETURNABLES = {\
'NodeID' : 'molD', # required
############################################################
'MethodID' : 'Method.id',
'MethodCategory' : 'Method.category',
############################################################

'MoleculeSpeciesId':'Molecule.id',
'MoleculeInchi':'Molecule.inchi',
'MoleculeInchiKey':'Molecule.inchikey',
'MoleculeChemicalName':'Molecule.name',
'MoleculeOrdinaryStructuralFormula':'Molecule.chemical_formula',
'MoleculeStoichiometricFormula':'Molecule.chemical_formula',

#'MoleculeBasisState':'proba',

'MoleculeStateId':'MoleculeState.id',
#'MoleculeStateQuantumNumbers': 'l',
'MoleculeQnCase':'dcs',
'MoleculeQNv':'MoleculeState.l',
'MoleculeQNj':'MoleculeState.n',
'MoleculeStateEnergyOrigin':'MoleculeState.energy_origin.id',
'MoleculeStateEnergy':'MoleculeState.energy',
'MoleculeStateEnergyUnit':'MoleculeState.energy_unit',
'MoleculeStateDescription':'MoleculeState.getDescription()',
'MoleculeStateAuxillary':'MoleculeState.getAuxillary()',

'CrossSectionId':'RadCros.id',
'CrossSectionSpecies':'RadCros.molecule_state.molecule.id',
'CrossSectionState':'RadCros.molecule_state.id',
'CrossSectionProcess':'diss',
'CrossSectionX':'RadCros.x.data_values',
'CrossSectionXUnit':'RadCros.x.unit',
'CrossSectionXName':'RadCros.x.parameter',
'CrossSectionXN':'RadCros.x.count',
'CrossSectionY':'RadCros.y.data_values',
'CrossSectionYUnit':'RadCros.y.unit',
'CrossSectionYName':'RadCros.y.parameter',
'CrossSectionYN':'RadCros.y.count',
'CrossSectionRef':'RadCros.sourcerefs',

'SourceID':'Source.id',
'SourceCategory':'Source.category',
'SourceArticleNumber':'Source.article_number',
'SourceDOI':'Source.digital_object_id',
'SourcePageBegin':'Source.page_begin',
'SourcePageEnd':'Source.page_end',
'SourceTitle':'Source.title',
'SourceAuthorName':'Source.authnames',
'SourceURI':'Source.uri',
'SourceVolume':'Source.volume',
'SourceYear':'Source.year',
'SourceComments':'Source.comments',
}

# The restrictable dictionary defines limitations to the search.
# The left-hand side is standardized, the righ-hand size should
# be defined in Django query-language style, where e.g. a search
# for the Species.atomic field  would be written as species__atomic.

RESTRICTABLES = {\
'MoleculeChemicalName' : 'molecule_state__molecule__name',
'MoleculeStoichiometricFormula' : 'molecule_state__molecule__chemical_formula',
'InchiKey' : 'molecule_state__molecule__inchikey',
'Inchi' : 'molecule_state__molecule__inchi',
'MoleculeQNJ':'molecule_state__n',
'MoleculeQNv':'molecule_state__l',
#'RadTransWavelength' : 'RadCros.
}


