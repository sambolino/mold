$(document).ready(function(){
    base_url = 'http://servo.aob.rs/mold';
    
    molecules = 'select[name=Molecules]';
    qnj = 'input[name=QNJ]';
    qnv = 'input[name=QNv]';

    molecules1 = 'select[name=Molecules1]';
    wavelength = 'select[name=Wavelength]';
    temperature = 'input[name=Temperature]';

    molecules2 = 'select[name=Molecules2]';
    temperature2 = 'input[name=Temperature2]';

    $("#tabs").tabs();

    $('#plot').click(function () {
      var validation = true;
      if (!isPosInt($(temperature2).val()) || $(temperature2).val()<50) {
        $('#PlotHolder').html('Please enter a number >= 50').removeClass().addClass('error');
        validation = false;
      }
      if(validation){
        $('#PlotHolder').html('Calculating... Please wait a few hundred milisec').removeClass().addClass('calculating');
        request_url = base_url + '/plot/' + $(molecules2).val() + '/' + $(temperature2).val() + '/'
        $.getJSON (request_url, function(data) {
          var wavelengths = data[1];
          var results = data[2];
          var hash = {};
          var i;
          for (i = 0; i < results.length; i++){
            hash[wavelengths[i]]= results[i];
          }

          var columns = Math.ceil(i/30);
          var j = 0;
          var cells = '<table>';
          for(var key in hash)
          {
             if (j==0) cells += "<tr>";
             cells += "<td>" + key + "</td><td class='resultCell'>" + hash[key] + "</td>";
             if (j==columns-1) {
               cells += "</tr>";
               j = 0;
             } else j++;
          }
          cells += '</table>';
          $('#PlotHolder').hide().html('<img src="'+base_url+'/static/plots/'+data[0]+'">'+cells).removeClass().addClass('result').fadeIn(2000);
        });
      }
    });


    $('#calculateSum').click(function () {
      var validation = true;
      if (!isPosInt($(wavelength).val())) {
        $('#SumHolder').html('Please select a wavelength').removeClass().addClass('error');
        validation = false;
      }
      if (!isPosInt($(temperature).val()) || $(temperature).val()<50) {
        $('#SumHolder').html('Please enter a number >= 50').removeClass().addClass('error');
        validation = false;
      }
      if(validation){
        $('#SumHolder').html('Calculating... Please wait a few hundred milisec').removeClass().addClass('calculating');
        request_url = base_url + '/calculate_sum/' + $(molecules1).val() + '/' + $(wavelength).val() + '/' + $(temperature).val() + '/'
        $.getJSON (request_url, function(data) {
          $('#SumHolder').hide().html(data).removeClass().addClass('result').fadeIn(1500);
        });
      }
    });

    $(molecules1).change(function(){
        species_id = $(this).val();
        $(wavelength).resetElem();
        $(temperature).resetElem();
        $(wavelength).removeAttr('disabled');
        request_url = base_url + '/get_wavelengths/'+ species_id + '/';
        $.getJSON(request_url, function(data){
          $.each(data, function(key, value){
            $(wavelength).append('<option value="' + value + '">' + value + '</option>');
          });
        })
    })

    $(wavelength).change(function(){
        $(temperature).resetElem();
        $(temperature).removeAttr('disabled');
    })

    $('#generateXsams').click(function() {
        xsamsDoc = null;
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
