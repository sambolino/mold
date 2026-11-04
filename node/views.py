import json
import math
import re
from bisect import bisect_right
from django.conf import settings
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
    base_url = getattr(
        settings, 'MOLD_BASE_URL', request.META.get('SCRIPT_NAME', '')
    ).rstrip('/')
    html = t.render ({'f':f,'s':s,'p':p,'BASE_URL':base_url,})
    return HttpResponse(html)

CALCULATOR_TEMPERATURE_RANGE = (50.0, 50000.0)
MAX_INDIVIDUAL_CHARTS = 20


def _temperature_range(molecule):
    # Thermal averages are calculated directly from the rovibrational states;
    # the narrower intervals shown in individual papers are not hard limits.
    return CALCULATOR_TEMPERATURE_RANGE


def _validate_temperature(molecule, temperature):
    temperature_min, temperature_max = _temperature_range(molecule)
    if temperature < temperature_min or temperature > temperature_max:
        raise ValueError(
            'Temperature for %s must be between %g and %g K.' % (
                molecule.chemical_formula,
                temperature_min,
                temperature_max,
            )
        )


LEGACY_EXPONENT = re.compile(
    r'^([+-]?(?:\d+(?:\.\d*)?|\.\d+))([+-]\d+)$'
)


def _data_float(value):
    try:
        return float(value)
    except ValueError:
        match = LEGACY_EXPONENT.match(value)
        if match is None:
            raise
        return float('%sE%s' % match.groups())


def _aligned_cross_section_data(molecule):
    processes = list(RadiativeProcess.objects.filter(
        molecule_state__molecule=molecule
    ).select_related('molecule_state', 'x', 'y'))
    if not processes:
        raise ValueError('No cross-section data are available for this molecule.')

    sample_process = processes[0]
    raw_wavelengths = [
        _data_float(value) for value in sample_process.x.data_values.split()
    ]
    cross_sections = [
        [_data_float(value) for value in process.y.data_values.split()]
        for process in processes
    ]
    point_count = min(
        [len(raw_wavelengths)] + [len(values) for values in cross_sections]
    )
    if point_count < 2:
        raise ValueError('Not enough aligned cross-section data are available.')

    # Some imported legacy lists contain trailing zeroes or surplus wavelengths
    # beyond their declared count. Only the common x/y portion is meaningful.
    wavelengths = raw_wavelengths[:point_count]
    cross_sections = [values[:point_count] for values in cross_sections]
    return processes, sample_process, wavelengths, cross_sections


def _thermal_cross_section_curve(molecule, temperature):
    processes, sample_process, wavelengths, process_cross_sections = (
        _aligned_cross_section_data(molecule)
    )
    weighted_cross_sections = [0.0] * len(wavelengths)
    partition = 0.0
    kB = 1.3804e-16
    cgs = 4.3590e-11
    coefficient = cgs / (kB * temperature)

    for process, cross_sections in zip(processes, process_cross_sections):
        g = 0.5 if process.molecule_state.n % 2 == 0 else 1.5
        exponent = coefficient * float(process.molecule_state.energy)
        weight = g * (2 * process.molecule_state.n + 1) * math.exp(-exponent)
        partition += weight
        for index, cross_section in enumerate(cross_sections):
            weighted_cross_sections[index] += weight * cross_section

    results = [value / partition for value in weighted_cross_sections]
    return sample_process, wavelengths, results


def _pchip_endpoint_slope(h0, h1, delta0, delta1):
    if delta0 == 0:
        return 0.0
    slope = ((2 * h0 + h1) * delta0 - h0 * delta1) / (h0 + h1)
    if slope * delta0 <= 0:
        return 0.0
    if delta0 * delta1 < 0 and abs(slope) > abs(3 * delta0):
        return 3 * delta0
    return slope


def _pchip_slopes(xs, ys):
    if len(xs) == 2:
        slope = (ys[1] - ys[0]) / (xs[1] - xs[0])
        return [slope, slope]

    h = [xs[index + 1] - xs[index] for index in range(len(xs) - 1)]
    delta = [
        (ys[index + 1] - ys[index]) / h[index]
        for index in range(len(h))
    ]
    slopes = [0.0] * len(xs)
    slopes[0] = _pchip_endpoint_slope(h[0], h[1], delta[0], delta[1])
    slopes[-1] = _pchip_endpoint_slope(h[-1], h[-2], delta[-1], delta[-2])

    for index in range(1, len(xs) - 1):
        if delta[index - 1] == 0 or delta[index] == 0 or delta[index - 1] * delta[index] < 0:
            slopes[index] = 0.0
        else:
            w1 = 2 * h[index] + h[index - 1]
            w2 = h[index] + 2 * h[index - 1]
            slopes[index] = (w1 + w2) / (
                w1 / delta[index - 1] + w2 / delta[index]
            )
    return slopes


