// Merge all the features into the map and return
function generate_tenement_map(tenement_list, target_list) {

  //Setting up the map
  const tenement_map = L.map("tenement_map", {
    zoomControl: false,
    attributionControl: false,
  }).setView([-19.917574, 143.702789], 5);

  //Setting Up Map Display
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(tenement_map);

  var geojson_feature = new L.FeatureGroup().addTo(tenement_map);

  
  if (tenement_list.features.length > 0) {
    geojson_layer = L.geoJson(tenement_list, {

      onEachFeature: function onEachFeature(feature, layer) {
        layer.on({
          // Zoom on click Function
          click: function zoomToFeature(e) {
            tenement_map.fitBounds(e.target.getBounds());
          },
        });
      },
    }).addTo(geojson_feature);
  }

  if (target_list.length != 0){
    target_list.every((target) => {
      var coordinates = target.location.split(" ");
      var marker = L.marker([+coordinates[0], +coordinates[1]]);
      geojson_feature.eachLayer(function (layer) {
        if (turf.booleanIntersects(marker.toGeoJSON(), layer.toGeoJSON())) {
          marker.addTo(geojson_feature);
                // .bindTooltip(`<table>
                //         <tr>
                //           <th>Name:</th>
                //           <td>${target.name}</td>
                //         </tr>
                //         <tr>
                //           <th>Latitude:</th>
                //           <td>${+coordinates[0]}</td>
                //         </tr>
                //         <tr>
                //           <th>Longitude:</th>
                //           <td>${+coordinates[1]}</td>
                //         </tr>
                //         <tr>
                //           <th>Description:</th>
                //           <td>${target.description}</td>
                //         </tr>
                //       </table>`,
                //       {
                        
                //         sticky: true,
                //         className: "foliumtooltip",
                //       });
        }
      });
      return true
    });
  }
  if (geojson_feature.getLayers().length > 0) {
    try{tenement_map.fitBounds(geojson_feature.getBounds());}
    catch{console.log('Coordinates for tenements not found. Check if Arcgis servers are in use to fetch coordinates')}
  }
  return tenement_map;

}

function get_intersected_targets(tenement, target_list, tenement_data){

//Setting up the map
var intersected_targets = []

// pending application file is searched to find the tenement
tenement_data.eachLayer(function (layer) {
    // if tenement found
    if (layer.feature.properties.DISPLAYNAM === tenement) {
      if (target_list.length != 0){
        target_list.every((target) => {
          var coordinates = target.location.split(" ");
          var marker = L.marker(coordinates);
          if (turf.booleanIntersects(marker.toGeoJSON(), layer.toGeoJSON())) {
              target.location = "[ " + coordinates[0] +", " + coordinates[1] + " ]"
              intersected_targets.push(target);
            }
          return true
        });
        }
      return false; // stop the search
    }
    return true; // continue search
  });

return intersected_targets;
}