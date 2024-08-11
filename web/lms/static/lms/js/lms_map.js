parcels_map = L.map('parcels_map', {
  zoonControl: false,
  // dragging: false
}).setView([-20.917574, 142.702789], 6);
VIEW_ZOOM = 13

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
}).addTo(parcels_map);


owners_count_color = {
  zero: "#9CA3BA",
  one: "#3D5888",
  two: "#323B6A",
  five: "#0a1936"
}

styles = {
  project:
  {
    weight: 2,
    fillOpacity: 0.05,
    color: '#8f8d8d',
    zIndex: 0
  },
  normal: {
    weight: 2,
    fillOpacity: 0.2,
  },
  selected: {
    weight: 5,
    fillOpacity: 0.8,
    color: "#E78830" 
  },
  hover: {
    weight: 5,
    fillOpacity: 1,
    color: "#E78830"
  }
}

// Init parcels on page first loading
featureCollectionData = JSON.parse(PARCEL_FEATURE_COLLECTION_CONTEXT.replaceAll("&quot;", '"'))
parcelsLayer = L.geoJSON(null, {
  style: function(feature) {
    return styles.normal
  },
  onEachFeature: onEachParcelFeature
}).addTo(parcels_map)

if (Object.keys(featureCollectionData).length > 0){
  parcelsLayer.addData(featureCollectionData);
}


//let selectedFeature;
function updateParcelMapOnSelectingParcel(parcelMapURL, completion) {
 
  console.log(parcelMapURL);
  $.getJSON(parcelMapURL,
    function (responseData) {
      if (!responseData || !responseData.data) return

      selectedFeature = responseData.data.selectedFeature
      featureCollectionData = responseData.data.parcels_feature_collection

      const parcelMiddlePoint = selectedFeature.properties.middle_point.coordinates.slice().reverse() 
      parcels_map.setView(parcelMiddlePoint, VIEW_ZOOM ?? 12)
      // const layer = parcelsLayer.getLayer(selectedFeature.properties.id)
      // parcels_map.panTo(layer.getBounds().getCenter())

      // Set project Geometry
      projectL = L.geoJSON(featureCollectionData.project_geometry, {
        style: function(feature) {
          return styles.project
        },
        
      }).addTo(parcels_map)
      
      // Set Parcels Geometry with updated data
      parcelsLayer.clearLayers()
      parcelsLayer = L.geoJSON(featureCollectionData, {
        style: function(feature) {
          return styles.normal
        },
        onEachFeature: onEachParcelFeature
      }).addTo(parcels_map)

      parcelsLayer.bringToFront();

      parcelsLayer.eachLayer(function (layer) {  
        if(layer.feature.properties.lot == selectedFeature.properties.lot 
          & layer.feature.properties.plan == selectedFeature.properties.plan ) {
          layer.feature.properties["selected"] = true    
          layer.setStyle(styles.selected) 
        } else {
          setLayerToNormal(layer)
          layer.feature.properties["selected"] = false
        }
      });

      completion()
    }
  );
}

function onEachParcelFeature(feature, layer) {
  layer._leaflet_id = feature.properties.id

  layer.on({
    mouseover: function (e) {
      layer.setStyle(styles.hover);
    
      if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
      }
    },
    mouseout: function (e) {
      // geojsonLayer.resetStyle(layer);
      if(layer.feature.properties.lot == selectedFeature.properties.lot 
        & layer.feature.properties.plan == selectedFeature.properties.plan ) {
        layer.setStyle(styles.selected);
      } else {
        setLayerToNormal(layer)
      }
    },
    // Zoom to Tenement when it is clicked
    click: function (e) {
        // parcels_map.fitBounds(e.target.getBounds());
       
        
        // parcelsLayer.eachLayer((l) => {
        //   layer.feature.properties["selected"] = false
        //   setLayerToNormal(layer)
        // })

        // layer.setStyle(styles.selected)
        // layer.feature.properties["selected"] = true
        // parcels_map.panTo(layer.getBounds().getCenter())

        handleParcelChanged(feature.properties.id, feature.properties.url)
    },
  });

  layer.bindTooltip(`<div>${feature.properties.lot}/${feature.properties.plan} - <i class="fa-solid fa-person"></i> ${layer.feature.properties.owners_count}</div>`, {
  
    direction: 'center'
  })
  // .on('tooltipopen', function() {
  //   var tooltip = this.getTooltip();
  //   var content = tooltip.getContent();
  //   var googleMapsLink = 'https://maps.google.com/?q=' + feature.geometry.coordinates[0][0][1] + ',' + feature.geometry.coordinates[0][0][0];
  //  console.log("link",googleMapsLink)
  //   var fullLink = `<a href="${googleMapsLink}" target="_blank">View Full on Google Maps</a>`;
  //   tooltip.setContent(content + '<br>' + fullLink);
  //   tooltip.getElement().style.zIndex = '10000';
    // var link = tooltip._contentNode.querySelector('a');
    // var listener = function(event) {
    //   event.stopPropagation(); // Prevent click event from closing the tooltip
    //   window.open(googleMapsLink, '_blank');
    //   link.removeEventListener('click', listener); // Remove event listener after it's clicked
    // };
    // link.addEventListener('click', listener);
 // });
}

var legend = L.control({ position: "bottomleft" });

legend.onAdd = function(map) {
  var div = L.DomUtil.create("div", "lms-legend");
  // div.innerHTML += "<h4>Tegnforklaring</h4>";
  div.innerHTML += `<i style="background-color: ${owners_count_color.zero}"></i><span>0 owner</span><br>`;
  div.innerHTML += `<i style="background-color: ${owners_count_color.one}"></i><span>1 owner</span><br>`;
  div.innerHTML += `<i style="background-color: ${owners_count_color.two}"></i><span>2 - 5 owners</span><br>`;
  div.innerHTML += `<i style="background-color: ${owners_count_color.five}"></i><span>> 5 owners</span><br>`;
  
  

  return div;
};

legend.addTo(parcels_map);

// ----- Style
function setLayerToNormal(layer) {
  let owners_count = layer.feature.properties.owners_count
  if (!owners_count) {
    layer.setStyle(styles.normal)
  }
  // owners_count = Math.floor(Math.random() * 10);
  if (owners_count === 0) {
    layer.setStyle({...styles.normal, fillOpacity: 0.5, color: owners_count_color.zero, fillColor: owners_count_color.zero, weight: 3})
  } else if (owners_count === 1) {
    layer.setStyle({...styles.normal, fillOpacity: 0.5, weight: 2, color: owners_count_color.one, fillColor: owners_count_color.one})
  } else if (owners_count >= 2 && owners_count <=5 ) {
    layer.setStyle({...styles.normal, weight: 2, fillOpacity: 0.7, color: owners_count_color.two, fillColor: owners_count_color.two})
  } else {
    layer.setStyle({...styles.normal, weight: 3, fillOpacity: 0.8, color: owners_count_color.five, fillColor: owners_count_color.five})
  }

  if (layer.feature.properties.selected) {
    layer.setStyle(styles.selected) 
  }
}


