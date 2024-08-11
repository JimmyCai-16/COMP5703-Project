// Some commonly used keycodes
const [VK_0, VK_1, VK_2, VK_3, VK_4, VK_5, VK_6, VK_7, VK_8, VK_9] = [48, 49, 50, 51, 52, 53, 54, 55, 56, 57];
const [VK_NUMPAD0, VK_NUMPAD1, VK_NUMPAD2, VK_NUMPAD3, VK_NUMPAD4, VK_NUMPAD5, VK_NUMPAD6, VK_NUMPAD7, VK_NUMPAD8, VK_NUMPAD9] = [96, 97, 98, 99, 100, 101, 102, 103, 104, 105];
const [VK_W, VK_A, VK_S, VK_D] = [87, 65, 83, 68, 38];
const [VK_UP, VK_LEFT, VK_DOWN, VK_RIGHT] = [38, 37, 40, 39];
const [VK_ESCAPE, VK_DEL, VK_TAB] = [27, 46, 9];
const [VK_CTRL, VK_SHIFT, VK_ALT, VK_WINDOWS] = [17, 16, 18, 91];
const mapLayer = 'map_layer'


// Generates dates based on the number of behind the current date
function generateTimeRanges(timeRanges) {
    let currentDate = new Date()
    let dateRange = []
    for (let i = 0; i < timeRanges.length; i++) {
        currentDate.setDate(currentDate.getDate() - timeRanges[i])      // generates the next date
        dateRange.push(currentDate.toISOString().substring(0, 10))      // stores them as string
    }
    return dateRange
}

// generates colours for the epm layers based on their dates (except expiring)
function getColor(tenementDate, colors, timeRanges) {
    for (let i = timeRanges.length - 1; i > -1; i--) {                   // goes from the earliest to latest date
        if (tenementDate < timeRanges[i]) {                              // checks if the date is earlier than the dates for the tenement
            return colors[i + 1]                                          // assigns the color
        }
    }
    return colors[0]                                                    // in case the tenement recently got assigned to the layer
}


/**
 * Generates the html for the map sidebar, takes in a maps feature list
 * @param features
 * @returns {"<ul class=\"interactive-map-sidebar\"></ul>"}
 */
let generateSidebar = function (features) {

    console.log(features);

    let _inner = function (feature) {
        let content = '';

        for (const [key, entry] of Object.entries(feature)) {

            let name = entry.name;
            let display = entry.display;
            let color = 'color' in entry ? entry.color : '';
            let inner = Object.keys(entry.content).length ? `<ul id="${key}Body" class="collapse show">${_inner(entry.content)}</ul>` : ''

            content += `
                <li>
                    <input id="${key}Check" type="checkbox" name="${name}" value="${key}"/>
                    <label data-bs-toggle="collapse" data-bs-target="#${key}Body">
                        ${(color) ? `<span class="interactive-map-colorbox" style="background: ${color}"></span>` : ''}
                        ${display}
                    </label>
                    ${inner}
                </li>`
        }
        return content;
    }

    return `<ul class="interactive-map-sidebar">${_inner(features)}</ul>`
};

/**
 * Serializes the checkbox values of a checkbox tree, halts a branch at its first checked box.
 * @param initial Head element of the tree, a `ul` selector
 * @returns {*[]}
 */
function serializeCheckboxTree(initial) {
    let traverse = function (node, querySet = []) {
        // Traverse the nodes child branches
        $(node).children('li').each(function () {
            let check = $(this).children('input[type="checkbox"]:checked')[0];

            if (check) {
                // Get all parents and generate an object containing the tree check key,value pairs
                let query = $(this)
                    .parentsUntil(initial, 'ul')
                    .siblings('input[type="checkbox"]')
                    .add(check)  // Add the checkbox as it's not included in the above query
                    .toArray()
                    .reduce((acc, e) => ({...acc, [e.name]: e.value}), {});

                return querySet.push(query);
            }
            // If it wasn't checked, traverse the next branch
            let body = $(this).children('ul');
            if (body.length) {
                return traverse(body, querySet);
            }
        });

        return querySet;
    }

    return traverse(initial);
}

