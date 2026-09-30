from django.db import models

class Molecule(models.Model):
    name = models.CharField(max_length=32, db_index=True)
    inchi = models.CharField(max_length=256)
    inchikey = models.CharField(max_length=128)
    chemical_formula = models.CharField(max_length=128)
    cas = models.CharField(max_length=128, null=True, blank=True)
    def __str__(self):
        return "%s: %s" % (self.name, self.chemical_formula )
    def __unicode__(self):
        return "%s: %s" % (self.name, self.chemical_formula )
    class Meta:
        db_table = u'molecules'

class MoleculeState(models.Model):
    energy_origin = models.ForeignKey('self', null=True, on_delete=models.DO_NOTHING)
    n = models.PositiveSmallIntegerField(null=True, blank=True)
    l = models.PositiveSmallIntegerField(null=True, blank=True)
    energy = models.CharField(max_length=128, null=True, blank=True)
    energy_unit = models.CharField(max_length=32, null=True, blank=True)
    molecule = models.ForeignKey(Molecule, on_delete=models.CASCADE)
    description = models.CharField(max_length=128, null=True, blank=True)
    auxillary = models.BooleanField(blank=True)
    def __str__(self):
        return "id: %s %s - %s - %s" % (self.id, self.molecule.name, self.n, self.l )
    def __unicode__(self):
        return "id: %s %s - %s - %s" % (self.id, self.molecule.name, self.n, self.l )
    def getAuxillary(self):
        if self.auxillary==True:
            return 'true'
        else:
            return 'false'
    def getDescription(self):
        if (self.description==None or self.description==''):
            return "r: %s, v: %s" % (self.n, self.l)
        else:
            return self.description
    class Meta:
        db_table = u'moleculestates'

class DataList(models.Model):
    count =  models.IntegerField(null=True, blank=True)
    data_values = models.TextField(null=True, blank=True, help_text="""Space delimited values""")
    unit = models.CharField(max_length=16, null=True, blank=True)
    parameter = models.CharField(max_length=32, null=True, blank=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    def __str__(self):
        return "id: %s %s count %s" % (self.id, self.parameter, self.count)
    def __unicode__(self):
        return "id: %s %s count %s" % (self.id, self.parameter, self.count)

    class Meta:
        db_table= u'datalists'

class Author(models.Model):
    name = models.CharField(max_length=128)
    institution = models.CharField(max_length=256, null=True, blank=True)
    def __str__(self):
        return "%s" % (self.name)
    def __unicode__(self):
        return "%s" % (self.name)

    class Meta:
        db_table= u'authors'

class Source(models.Model):
    category = models.CharField(max_length=32, null=True, blank=True)
    article_number = models.CharField(max_length=128, null=True, blank=True, help_text="""Article number, journal-specific article identifier, may contain any string""")
    digital_object_id = models.CharField(max_length=128, null=True, blank=True, help_text="""Digital Object Identifier. Example: doi:10.1016/j.adt.2007.11.003""")
    title = models.CharField(max_length=128, help_text="""Title""")
    source_id = models.CharField(max_length=128, null=True, blank=True)
    publisher = models.CharField(max_length=256, null=True, blank=True, help_text="""Publisher of a bibliographic reference. Example: IOP Publishing Ltd""")
    authors = models.ManyToManyField(Author, related_name="sources")
    uri = models.CharField(max_length=256, null=True, blank=True, help_text="""A Uniform Resource Identifier of a bibliographic reference. Example: http://www.iop.org/EJ/abstract/0953-4075/41/10/105002""")
    page_begin = models.CharField(max_length=16, null=True, blank=True, help_text="""Initial page of a bibliographic reference. Example: 22""")
    page_end = models.CharField(max_length=16, null=True, blank=True, help_text="""Final page of a bibliographic reference. Example: 23""")
    volume = models.CharField(max_length=128, null=True, blank=True, help_text="""Volume of the bibliographic reference. Example: 72A""")
    source_name = models.CharField(max_length=256, null=True, blank=True, help_text="""Bibliographic reference name. Example: Physical Review""")
    bibtex = models.CharField(max_length=1024, null=True, blank=True, help_text="""BibTeX representation of reference, for those who already have it in database""")
    comments = models.CharField(max_length=1024, null=True, blank=True)
    year = models.CharField(max_length=16, null=True, blank=True)

    def __str__(self):
        if len(self.title) > 0 :
            return "%s" % self.title
        return "id: %s %s" % (self.id, self.comments)
    def __unicode__(self):
        if len(self.title) > 0 :
            return "%s" % self.title
        return "id: %s %s" % (self.id, self.comments)

    class Meta:
        db_table= u'sources'

class RadiativeProcess(models.Model):
    molecule_state = models.ForeignKey(MoleculeState, on_delete=models.CASCADE)
    x = models.ForeignKey(DataList, related_name="wavelengths", on_delete=models.CASCADE)
    y = models.ForeignKey(DataList, related_name="cross_sections", on_delete=models.CASCADE)
    sources = models.ManyToManyField(Source, related_name="photo_dissociations", null=True, blank=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    def __str__(self):
        return "id: %s %s '%s-%s'" % (self.id, self.molecule_state.molecule.chemical_formula, self.molecule_state.n, self.molecule_state.l )
    def __unicode__(self):
        return "id: %s %s '%s-%s'" % (self.id, self.molecule_state.molecule.chemical_formula, self.molecule_state.n, self.molecule_state.l )

    class Meta:
        db_table = u'photo_dissociations'

