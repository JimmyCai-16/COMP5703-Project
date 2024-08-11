$(document).ready(function () {

  $.getJSON('get/tenements_geojson/', function (tenement_data) {

    tenements = JSON.parse(tenement_data.context);

    //Setting up the map
    const target_map = L.map("target_map", {
      zoomControl: false,
      attributionControl: false,
    }).setView([-19.917574, 143.702789], 5);

    //Setting Up Map Display
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution:
        '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(target_map);


    var geojson_feature = new L.FeatureGroup().addTo(target_map);

    if (tenements.features.length > 0) {
      geojson_layer = L.geoJson(tenements, {

        onEachFeature: function onEachFeature(feature, layer) {
          layer.on({
            // Zoom on click Function
            click: function zoomToFeature(e) {
              target_map.fitBounds(e.target.getBounds());
            },
          });
        },
      }).addTo(geojson_feature);
      try{target_map.fitBounds(geojson_feature.getBounds());}
      catch{console.log('Coordinates for tenements not found. Check if Arcgis servers are in use to fetch coordinates')}
    }

    var markerLayer = new L.FeatureGroup().addTo(target_map);

    $('#addTargetButton').on('click',function (e) {
          
      setTimeout(function(){ 
        target_map.invalidateSize(); 
        if (geojson_feature.getLayers().length > 0) {
          try{target_map.fitBounds(geojson_feature.getBounds());}
          catch{console.log('Coordinates for tenements not found. Check if Arcgis servers are in use to fetch coordinates')}
        }
      }, 200);
      $('#id_target_id').val('');
      $('#id_target_name').val('');
      $('#id_target_description').val('');
      $('#id_location').val('');
      $('#id_location_input').val('');
      $('#addEditTargetForm .modal-header').text('Add Prospect');
      $('#addEditTargetForm #btnSubmit').text('Add');
      markerLayer.clearLayers();
   
    });

    $('#target-table').on('click', 'button:has(.fa-pen)', function (e) {
      setTimeout(function(){ target_map.invalidateSize()}, 200);
      let tableRow = $('#target-table').DataTable().row($(this).parents('tr')).data();
      let location = tableRow['location'].replace(/(\[|\]|,)/gm,'')
      location = location.trim();
      $('#id_target_id').val(tableRow['name']);
      $('#id_target_name').val(tableRow['name']);
      $('#id_target_description').val(tableRow['description']);
      $('#id_location').val(location);
      $('#id_location_input').val(location);
      $('#addEditTargetForm .modal-header').text('Edit Prospect');
      $('#addEditTargetForm #btnSubmit').text('Save');
      var coordinates = location.split(" ")
      markerLayer.clearLayers();
      L.marker(coordinates).addTo(markerLayer);
      
      target_map.setView(coordinates, 9);
  });

    target_map.on('click', function (e) {
      
      markerLayer.clearLayers(); 
      
      var marker = L.marker([e.latlng.lat, e.latlng.lng]).addTo(markerLayer);
      marker.bindPopup(`Latitude: ${e.latlng.lat}  
                        Longitude: ${e.latlng.lng}`).openPopup();

      $('#id_location').val(`${e.latlng.lat} ${e.latlng.lng}`);
      $('#id_location_input').val(`${e.latlng.lat} ${e.latlng.lng}`);
    });
  });
});