def _pchip_value(xs, ys, selected_x):
    slopes = _pchip_slopes(xs, ys)
    segment = min(max(bisect_right(xs, selected_x) - 1, 0), len(xs) - 2)
    h = xs[segment + 1] - xs[segment]
    t = (selected_x - xs[segment]) / h
    t2 = t * t
    t3 = t2 * t
    return (
        (2 * t3 - 3 * t2 + 1) * ys[segment]
        + (t3 - 2 * t2 + t) * h * slopes[segment]
        + (-2 * t3 + 3 * t2) * ys[segment + 1]
        + (t3 - t2) * h * slopes[segment + 1]
    )


def _thermal_plot_data(molecule, temperature, sample_process, wavelengths, results):
    temperature_min, temperature_max = _temperature_range(molecule)
    return {
        'title': 'Thermal average cross section: %s at %g K' % (
            molecule.chemical_formula,
            temperature,
        ),
        'curve_label': 'PCHIP interpolation',
        'prediction_curve_label': 'PCHIP interpolation',
        'point_label': 'Database data',
        'x_label': 'Wavelength',
        'x_unit': sample_process.x.unit or 'nm',
        'y_label': 'Cross section',
        'y_unit': sample_process.y.unit or 'cm2',
        'temperature': temperature,
        'points': [
            {'x': wavelength, 'y': result}
            for wavelength, result in zip(wavelengths, results)
        ],
        'wavelengths': wavelengths,
        'results': ["{:.3E}".format(result) for result in results],
        'wavelength_min': wavelengths[0],
        'wavelength_max': wavelengths[-1],
        'temperature_min': temperature_min,
        'temperature_max': temperature_max,
    }


def calculate_sum(request, species_id, wavelength, temperature):
    try:
        molecule = Molecule.objects.get(inchikey=species_id)
        wavelength_value = float(wavelength)
        temperature_value = float(temperature)
        if not math.isfinite(wavelength_value) or not math.isfinite(temperature_value):
            raise ValueError('Wavelength and temperature must be finite numbers.')
        _validate_temperature(molecule, temperature_value)

        sample_process, wavelengths, results = _thermal_cross_section_curve(
            molecule,
            temperature_value,
        )
        if wavelength_value < wavelengths[0] or wavelength_value > wavelengths[-1]:
            raise ValueError(
                'Wavelength must be between %g and %g %s.' % (
                    wavelengths[0],
                    wavelengths[-1],
                    sample_process.x.unit or 'nm',
                )
            )
        selected_value = _pchip_value(
            wavelengths,
            results,
            wavelength_value,
        )
    except Molecule.DoesNotExist:
        return HttpResponse(
            json.dumps({'error': 'Choose an available molecule.'}),
            content_type='application/json',
            status=404,
        )
    except (TypeError, ValueError) as error:
        return HttpResponse(
            json.dumps({'error': str(error)}),
            content_type='application/json',
            status=400,
        )

    data = _thermal_plot_data(
        molecule,
        temperature_value,
        sample_process,
        wavelengths,
        results,
    )
    data.update({
        'predicted_y': selected_value,
        'selected_wavelength': wavelength_value,
        'predicted_y_formatted': "{:.6E}".format(selected_value),
    })
    return HttpResponse(json.dumps(data), content_type='application/json')

    #return HttpResponse(json.dumps("{:.3E}".format(result) + " cm<sup>2</sup>"), mimetype="application/json")
    return HttpResponse(json.dumps("{:.3E}".format(result) + " cm<sup>2</sup>"))

def get_wavelengths(request, species_id):
    molecule = get_object_or_404(Molecule, inchikey=species_id)
    _, sample_process, wavelengths, _ = _aligned_cross_section_data(molecule)
    temperature_min, temperature_max = _temperature_range(molecule)
    return HttpResponse(json.dumps({
        'wavelength_min': wavelengths[0],
        'wavelength_max': wavelengths[-1],
        'wavelength_unit': sample_process.x.unit or 'nm',
        'temperature_min': temperature_min,
        'temperature_max': temperature_max,
    }), content_type='application/json')


