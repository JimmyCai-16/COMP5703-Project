// Merge all the features into the map and return
function generate_project_map(tenement_list, target_list) {
  //Setting up the map
  const project_map = L.map("project_map", {
    zoomControl: false,
    attributionControl: false,
  }).setView([-19.917574, 143.702789], 5);

  //Setting Up Map Display
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(project_map);

  var geojson_feature = new L.FeatureGroup().addTo(project_map);

  if (tenement_list.features.length > 0) {
    geojson_layer = L.geoJson(tenement_list, {

      onEachFeature: function onEachFeature(feature, layer) {
        layer.on({
          // Zoom on click Function
          click: function zoomToFeature(e) {
            project_map.fitBounds(e.target.getBounds());
          },
        });
        layer.bindPopup(layer.feature.properties['permit_type'] + " " + layer.feature.properties['permit_number']);
      },
    }).addTo(geojson_feature);
  }

  if (target_list.length != 0){
  target_list.every((target) => {
    var coordinates = target.location.split(" ");
    L.marker(coordinates).addTo(geojson_feature)
        .bindPopup(target.name);
      //               <tr>
      //                 <th>Name:</th>
      //                 <td>${target.name}</td>
      //               </tr>
      //               <tr>
      //                 <th>Latitude:</th>
      //                 <td>${+coordinates[0]}</td>
      //               </tr>
      //               <tr>
      //                 <th>Longitude:</th>
      //                 <td>${+coordinates[1]}</td>
      //               </tr>
      //               <tr>
      //                 <th>Description:</th>
      //                 <td>${target.description}</td>
      //               </tr>
      //             </table>`,
      //             {
                    
      //               sticky: true,
      //               className: "foliumtooltip",
      //             });
    return true;
  });
}
  if (geojson_feature.getLayers().length > 0) {
    try{project_map.fitBounds(geojson_feature.getBounds());}
    catch{console.log('Coordinates for tenements not found. Check if Arcgis servers are in use to fetch coordinates')}
  }
  return project_map;
}


function get_intersected_tenements(tenement_list, target, tenement_data){

  var intersected_tenement={};
  // all four application files are searched to fetch data belonging to the project's tenenments
    tenement_list.every((tenement) => {
      let tenement_id = tenement.type + " " + tenement.number
      // pending application file is searched to find the tenement
      tenement_data.eachLayer(function (layer) {
            if (layer.feature.properties.DISPLAYNAM === tenement_id) {
                // check if tenement is within shape drawn
                if (turf.booleanIntersects(target, layer.toGeoJSON())) {
                    intersected_tenement =  tenement
                }
            }
        });

      return true;
    });
  return intersected_tenement
}