# -*- coding: utf-8 -*-
#
# This module (which must have the name queryfunc.py) is responsible
# for converting incoming queries to a database query understood by
# this particular node's database schema.
#
# This module must contain a function setupResults, taking a sql object
# as its only argument.
#

# library imports

import logging
from itertools import chain

from vamdctap.sqlparse import sql2Q
from .dictionaries import *

from . import models

log = logging.getLogger("vamdc.node.queryfu")

LIMIT = 1000

#------------------------------------------------------------
# Main function
#------------------------------------------------------------

def setupResults(sql):
    """
    This function is always called by the NodeSoftware.
    """
    # log the incoming query
    log.debug(sql)

    # convert the incoming sql to a correct django query syntax object
    # (sql2Q is a helper function to do this for us).
    q = sql2Q(sql)

    print(q)
    processes = models.RadiativeProcess.objects.filter(q)

    stateids = set(processes.values_list('molecule_state', flat=True))
    states = models.MoleculeState.objects.filter(pk__in=stateids)

#    molecules = set(states.values_list('molecule', flat=True))
    sourceids = set()
    molecules = set()
    energyoriginids = set()
    for state in states:
        molecules.add(state.molecule)
        energyoriginids.add(state.energy_origin.id)

    for molecule in molecules:
        molecule.States = molecule.moleculestate_set.filter(pk__in=stateids.union(energyoriginids))
    for process in processes:
        process.sourcerefs = []
        for source in process.sources.all():
            process.sourcerefs.append(source.id)
            sourceids.add(source.id)
    nstates = len(states)
    nspecies  = len(molecules)

    sources = models.Source.objects.filter(pk__in=sourceids)
    for src in sources:
        src.authnames = src.authors.values_list('name', flat=True)

    nsources = len(sources)
    ncoll = 0
    ntrans = len(processes)

    # standardized and shouldn't be changed.
    headerinfo = {'COUNT-SOURCES'    : nsources,
                  'COUNT-SPECIES'    : nspecies,
                  'COUNT-STATES'     : nstates,
        		  'COUNT-COLLISIONS' : ncoll,
                  'COUNT-RADIATIVE'  : ntrans}

    # Return the data. The keynames are standardized.
    return {'Sources'    : sources,
    	    'RadCross'   : processes,
            'Molecules'  : molecules,
	        'HeaderInfo' : headerinfo}