def individual_cross_sections(request, species_id):
    """Return the same individual cross sections selected by the first tab."""
    try:
        molecule = Molecule.objects.get(inchikey=species_id)
        processes = RadiativeProcess.objects.filter(
            molecule_state__molecule=molecule
        ).select_related('molecule_state', 'x', 'y').order_by(
            'molecule_state__n', 'molecule_state__l', 'id'
        )

        filters = {}
        for query_name, model_name in (('qnj', 'molecule_state__n'),
                                       ('qnv', 'molecule_state__l')):
            raw_value = request.GET.get(query_name, '')
            if raw_value != '':
                value = int(raw_value)
                if value < 0:
                    raise ValueError('%s must be a non-negative integer.' % query_name.upper())
                filters[model_name] = value
        processes = processes.filter(**filters)
        process_count = processes.count()
        if process_count > MAX_INDIVIDUAL_CHARTS:
            raise ValueError(
                'This search matches %s individual cross sections. '
                'Enter QNJ and/or QNv to narrow the diagrams to at most %s.' % (
                    process_count,
                    MAX_INDIVIDUAL_CHARTS,
                )
            )

        series = []
        for process in processes:
            if not process.x.data_values or not process.y.data_values:
                continue
            wavelengths = [_data_float(value) for value in process.x.data_values.split()]
            cross_sections = [_data_float(value) for value in process.y.data_values.split()]
            point_count = min(len(wavelengths), len(cross_sections))
            if point_count < 2:
                continue
            state = process.molecule_state
            state_parts = []
            if state.n is not None:
                state_parts.append('J=%s' % state.n)
            if state.l is not None:
                state_parts.append('v=%s' % state.l)
            state_label = ', '.join(state_parts) or 'state %s' % state.id
            series.append({
                'title': 'Individual cross section: %s (%s)' % (
                    molecule.chemical_formula, state_label
                ),
                'curve_label': 'PCHIP interpolation',
                'point_label': 'Database data',
                'x_label': process.x.parameter or 'Wavelength',
                'x_unit': process.x.unit or 'nm',
                'y_label': process.y.parameter or 'Cross section',
                'y_unit': process.y.unit or 'cm2',
                'points': [
                    {'x': x, 'y': y}
                    for x, y in zip(
                        wavelengths[:point_count],
                        cross_sections[:point_count],
                    )
                ],
            })
    except Molecule.DoesNotExist:
        return HttpResponse(
            json.dumps({'error': 'Choose an available molecule.'}),
            content_type='application/json',
            status=404,
        )
    except (TypeError, ValueError) as error:
        return HttpResponse(
            json.dumps({'error': str(error)}),
            content_type='application/json',
            status=400,
        )

    if not series:
        return HttpResponse(
            json.dumps({'error': 'No cross-section data match this search.'}),
            content_type='application/json',
            status=404,
        )
    return HttpResponse(
        json.dumps({'series': series}),
        content_type='application/json',
    )

def get_XY(request, species_id, n, l):
    molecule = Molecule.objects.get(inchikey=species_id)
    #datalist = DataList.objects.filter(wavelengths__molecule_state__molecule=molecule)[:1].get()
    #wavelengths = [int(i) for i in datalist.data_values.split()]
    process = RadiativeProcess.objects.filter(molecule_state__molecule=molecule).filter(molecule_state__n=n).filter(molecule_state__l=l).get()
    cs = [_data_float(value) for value in process.y.data_values.split()]
    wavelengths = [_data_float(value) for value in process.x.data_values.split()]
    point_count = min(len(wavelengths), len(cs))
    wavelengths = wavelengths[:point_count]
    cs = cs[:point_count]
    #return HttpResponse(json.dumps(wavelengths), mimetype="application/json")
    t = wavelengths, cs
    return HttpResponse(json.dumps(t))
    #return HttpResponse(json.dumps(wavelengths), json.dumps(cs))

def plot(request, species_id, temperature):
    try:
        molecule = Molecule.objects.get(inchikey=species_id)
        temperature_value = float(temperature)
        if not math.isfinite(temperature_value):
            raise ValueError('Temperature must be a finite number.')
        _validate_temperature(molecule, temperature_value)
        sample_process, wavelengths, results = _thermal_cross_section_curve(
            molecule,
            temperature_value,
        )
        data = _thermal_plot_data(
            molecule,
            temperature_value,
            sample_process,
            wavelengths,
            results,
        )
    except Molecule.DoesNotExist:
        return HttpResponse(
            json.dumps({'error': 'Choose an available molecule.'}),
            content_type='application/json',
            status=404,
        )
    except (TypeError, ValueError) as error:
        return HttpResponse(
            json.dumps({'error': str(error)}),
            content_type='application/json',
            status=400,
        )
    return HttpResponse(json.dumps(data), content_type='application/json')
