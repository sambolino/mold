import os.path
import json
import uuid
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.template import RequestContext
from django.db.models import F
from django.shortcuts import render_to_response,get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from node.models import *
from node.forms import *

def index(request):
    t = get_template('main.html')
    title = 'Search'
    f = Search_form()
    s = Sum_form()
    p = Plot_form()
    html = t.render ({'f':f,'s':s,'p':p,})
    return HttpResponse(html)

def calculate_sum(request, species_id, wavelength, temperature):
    molecule = Molecule.objects.get(inchikey=species_id)

    #to avoid auxiliary states - regardless where are they on the list
    state_first = MoleculeState.objects.filter(molecule=molecule).first()
    sample_process = RadiativeProcess.objects.filter(molecule_state = state_first).first()
    if not sample_process:
        state_last = MoleculeState.objects.filter(molecule=molecule).last()
        sample_process = RadiativeProcess.objects.filter(molecule_state = state_last).first()

    wavelengths = [int(i) for i in sample_process.x.data_values.split()]
    index_of_wavelength = wavelengths.index(int(wavelength))
   
    z,s = (0,)*2
    kB = 1.3804e-16
    cgs = 4.3590e-11
    a = 50.0
    koef=cgs/(kB*float(temperature))
    #states = MoleculeState.objects.filter(molecule=molecule, auxillary = False)
    processes = RadiativeProcess.objects.filter(molecule_state__molecule=molecule)
    
    for process in processes:
        g = 0.5 if (process.molecule_state.n % 2 ==0) else 1.5
        exponent=koef* float(process.molecule_state.energy)
        
        z += g * (2 * process.molecule_state.n + 1) * math.exp(-(exponent))
        
        cross_sections = [float(i) for i in process.y.data_values.split()]
        s += g * (2 * process.molecule_state.n + 1) * math.exp(-(exponent)) * cross_sections[index_of_wavelength]

    result = s/z

    #return HttpResponse(json.dumps("{:.3E}".format(result) + " cm<sup>2</sup>"), mimetype="application/json")
    return HttpResponse(json.dumps("{:.3E}".format(result) + " cm<sup>2</sup>"))

def get_wavelengths(request, species_id):
    molecule = Molecule.objects.get(inchikey=species_id)
    datalist = DataList.objects.filter(wavelengths__molecule_state__molecule=molecule)[:1].get()
    wavelengths = [int(i) for i in datalist.data_values.split()]
    #return HttpResponse(json.dumps(wavelengths), mimetype="application/json")
    return HttpResponse(json.dumps(wavelengths))

def get_XY(request, species_id, n, l):
    molecule = Molecule.objects.get(inchikey=species_id)
    #datalist = DataList.objects.filter(wavelengths__molecule_state__molecule=molecule)[:1].get()
    #wavelengths = [int(i) for i in datalist.data_values.split()]
    process = RadiativeProcess.objects.filter(molecule_state__molecule=molecule).filter(molecule_state__n=n).filter(molecule_state__l=l).get()
    cs = [float(i) for i in process.y.data_values.split()]
    wavelengths = [int(i) for i in process.x.data_values.split()]
    #return HttpResponse(json.dumps(wavelengths), mimetype="application/json")
    t = wavelengths, cs
    return HttpResponse(json.dumps(t))
    #return HttpResponse(json.dumps(wavelengths), json.dumps(cs))

def plot(request, species_id, temperature):
    molecule = Molecule.objects.get(inchikey=species_id)
    processes = RadiativeProcess.objects.filter(molecule_state__molecule=molecule)
    wavelengths = [int(i) for i in processes[0].x.data_values.split()]

    z = 0
    s = [0]*len(wavelengths)
    kB = 1.3804e-16
    cgs = 4.3590e-11
    koef = cgs/(kB*float(temperature))

    for process in processes:
        g = 0.5 if (process.molecule_state.n % 2 ==0) else 1.5
        exponent=koef* float(process.molecule_state.energy)
        
        z += g * (2 * process.molecule_state.n + 1) * math.exp(-(exponent))
        
        cross_sections = [float(i) for i in process.y.data_values.split()]
        for i, cs in enumerate(cross_sections):
            s[i] += g * (2 * process.molecule_state.n + 1) * math.exp(-(exponent)) * cs

    results = [i/z for i in s]

    filename = str(uuid.uuid4()) + '.png'
    plt.clf()
    plt.plot(wavelengths, results, 'ro')
    plt.xlabel('nm');
    plt.ylabel('cm^2');
    #plt.connect('button_press_event', onclick)
    plt.savefig(os.path.dirname(os.path.realpath(__file__)) + '/../static/plots/'+filename)
#    plt.clear()
    res = ["{:.3E}".format(result) for result in results]
    t = filename, wavelengths, res
    #return HttpResponse(json.dumps(t), mimetype="application/json")
    return HttpResponse(json.dumps(t))
    
def onclick(event):
    print('test')
