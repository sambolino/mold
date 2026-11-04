$(document).ready(function(){
    var base_url = window.MOLD_BASE_URL || '';
    
    molecules = 'select[name=Molecules]';
    qnj = 'input[name=QNJ]';
    qnv = 'input[name=QNv]';

    var molecules1 = 'select[name=Molecules1]';
    var wavelength = '#ThermalWavelength';
    var temperature = '#ThermalTemperature';
    var thermalRange = null;

    var molecules2 = 'select[name=Molecules2]';
    var temperature2 = 'input[name=Temperature2]';
    var plotRange = null;

    $("#tabs").tabs();

    function formattedRange(minimum, maximum) {
      return Number(minimum).toLocaleString('en-US') + '–' +
        Number(maximum).toLocaleString('en-US') + ' K';
    }

    function valueInsideRange(value, range) {
      return isFinite(value) && value >= Number(range.temperature_min) &&
        value <= Number(range.temperature_max);
    }

    function loadPlotRange() {
      var speciesId = $(molecules2).val();
      plotRange = null;
      $('#PlotTemperatureRange').text('');
      if (!speciesId) {
        return;
      }

      $.getJSON(base_url + '/get_wavelengths/' + encodeURIComponent(speciesId) + '/', function(data) {
        plotRange = data;
        $(temperature2)
          .attr('min', data.temperature_min)
          .attr('max', data.temperature_max)
          .attr('step', 'any');
        var currentValue = Number($(temperature2).val());
        if (!valueInsideRange(currentValue, data)) {
          $(temperature2).val(Math.min(
            Math.max(5000, Number(data.temperature_min)),
            Number(data.temperature_max)
          ));
        }
        $('#PlotTemperatureRange').text(
          'Available calculation range: ' + formattedRange(data.temperature_min, data.temperature_max)
        );
      }).fail(function() {
        $('#PlotTemperatureRange').text('The temperature range could not be loaded.');
      });
    }

    $(molecules2).change(loadPlotRange);
    loadPlotRange();

    $('#plot').click(function () {
      var temperatureValue = Number($(temperature2).val());
      if (!plotRange) {
        $('#PlotHolder').html('Choose a molecule first.').removeClass().addClass('error');
        return;
      }
      if (!valueInsideRange(temperatureValue, plotRange)) {
        $('#PlotHolder').html(
          'Temperature must be between ' + plotRange.temperature_min + ' and ' +
          Number(plotRange.temperature_max).toLocaleString('en-US') + ' K.'
        ).removeClass().addClass('error');
        return;
      }

      $('#PlotHolder').html('Calculating... Please wait a few hundred milisec').removeClass().addClass('calculating');
      var request_url = base_url + '/plot/' + encodeURIComponent($(molecules2).val()) + '/' + encodeURIComponent($(temperature2).val()) + '/';
      $.getJSON(request_url, function(data) {
        $('#PlotHolder').hide().html('<div id="MoldInteractivePlot"></div>').removeClass().addClass('result').fadeIn(350);
        MoldInteractiveChart.render(document.getElementById('MoldInteractivePlot'), data);
      }).fail(function(xhr) {
        var message = 'The plot could not be calculated.';
        if (xhr.responseJSON && xhr.responseJSON.error) {
          message = xhr.responseJSON.error;
        }
        $('#PlotHolder').html(message).removeClass().addClass('error');
      });
    });


    function clearThermalResult() {
      $('#SumHolder').empty().removeClass('result error calculating');
    }

    function thermalError(message) {
      $('#SumHolder').html(message).removeClass('result calculating').addClass('error');
    }

    $(molecules1).change(function(){
        var species_id = $(this).val();
        thermalRange = null;
        $(wavelength).val('').prop('disabled', true).removeAttr('min max');
        $(temperature).val('5000').prop('disabled', true);
        $('#calculateSum').prop('disabled', true);
        $('#WavelengthRange').text('');
        clearThermalResult();

        if (!species_id) {
          return;
        }

        var request_url = base_url + '/get_wavelengths/' + encodeURIComponent(species_id) + '/';
        $.getJSON(request_url, function(data){
          thermalRange = data;
          $(wavelength)
            .attr('min', data.wavelength_min)
            .attr('max', data.wavelength_max)
            .attr('placeholder', data.wavelength_min + ' – ' + data.wavelength_max)
            .prop('disabled', false)
            .val(data.wavelength_min);
          $(temperature)
            .attr('min', data.temperature_min)
            .attr('max', data.temperature_max)
            .prop('disabled', false);
          var temperatureValue = Number($(temperature).val());
          if (!valueInsideRange(temperatureValue, data)) {
            $(temperature).val(Math.min(
              Math.max(5000, Number(data.temperature_min)),
              Number(data.temperature_max)
            ));
          }
          $('#WavelengthRange').text(
            data.wavelength_min + '–' + data.wavelength_max + ' ' + data.wavelength_unit
          );
          $('#TemperatureRange').text(
            formattedRange(data.temperature_min, data.temperature_max)
          );
          $('#calculateSum').prop('disabled', false);
        }).fail(function() {
          thermalError('The available wavelength range could not be loaded.');
        });
    });

    $(wavelength + ', ' + temperature).on('change keyup input', clearThermalResult);

    $('#ThermalForm').submit(function(event) {
      event.preventDefault();
      if (!thermalRange) {
        thermalError('Choose a molecule first.');
        return;
      }

      var wavelengthValue = Number($(wavelength).val());
      var temperatureValue = Number($(temperature).val());
      if (!isFinite(wavelengthValue)) {
        thermalError('Enter a valid wavelength.');
        return;
      }
      if (wavelengthValue < Number(thermalRange.wavelength_min) || wavelengthValue > Number(thermalRange.wavelength_max)) {
        thermalError(
          'Wavelength must be between ' + thermalRange.wavelength_min + ' and ' +
          thermalRange.wavelength_max + ' ' + thermalRange.wavelength_unit + '.'
        );
        return;
      }
      if (!isFinite(temperatureValue) ||
          temperatureValue < Number(thermalRange.temperature_min) ||
          temperatureValue > Number(thermalRange.temperature_max)) {
        thermalError(
          'Temperature must be between ' + thermalRange.temperature_min + ' and ' +
          Number(thermalRange.temperature_max).toLocaleString('en-US') + ' K.'
        );
        return;
      }

      $('#SumHolder')
        .html('Calculating the interpolated thermal cross section...')
        .removeClass('result error')
        .addClass('calculating');
      $('#calculateSum').prop('disabled', true);
      var request_url = base_url + '/calculate_sum/' + encodeURIComponent($(molecules1).val()) + '/' +
        encodeURIComponent($(wavelength).val()) + '/' + encodeURIComponent($(temperature).val()) + '/';
      $.getJSON(request_url, function(data) {
        var html = '<div class="GprResultLabel">Predicted value</div>';
        html += '<div class="GprResultValue">' + data.predicted_y_formatted + '</div>';
        html += '<div class="GprExactPoint">λ = ' + data.selected_wavelength + ' ' + data.x_unit;
        html += ' &nbsp; | &nbsp; T = ' + data.temperature + ' K';
        html += ' &nbsp; | &nbsp; σ = ' + data.predicted_y_formatted + ' ' + data.y_unit + '</div>';
        html += '<div id="ThermalPredictionPlot"></div>';
        $('#SumHolder').html(html).removeClass('calculating error').addClass('result');
        MoldInteractiveChart.renderPrediction(
          document.getElementById('ThermalPredictionPlot'),
          data
        );
      }).fail(function(xhr) {
        var message = 'The thermal cross section could not be calculated.';
        if (xhr.responseJSON && xhr.responseJSON.error) {
          message = xhr.responseJSON.error;
        }
        thermalError(message);
      }).always(function() {
        $('#calculateSum').prop('disabled', false);
      });
    });

    $('#generateXsams').click(function() {
        xsamsDoc = null;
        $('#IndividualPlotHolder').empty().removeClass('result error calculating');
        var searchString = "select * ";
        var nextClause = "where ";
  	    var validation = true;
        if ($(molecules).val()!=''){
           searchString += nextClause; 
           searchString += "InchiKey='" + $(molecules).val() + "' ";
           nextClause = "and ";
        }
        if ($(qnj).val()!='')
          if(isPosInt($(qnj).val())){
            searchString += nextClause;
            searchString += "MoleculeQNJ=" + $(qnj).val() + " ";
            nextClause = "and ";
            }
          else {
            document.getElementById('XMLHolder').innerHTML = 'Please enter a valid positive integer for QN';
            validation = false;
          }
        if ($(qnv).val()!='')
          if(isPosInt($(qnv).val())){
            searchString += nextClause;
            searchString += "MoleculeQNv=" + $(qnv).val() + " ";
            }
          else {
            document.getElementById('XMLHolder').innerHTML = 'Please enter a valid positive integer for QN';
            validation = false;
          }
        if (validation){
          var str = base_url + "/tap/sync?REQUEST=doQuery&LANG=VSS2&FORMAT=XSAMS&QUERY=" + searchString;
	        //LoadXMLString("XMLHolder", '');
	        document.getElementById('XMLHolder').innerHTML = 'Loading...';
          LoadXML("XMLHolder",str);

          var selectedMolecule = $(molecules).val();
          if (!selectedMolecule) {
            $('#IndividualPlotHolder')
              .html('Choose a molecule to display its cross-section diagrams.')
              .addClass('error');
            return;
          }
          var plotUrl = base_url + '/individual_cross_sections/' +
            encodeURIComponent(selectedMolecule) + '/?qnj=' +
            encodeURIComponent($(qnj).val()) + '&qnv=' +
            encodeURIComponent($(qnv).val());
          $('#IndividualPlotHolder')
            .html('Loading diagrams...')
            .addClass('calculating');
          $.getJSON(plotUrl, function(data) {
            var holder = document.getElementById('IndividualPlotHolder');
            holder.innerHTML = '';
            (data.series || []).forEach(function(series, index) {
              var chart = document.createElement('div');
              chart.className = 'IndividualPlot';
              chart.id = 'IndividualPlot-' + index;
              holder.appendChild(chart);
              MoldInteractiveChart.render(chart, series);
            });
            $('#IndividualPlotHolder').removeClass('calculating error').addClass('result');
          }).fail(function(xhr) {
            var message = 'The individual cross-section diagrams could not be loaded.';
            if (xhr.responseJSON && xhr.responseJSON.error) {
              message = xhr.responseJSON.error;
            }
            $('#IndividualPlotHolder')
              .html(message)
              .removeClass('calculating result')
              .addClass('error');
          });
        }
    })

});

function isPosInt(n){
    //return 0 === n % (!isNaN(parseFloat(n)) && 0 <= ~~n);
    return (!isNaN(parseFloat(n)) && 0 <= ~~n);
}

(function( $ ){
    $.fn.resetElem = function() {
	$(this).prop('disabled', true).html('<option value="" selected="selected">---------</option>');
    };
})( jQuery );