(function ($) {

        // Map object
        let InteractiveMap = function (selector, settings = {}) {
            // Try to find the map instance and return it
            if (Object.keys(selector).length === 0) {
                return false;
            }

            for (let i = 0; InteractiveMap.instances.length; i++) {
                let obj = InteractiveMap.instances[i];

                if (obj[0].id === selector[0].id) {
                    return obj;
                }
            }

            // Save the instance
            this.id = InteractiveMap.instances.length;

            // Push this to the singleton
            InteractiveMap.instances.push(this);

            // Set up some instance settings
            let _this = this;
            let _settings = Object.assign({}, InteractiveMap.defaults, settings);
            this._ajax = _settings.ajax;
            this._data = _settings.data;
            this._features = _settings.features;

            /** Feature handler, allows the client to dynamically index the supplied features. Though nested features
             are required to exist under the 'content' key
             e.g., `this.features.QLD.EPM.A.color` rather than `this.features.QLD.content.EPM.content.A.color`
            */
            let featureHandler = {
                get: function (target, prop, receiver) {
                    if (prop === 'getTarget') {
                        return function () {
                            return target;
                        };
                    } else if (prop in target) {
                        let value = target[prop];
                        if (typeof value === "object" && value !== undefined) {
                            return new Proxy(target[prop], featureHandler);
                        } else {
                            return value;
                        }
                    } else if (target.content && prop in target.content) {
                        return new Proxy(target.content[prop], featureHandler);
                    } else {
                        throw new Error(`Property ${prop} does not exist`);
                    }
                }
            }

            this.controls = {};
            this.tables = []

            // Add some classes to the maps selector (initial container object)
            this.selector = selector;  // the jQuery selector attached to this map
            this.selector.css({
                'width': _settings['width'],
                'height': _settings['height'],
            });

            /**
             * Begin Leaflet related code
             */
            console.log(this.selector[0].id)
            // Put the instance functions here
            this.map = L.map(this.selector[0].id, {
                zoomControl: false,
            }).setView(_settings.viewPort, _settings.zoomLevel);

            //adding world map to map container
            L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: _settings.maxZoom,
                minZoom: _settings.minZoom,
                attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            }).addTo(this.map);

            // this.addFeature = function (name, settings = {}) {
            //     // Gets the feature group, or creates a new one if it doesn't exist
            //     if (_this.layers[name] === undefined) {
            //         _this.layers[name] = new L.featureGroup(settings)
            //     }
            //     else {
            //         console.log('This layer name already exists!')
            //     }
            // }

            // Generate Tool bar
            // this.addToolBar = function (position = 'topleft', name = 'toolbar', polyline = true, polygon = true, circle = true, rectangle = true, marker = true, circlemarker = true, edit = false) {
            //     _this.addFeature(name)
            //     _this.map.addLayer(_this.layers[name]);
            //
            //     _this.controls[name] = new L.Control.Draw({
            //         position: position,
            //         draw: {
            //             polyline: polyline,
            //             polygon: polygon,
            //             circle: circle,
            //             rectangle: rectangle,
            //             marker: marker,
            //             circlemarker: circlemarker,
            //         },
            //         edit: edit
            //     });
            //     _this.map.addControl(_this.controls[name]);
            // }

            // Generate Legend
            // this.addLegend = function (legendName, timeRanges, colors, legendTitle, legendPosition = "bottomright") {
            // }

            // this.addFeature(mapLayer)

            // Sidebar
            if (_settings['showSideBar']) {
                this.sidebar = L.control.slideMenu(generateSidebar(this._features), {
                    icon: "fa-solid fa-layer-group",
                }).addTo(_this.map);

                /**
                 * Serializes the sidebar checkbox selections into a list of potential queries.
                 * @returns {*[]}
                 */
                this.sidebar.serialize = function () {
                    // TODO: Be more specific with this selector multiple maps use the same class so this is bad
                    let sideBar = _this.selector.find('.interactive-map-sidebar');

                    return serializeCheckboxTree(sideBar);
                }

                // Sidebar checkbox interactivity events
                $('.interactive-map-sidebar input[type="checkbox"]').change(function (e) {
                    let check = $(this);
                    let checked = check.prop("checked");
                    let container = check.parent();

                    // Set all children to the value of the checked box
                    container.find('input[type="checkbox"]').prop({
                        checked: checked,
                        indeterminate: false
                    });

                    // Update parent categories all the way to top level
                    container.parentsUntil('.interactive-map-sidebar', 'ul').each(function () {
                        let parent = $(this).siblings('input[type="checkbox"]');
                        let children = $(this).children('li').children('input[type="checkbox"]');

                        // Filter children types
                        let checked = children.filter(":checked");
                        let indeterminate = children.filter(function () {
                            return $(this).prop('indeterminate');
                        });

                        if (checked.length + indeterminate.length === 0) {
                            parent.prop({checked: false, indeterminate: false});
                        } else if (checked.length === children.length) {
                            parent.prop({checked: true, indeterminate: false});
                        } else {
                            parent.prop({checked: false, indeterminate: true});
                        }
                    });

                    console.log('sidebar.serialize()', _this.sidebar.serialize());

                    _this.ajax();
                });
            }

            // Add Minimap
            if (_settings['showMinimap']) {
                // creating mini map's world map
                let miniTiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    minZoom: 2,
                    maxZoom: 3,
                    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                })
                // generating mini map
                this.minimap = new L.Control.MiniMap(miniTiles, {toggleDisplay: true}).addTo(this.map);
            }

            // Add Toolbar
            if (_settings['showToolbar']) {
                _this.addToolBar()
            }

            if (_settings['showFullscreen']) {
                _this.controls['fullscreen'] = L.control.fullscreen();
                _this.map.addControl(_this.controls['fullscreen']);
            }

            // Add Search Box
            if (_settings['showSearchBox']) {
                _this.controls['searchBox'] = new L.Control.Search({
                    layer: _this.layers[mapLayer],
                    propertyName: 'id', // dataset property to search
                    initial: false,
                    marker: false,
                    autoCollapse: true,
                    textPlaceholder: 'Type Permit',
                    // zoom to location
                    moveToLocation: function (tenement) {
                        _this.map.fitBounds(tenement['layer']._bounds);
                    },
                });
                _this.map.addControl(_this.controls['searchBox']);
            }

            if (_settings['showScale']) {
                // miles/km scale to display coordinates
                _this.controls['scale'] = L.control.scale();
                _this.map.addControl(_this.controls['scale']);
            }

            if (_settings['showCursorTracker']) {
                // mouse coordinate tracker
                const Coordinates = L.Control.extend({
                    onAdd: map => {
                        const container = L.DomUtil.create("div");
                        map.addEventListener("mousemove", tenement => {
                            container.innerHTML = `
                                <p>Latitude: ${tenement.latlng.lat.toFixed(4)} | 
                                    Longitude: ${tenement.latlng.lng.toFixed(4)}
                                </p>`;
                        });
                        return container;
                    }
                });
                _this.controls['cursorTracker'] = new Coordinates({position: "bottomleft"});
                _this.map.addControl(_this.controls['cursorTracker']);
            }

            // Add Interactive Table
            if (_settings['showTable']) {
                $('#'+_this.selector[0].id).before('<div id='+'"'+_this.selector[0].id+'-header" class ="map-header">Select tenement(s) displayed using the toolbar to see their details</div>')
                $('#'+_this.selector[0].id).after('<div id='+'"'+_this.selector[0].id+'-footer" class = "map-footer">Results are displayed here</div>')
                $('#'+_this.selector[0].id+'-footer').after('<div id='+'"'+_this.selector[0].id+'-table" class="table-panel"></div>')
                $('#'+_this.selector[0].id+'-table').append(`<div class="container-fluid">
                                                                <div class="row">
                                                                    <div class="col-12">
                                                                        <div class="card shadow mb-2">
                                                                            <div class="card-header">
                                                                                <div class="nav nav-tabs card-header-tabs" id="nav-`+_this.selector[0].id+`-tab" role="tablist"></div>
                                                                            </div>
                                                                            <div class="card-body tab-content overflow-auto" id="nav-`+_this.selector[0].id+`-tabContent"></div>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>`)
                $('#'+_this.selector[0].id+'-table').slideUp();
            }

            /**
             * Adds a polygon to the map with some colour
             * @param polygon an array of coordinates
             * @param settings some settings for the polygon
             */
            this.addPolygon = function (polygon, layerName) {
                // add some polygon to the map
                let feature = _this.layers.get(layer, _this.addLayer(layer))

            }

            /**
             * Add many polygons to the map where all polygons use supplied settings
             * @param polygons an array of polygons
             * @param settings some settings for all polygons
             */
            this.addPolygons = function (polygons, layerName) {
                polygons.forEach((polygon, i, arr) => {
                    _this.addPolygon(polygon, layerName);
                });
            }

            this.addGeoJson = function (geoJsonData, color) {
                const selectionLayer = L.geoJson(geoJsonData, {

                    style: function (feature) {  // Polygon Colour
                        {
                            return {color: color}
                        }
                    },

                    onEachFeature: function onEachFeature(feature, layer) {
                        layer.on({  // Events on mouse hover and click
                            // Highlight Tenement when hovering over it
                            mouseover: function (tenement) {
                                let layer = tenement.target;
                                layer.setStyle({
                                    weight: 5,
                                    fillOpacity: 0.7
                                });
                                layer.bringToFront();
                            },
                            // UN-Highlight tenement when not hovering over it
                            mouseout: function (tenement) {
                                selectionLayer.resetStyle(tenement.target);
                            },
                            // Zoom to Tenement when it is clicked
                            click: function (tenement) {
                                _this.map.fitBounds(tenement.target.getBounds());
                            },
                        });

                        layer.bindTooltip(function (layer) {
                            // Create dynamic tooltip
                            let div = L.DomUtil.create('div');
                            let rows = layer.feature.tooltip.map(obj => `
                                <tr>
                                    <th>${obj.display}</th>
                                    <td>${layer.feature.properties[obj.property]}</td>
                                </tr>
                            `).join('');

                            div.innerHTML = `<table>${rows}</table>`;
                            return div
                        },
                        {
                            sticky: true, // whether to follow the mouse or not
                            className: "map-tooltip" // display design class
                        });
                    }
                }).addTo(_this.layers[mapLayer]);
            }

            this.addTab = function (tabState, tabType, tabStatus){
                let tabName = tabState + "-" + tabType + "-" + tabStatus 
                let status;
                switch (tabStatus){
                    case 'A':
                        status = 'Applications'
                        break;
                    case 'G':
                        status = 'Grants'
                        break;
                    default:
                        status = 'Expired'
                        break;
                }
                $('#nav-'+_this.selector[0].id+'-tab').append(`<a class="nav-link"
                                                                id="nav-`+tabName+`-tab"
                                                                data-bs-toggle="tab"
                                                                data-bs-target="#nav-`+tabName+`"
                                                                role="tab"
                                                                aria-controls="nav-`+tabName+`"
                                                                aria-selected="true"> ( `+ tabState + " ) " + tabType + " Permit " + status + ` 
                                                                    <span class="badge rounded-pill">0</span>
                                                                </a>`)
            }

            this.addTableHTML = function (tableName){
                $('#nav-'+_this.selector[0].id+'-tabContent').append(`<div
                                                                        class="tab-pane"
                                                                        id="nav-`+tableName+`"
                                                                        role="tabpanel"
                                                                        aria-labelledby="nav-`+tableName+`-tab"
                                                                        >

                                                                        <table id="`+tableName+`-table" class="table table-sm dt-responsive table-hover" style="width: 100%">
                                                                            <thead>
                                                                            <tr>
                                                                                <th>Permit Number</th>
                                                                                <th>Permit Type</th>
                                                                                <th>Permit Status</th>
                                                                                <th>Permit sub-status</th>
                                                                                <th>Lodge Date</th>
                                                                                <th>Grant Date</th>
                                                                                <th>Expiry Date</th>
                                                                                <th>Authorised Holder Name</th>
                                                                            </tr>
                                                                            </thead>
                                                        
                                                                            <tbody>
                                                                            </tbody>
                                                        
                                                                        </table>
                                                                        </div>`)
            }

            this.addTable = function (tableName) {
                _this.tables.push(tableName)
                var newTable = $('#'+tableName+'-table').DataTable({
                    lengthMenu: [            // pagination count
                        [10, 25, 50, -1],    // number
                        [10, 25, 50, "All"], //display number
                    ],
                    columns: [
                        {title: "Permit Number", data: "id"},
                        {title: "Permit Type", data: "permit_type"},
                        {title: "Permit Status", data: "permit_status"},
                        {title: "Permit State", data: "permit_state"},
                        {title: "Lodge Date", data: "date_lodged"},
                        {title: "Grant Date", data: "date_granted"},
                        {title: "Expiry Date", data: "date_expired"},
                        {title: "Authorised Holder Name", data: "authorised_holder"},
                    ],   // column headers
                    columnDefs: [{           // Replace empty column value with None
                        "defaultContent": "None",
                        "targets": "_all"
                    }],
                    dom: 'Bfrt<"row"<"col-sm-12 col-md-3"l><"col-sm-12 col-md-4"i><"col-sm-12 col-md-5"p>>', // setting position table, search, toolbar and pagination
                    buttons: [              // Buttons to display in toolbar
                        {
                            text: '<i class="fa fa-trash"></i>',                                // delete button
                            action: function () {
                                $('#'+tableName+'-table').DataTable().rows(".selected").remove().draw();
                                _this.updateHeaders();
                            },
                        },
                        {
                            extend: 'colvis',
                            collectionLayout: 'fixed columns',
                            collectionTitle: 'Column Visibility Control'
                        },   
                        {
                            extend: 'columnToggle',
                            text: "Show/Hide All"
                        },                                                            // column visibility toggle
                        {
                            extend: "collection",                                               // export button
                            className: "custom-html-collection",
                            text: "Export",
                            buttons: [
                                'csv',                                                          // csv
                                'excel',                                                        // excel
                                {
                                    text: "JSON",                                               // JSON
                                    action: function (e, dt, button, config) {
                                        var data = dt.buttons.exportData();
        
                                        $.fn.dataTable.fileSave(
                                            new Blob([JSON.stringify(data)]),
                                            "Interactive Map.json"
                                        );
                                    },
                                },
                            ],
                        },
                    ],
                    select: {                                                                    // Select multiple rows to delete
                        style: "multi",
                    },
                });
                return newTable;
            }

            this.updateHeaders = function () {

                let total_count = 0
                _this.tables.forEach(function (item, index) {
                    let row_count = $("#"+item+"-table").DataTable().rows().count()
                    $("#nav-"+item+"-tab span").text(`${row_count}`);
                    total_count += row_count
                });
                $('#'+_this.selector[0].id+'-footer').empty();
                $('#'+_this.selector[0].id+'-footer').append(`Results <span class="badge rounded-pill">${total_count}</span>`);  
            }
            /**
             * Add a point to the map
             * @param coordinate
             * @param settings
             */
            this.addPoint = function (coordinate, settings) {
                // add some point to the map, I guess this is the target
            }

            this.fromDataTable = function (dataTable) {
                dataTable.rows.each(function (row, index, data) {
                    _this.addPolygon(row.area_polygon);
                });
            }

            this.removePolygon = function (id) {
                // remove the polygon from the map
            }

            this.render = () => {
                // render the map with this
            }

            // event when user creates a shape from the toolbar
            this.map.on(L.Draw.Event.CREATED, function (drawnShape) {
                _this.layers['toolbar'].clearLayers()                          // clear all previous layers

                drawnShape.layer.addTo(_this.layers['toolbar']);
                if (_settings['showTable']) {
                    if (drawnShape.layer instanceof L.Circle) {         // change shape instance if circle (intersection does not work on circles)
                        drawnShape.layer = L.PM.Utils.circleToPolygon(drawnShape.layer, 60);
                    }
            
                    var drawnShapeGJ = drawnShape.layer.toGeoJSON();        // required for intersection check
            
                    // Check if layer is selected in map
                    if (_this.map.hasLayer(_this.layers[mapLayer])) {

                        _this.tables.forEach(function (item, index) {
                            $('#'+item+'-table').DataTable().destroy();
                            $('#'+item+'-table').remove()
                            $('#nav-'+item).remove()
                            $('#nav-'+item+'-tab').remove()
                          });
                        _this.tables.length = 0;
                        _this.layers[mapLayer].eachLayer(function (s_layer) {                    // get all layers
                            s_layer.eachLayer(function (layer) {                                // loop through each layer
                                if (turf.booleanIntersects(drawnShapeGJ, layer.toGeoJSON())) {  // check for interseaction between layer and shape

                                    permitName = layer.feature.properties.permit_state + "-" + layer.feature.properties.permit_type + "-" + layer.feature.properties.permit_status
                                    console.log(permitName, layer.feature.properties)
                                    if (!_this.tables.includes(permitName)){
                                        _this.addTab(layer.feature.properties.permit_state, layer.feature.properties.permit_type, layer.feature.properties.permit_status)
                                        _this.addTableHTML(permitName)
                                        let newTable = _this.addTable(permitName)
                                        newTable.clear().draw();
                                        newTable.row.add(layer.feature.properties).draw();
                                    }
                                    else{
                                        let newTable = $('#'+permitName+'-table').DataTable();
                                        newTable.row.add(layer.feature.properties).draw();
                                    }
                                }
                            })
                        });
                        if(_this.tables.length > 0){
                            _this.updateHeaders();
                            $('#'+_this.selector[0].id+'-table').slideDown();
                        }
                        else{
                            $('#'+_this.selector[0].id+'-footer').empty();
                            $('#'+_this.selector[0].id+'-footer').append(`No Results Found`);
                            $('#'+_this.selector[0].id+'-table').slideUp();
                        }
                        
                    }
                }
            })
            /**
             Map Interaction Events
             */
            this.selector.click(() => {
                // some left click event;
                _this.selector.focus();

            }).contextmenu((e) => {
                // some right click event
                e.preventDefault();  // this disables the default right click context menu

            }).focusin(() => {
                // the map is in focus
            }).focusout(() => {
                // the map is no longer in focus
            }).keydown((e) => {
                // Keyboard inputs
                let keyCode = e.keyCode;
            })

            console.log('features', _this._features);

            // If initial Ajax was supplied, go get it
            this.ajax = function () {
                let sidebar = (this.sidebar) ? this.sidebar.serialize() : '';
                let bounds = _this.map.getBounds();

                let data = {
                    'query': sidebar,
                    'bounds': [bounds._northEast, bounds._southWest]
                }

                $.ajax(Object.assign({}, {
                    contentType: 'application/json',
                    type: "GET",
                    data: {
                        'data': JSON.stringify(data)
                    },
                    success: function (response) {
                         _this.layers[mapLayer].clearLayers(); // clearing all previous polygons on map

                        if (response.geojson) {
                            // Loop through each entry in the response geojson so we can add it to the correct layer
                            $.each(response.geojson, function (i, entry) {
                                let value;
                                let obj = _this.features;

                                // The feature data for an entry exists at the final level, so we need to get that
                                // using the following code block. The number of levels may change depending on the
                                // features input during map initialization so this has to be done dynamically.
                                $.each(_this.levels, function (j, level) {
                                    value = obj[entry.properties[level]];
                                    if (typeof value === undefined) {
                                        return;
                                    }

                                    obj = value;
                                })

                                // This is the property dictionary has colours etc.
                                let feature = value.getTarget();

                                // Add the layer with the right colour
                                _this.addGeoJson(entry, feature.color);
                            });
                        }
                    },
                    error: function (response) {
                        console.log('error', response);
                    }
                }, _this._ajax));
            }

            // Return the Map instance
            return this;
        }

        InteractiveMap.instances = [];
        InteractiveMap.defaults = {
            // Default settings here
            'viewPort': [-20.917574, 142.702789],
            'zoomLevel': 6,
            'height': '100vh',
            'width': '100vw',
            'maxZoom': 19,
            'minZoom': 2,
            'showMinimap': true,
            'ajax': null,
            'data': null,
        };

        $.fn.interactiveMap = InteractiveMap;
        $.fn.InteractiveMap = function (settings) {
            return $(this).interactiveMap(this, settings);
        }

    }
)(jQuery);
