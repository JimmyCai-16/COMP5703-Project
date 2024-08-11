// Some commonly used keycodes
const [VK_0, VK_1, VK_2, VK_3, VK_4, VK_5, VK_6, VK_7, VK_8, VK_9] = [
  48, 49, 50, 51, 52, 53, 54, 55, 56, 57,
];
const [
  VK_NUMPAD0,
  VK_NUMPAD1,
  VK_NUMPAD2,
  VK_NUMPAD3,
  VK_NUMPAD4,
  VK_NUMPAD5,
  VK_NUMPAD6,
  VK_NUMPAD7,
  VK_NUMPAD8,
  VK_NUMPAD9,
] = [96, 97, 98, 99, 100, 101, 102, 103, 104, 105];
const [VK_W, VK_A, VK_S, VK_D] = [87, 65, 83, 68, 38];
const [VK_UP, VK_LEFT, VK_DOWN, VK_RIGHT] = [38, 37, 40, 39];
const [VK_ENTER, VK_ESCAPE, VK_DEL, VK_TAB] = [13, 27, 46, 9];
const [VK_CTRL, VK_SHIFT, VK_ALT, VK_WINDOWS] = [17, 16, 18, 91];

/**
 * InteractiveMap constructor function.
 * Creates an instance of an interactive map.
 *
 * @param {jQuery} selector - The jQuery selector attached to the map container.
 * @param {InteractiveMap.defaultConfig | object} config - Configuration options for the map (optional).
 * @returns {InteractiveMap, boolean} - An instance of the InteractiveMap.
 */
let InteractiveMap = function (selector, config = {}) {
  // Try to find the map instance and return it
  if (Object.keys(selector).length === 0) {
    return false;
  }

  for (let i = 0; i < InteractiveMap.instances.length; i++) {
    let obj = InteractiveMap.instances[i];

    if (obj.selector.id === selector[0].id) {
      return obj;
    }
  }

  // Save the instance
  this.id = InteractiveMap.instances.length;

  // Push this to the singleton
  InteractiveMap.instances.push(this);

  // Set up some instance settings
  let _this = this;
  this.config = Object.assign({}, InteractiveMap.defaultConfig, config);
  this.selector = selector; // the jQuery selector attached to this map
  this.selector.css({
    width: _this.config.width,
    height: _this.config.height,
    "padding-bottom": _this.config.paddingBottom,
  });

  // Add Legend Control
  this.layers = {};
  this.widgets = {};
  this.searchLayer = new L.featureGroup({});
  /**
   * Begin Leaflet related code
   */
  // Put the instance functions here
  this.map = L.map(this.selector[0].id, {
    zoomControl: false,
  }).setView(_this.config.viewPort, _this.config.zoomLevel);

  // Add world map container
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: _this.config.maxZoom,
    minZoom: _this.config.minZoom,
    attribution:
      '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(_this.map);

  // INSTALL WIDGETS
  /**
   * Initialization functions for default InteractiveMap widgets. They will only trigger if within `settings.widgets`
   */
  const widgetFuncs = {
    /**
     * Initializes the Minimap Widget
     */
    minimap: function () {
      if (_this.widgets.minimap) {
        _this.map.removeControl(_this.widgets.minimap);
      }
      if (_this.config.widgets.includes("minimap")) {
        _this.widgets.minimap = new L.Control.MiniMap(
          L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"),
          {
            position: "topright",
            toggleDisplay: true, // Show/hide the minimap button
            minimized: false, // Start minimized
          }
        ).addTo(_this.map);
      }
    },
    /**
     * Initializes the FullScreen Widget
     */
    fullScreen: function () {
      if (_this.widgets.fullscreen) {
        _this.map.removeControl(_this.widgets.fullscreen);
      }
      if (_this.config.widgets.includes("fullscreen")) {
        _this.widgets.fullscreen = L.control.fullscreen({
          position: "topleft", // Position of the control
          title: "Full Screen", // Button tooltip
          titleCancel: "Exit Full Screen", // Tooltip when in full screen mode
          forceSeparateButton: true, // Show separate buttons for fullscreen and exit fullscreen
        }).addTo(_this.map);
      }
    },
    /**
     * Initializes the scale widget
     */
    scale: function () {
      // Remove existing scale if it exists
      if (_this.widgets.scale) {
        _this.map.removeControl(_this.widgets.scale);
      }
      // Set up widget if enabled in settings
      if (_this.config.widgets.includes("scale")) {
        _this.widgets.scale = L.control.scale().addTo(_this.map);
      }
    },
    /**
     * Zoom Button
     */
    zoomButton: function () {
      if (_this.widgets.zoomButton) {
        _this.map.removeControl(_this.widgets.zoomButton);
      }
      if (_this.config.widgets.includes("zoomButton")) {
        _this.widgets.zoomButton = new L.control.zoom({
          position: "topleft",
        }).addTo(_this.map);
      }
    },
    /**
     * Initializes the Draw Toolbar widget
     * onDraw()
     * postDraw()
     * selectedFeature()
     */
    toolbar: function () {
      // Remove any existing drawnItems and drawControl if they exist
      if (_this.widgets.drawnItems || _this.widgets.drawControl) {
        _this.map.removeControl(_this.widgets.drawnItems);
        _this.map.removeControl(_this.widgets.drawControl);
      }

      // Check if the 'toolbar' widget is enabled in settings
      if (_this.config.widgets.includes("toolbar")) {
        // Create a new FeatureGroup for drawn items and add it to the map
        _this.widgets.drawnItems = new L.FeatureGroup().addTo(_this.map);

        // Create a new Draw Control with specific drawing options and add it to the map
        _this.widgets.drawControl = new L.Control.Draw({
          position: "topleft",
          draw: {
            polygon: true,
            circle: true,
            rectangle: true,
            marker: true,
            polyline: true,
            circlemarker: false,
          },
          edit: {
            featureGroup: _this.widgets.drawnItems,
            remove: false,
          },
        }).addTo(_this.map);

        // Set up a draw event handler to respond when a shape is drawn
        _this.map.on(L.Draw.Event.CREATED, function (event) {
          const drawnLayer = event.layer;

          // Remove drawnLayer
          _this.widgets.drawnItems.clearLayers();

          // If no layers just stop here.
          if (!_this.layers) {
            return;
          }

          // Add the new drawnLayer
          _this.widgets.drawnItems.addLayer(drawnLayer);

          // Dispatch Event
          _this.dispatchEvent(
            new CustomEvent(InteractiveMap.Event.Toolbar.preDraw, {
              detail: {
                drawnLayer: event.layer,
                layerType: event.layerType,
              },
            })
          );

          // Check for intersection with other layers and perform some external logic if required
          Object.entries(_this.layers).forEach(([key, targetLayer]) => {
            if (
              _this.map.hasLayer(targetLayer) &&
              targetLayer !== drawnLayer &&
              targetLayer instanceof L.GeoJSON
            ) {
              // Highlight intersecting feature and trigger 'selectedFeature' callback
              targetLayer.eachLayer(function (selectedFeature) {
                if (areGeometriesIntersecting(drawnLayer, selectedFeature)) {
                  _this.dispatchEvent(
                    new CustomEvent(
                      InteractiveMap.Event.Toolbar.selectedFeature,
                      {
                        detail: {
                          drawnLayer: event.layer,
                          layerType: event.layerType,
                          target: { ...selectedFeature, key: targetLayer.key },
                        },
                      }
                    )
                  );
                }
              });
            }
          });

          // Dispatch Event
          _this.dispatchEvent(
            new CustomEvent(InteractiveMap.Event.Toolbar.postDraw, {
              detail: {
                drawnLayer: event.layer,
                layerType: event.layerType,
              },
            })
          );
        });
      }
    },
    /**
     * Reset Zoom control widget
     */
    resetBounds: function () {
      if (_this.widgets.resetBounds) {
        _this.map.removeControl(_this.widgets.resetBounds);
      }
      if (_this.config.widgets.includes("resetBounds")) {
        _this.widgets.resetBounds = new (L.Control.extend({
          options: {
            position: "topleft",
          },
          onAdd: function (/* map */) {
            const control = $(`
                            <div class="leaflet-bar leaflet-control">
                                <a class="leaflet-control-icon leaflet-control-reset-zoom" href="#" title="Reset Zoom"></a>
                            </div>
                        `);

            const button = control.find(".leaflet-control-icon")[0];

            button.addEventListener("click", () => {
              _this.fitBounds(_this.getCombinedBounds());
            });

            return control[0];
          },
        }))().addTo(_this.map);
      }
    },
    /**
     * Click to create mark
     */
    createMark: function () {
      if (_this.widgets.createMark) {
        _this.map.removeLayer(_this.widgets.createMark);
      }
      if (_this.config.widgets.includes("createMark")) {
        _this.widgets.createMark = new L.featureGroup({}).addTo(_this.map);

        _this.map.on("click", function (e) {
          _this.widgets.createMark.clearLayers();

          const marker = L.marker([e.latlng.lat, e.latlng.lng]).addTo(
            _this.widgets.createMark
          );

          _this.dispatchEvent(
            new CustomEvent(InteractiveMap.Event.Mark.created, {
              detail: {
                marker: marker,
                lat: e.latlng.lat,
                lng: e.latlng.lng,
              },
            })
          );
        });
      }
    },
    /**
     * Mouse Coordinates
     */
    mouseCoords: function () {
      if (_this.widgets.coordsDisplay) {
        _this.map.removeControl(_this.widgets.coordsDisplay);
      }
      if (_this.config.widgets.includes("mouseCoords")) {
        // Create the control and add it to the map
        _this.widgets.coordsDisplay = new (L.Control.extend({
          options: {
            position: "bottomleft",
          },
          onAdd: function (_) {
            this._div = L.DomUtil.create("div", "coordinates");
            this.update();
            return this._div;
          },
          update: function (latlng) {
            if (latlng) {
              this._div.innerHTML = `<table><tr><td>Latitude:</td><td>${latlng.lat.toFixed(
                4
              )}</td></tr><tr><td>Longitude:</td><td>${latlng.lng.toFixed(
                4
              )}</td></tr></table>`;
            } else {
              this._div.innerHTML = "";
            }
          },
        }))().addTo(_this.map);

        _this.map.on("mousemove", function (e) {
          _this.widgets.coordsDisplay.update(e.latlng); // Update coordinates on mousemove
        });
      }
    },
    /**
     * Search Box
     */
    searchBox: function () {
      if (_this.widgets.searchBox) {
        _this.map.removeControl(_this.widgets.searchBox);
      }

      if (_this.config.widgets.includes("searchBox")) {
        // Create widget HTML
        const container = $(`
                    <div class="leaflet-bar leaflet-control">
                        <div id="leaflet-search-container">
                            <input class="leaflet-search-input" style="display: none;" type="text" placeholder="Search...">
                            <a class="leaflet-control-icon leaflet-search-submit" href="#" title="Search"></a>
                            <a class="leaflet-control-icon leaflet-search-close" style="display: none;" href="#" title="Close"></a>
                        </div>
                        <div id="leaflet-search-results-container" style="display: none;">
                            <ul></ul>
                        </div>
                    </div>
                `);

        // Create the control
        const searchControl = L.control({ position: "topleft" });

        // Individual controls
        searchControl.textInput = container.find("input.leaflet-search-input");
        searchControl.submitButton = container.find("a.leaflet-search-submit");
        searchControl.closeButton = container.find("a.leaflet-search-close");
        searchControl.searchResults = container.find(
          "#leaflet-search-results-container"
        );
        searchControl.searchResultsUL = container.find(
          "#leaflet-search-results-container ul"
        );

        // Define control methods
        /**
         * Opens the control.
         */
        searchControl.open = () => {
          searchControl.closeButton.show();
          searchControl.textInput.show().focus();
        };

        /**
         * Closes the control.
         */
        searchControl.close = () => {
          searchControl.closeButton.hide();
          searchControl.searchResults.hide();
          searchControl.textInput.hide().blur();
        };

        /**
         * Clear the input and current search results.
         */
        searchControl.clear = () => {
          searchControl.textInput.val("");
          searchControl.searchResultsUL.html("");
        };

        /**
         * Resets the Search widget to its initial state.
         */
        searchControl.reset = () => {
          searchControl.close();
          searchControl.clear();
        };

        /**
         * Triggers basic feature filtering.
         * @param {string} property - Property field for filtering.
         * @param {string | null} display - Display field when showing on filter list.
         */
        searchControl.filter = (property, display = null) => {
          const searchString = searchControl.textInput.val();
          const partialMatches = _this.findFeature(
            property,
            searchString,
            true,
            false,
            false
          );

          searchControl.populateOptions(partialMatches, property, display);
        };

        /**
         * Triggers basic feature searching.
         * @param {string} property - Name of the feature property to match.
         * @returns {Array} - Array of found features
         */
        searchControl.search = (property) => {
          const searchString = searchControl.textInput.val();

          return _this.findFeature(property, searchString, true, true, true);
        };

        /**
         * Populates the search results from a given list of featureLayers.
         * @param {L.LayerGroup[]} featureLayers - Array of feature layers to search within.
         * @param {string} property - Name of the property that will be used for partial matching.
         * @param {string | null} display - Name of the display property that will be shown in the results.
         *  Defaults to search property if not supplied.
         */
        searchControl.populateOptions = (
          featureLayers,
          property,
          display = null
        ) => {
          if (display === null) {
            display = property;
          }
          // Clear all current options
          searchControl.searchResultsUL.empty();

          // Show the control
          if (featureLayers.length > 0) {
            // Populate first 10 results
            const listItems = featureLayers
              .slice(0, 50)
              .map((featureLayer) => {
                const properties = featureLayer.feature.properties;
                return `<li>${properties[display]}</li>`;
              })
              .join("");

            // Sort the created list items alphabetically
            const items = $(listItems).sort((a, b) => {
              const textA = $(a).text().toUpperCase();
              const textB = $(b).text().toUpperCase();
              return textA < textB ? -1 : textA > textB ? 1 : 0;
            });

            // Add the items to the UL
            searchControl.searchResultsUL.append(items);
          } else {
            searchControl.searchResultsUL.append(
              '<li class="leaflet-search-empty"></li>'
            );
          }

          searchControl.searchResults.show();
          searchControl.open();
        };

        const dispatchSearch = () => {
          if (searchControl.textInput.val()) {
            _this.dispatchEvent(
              new CustomEvent(InteractiveMap.Event.Search.submit, {
                detail: {
                  target: searchControl.textInput,
                  value: searchControl.textInput.val(),
                  widget: searchControl,
                },
              })
            );
          }
        };

        // Search results item clicked handler
        searchControl.searchResultsUL.on("click", "li", function () {
          const li = $(this);
          const searchText = li.text();

          // Modify controls
          searchControl.textInput.val(searchText);
          searchControl.searchResultsUL.empty();
          searchControl.searchResults.hide();
          searchControl.textInput.focus();

          // Trigger search event
          dispatchSearch();
        });

        searchControl.textInput
          .on("input", function (e) {
            // Create a new custom event with a different event type and the same event data
            e.preventDefault();
            e.stopPropagation();

            // Get search input information
            const value = searchControl.textInput.val();
            const previousValue = searchControl.textInput.previousValue ?? null;
            const isChanged = value !== previousValue;

            // Dispatch the 'changed' event
            _this.dispatchEvent(
              new CustomEvent(InteractiveMap.Event.Search.changed, {
                detail: {
                  target: searchControl.textInput,
                  value: value,
                  previousValue: previousValue,
                  isChanged: isChanged,
                  widget: searchControl,
                },
              })
            );

            // Update previous value
            searchControl.textInput.previousValue =
              searchControl.textInput.val();
          })
          .on("keydown", function (e) {
            if (e.keyCode === VK_ENTER && searchControl.textInput.val()) {
              e.preventDefault();
              dispatchSearch();
            }
          });

        searchControl.submitButton.on("click", function (e) {
          // Show the search box if it's not yet visible, otherwise submit contents
          if (searchControl.textInput.is(":visible")) {
            dispatchSearch();
          } else {
            _this.widgets.searchBox.open();
          }
        });

        searchControl.closeButton.on("click", function (e) {
          _this.widgets.searchBox.reset();
        });

        searchControl.onAdd = function (map) {
          // Disable map interaction with clicks on the search input
          L.DomEvent.disableClickPropagation(container[0]);

          // Return the container element
          return container[0];
        };

        _this.widgets.searchBox = searchControl;
        _this.widgets.searchBox.addTo(_this.map);
      }
    },
    // Logic is split into pre- & post-promise, so it's not here.
    // legend: function() {}
    // END WIDGETS
    legend: function () {
      if (!_this.config.widgets.includes("legend")) {
        return;
      }
    },
  };

  /**
   * Loads some GeoJSON data into the map
   * layerCreated()
   * @param structure GeoJSON tree structure.
   * @param settings layer settings
   * @param layerTree Tree object for legend container.
   */
  this.load = function (structure, settings, layerTree) {
    settings = { ...InteractiveMap.defaultLayerSettings, ...settings };

    /**
     * Recursively traverse the supplied tree structure, each branch is a child of the parent.
     * @param branch
     * @param parentKey
     * @returns {{field, label: string, layer: *}|{filter, selectAllCheckbox: (boolean|*|boolean), children: *, collapsed: boolean, label}|null}
     */
    function recurse(branch, parentKey) {
      const { display, value } = branch;

      // Generate the layers key, e.g., category_name
      const key = (
        parentKey ? `${parentKey}_${value}` : `${value}`
      ).toLowerCase();

      // If the struct has children, traverse until data layer is present
      if (branch.children) {
        return {
          label: branch.display,
          children: branch.children.map((child) => {
            return recurse(child, key);
          }),
          collapsed: settings.collapsed ?? true,
          selectAllCheckbox: settings.selectAllCheckbox ?? true,
        };
      } else if (branch.data) {
        // Generate color-related values
        const { rgba, colorBox } = generateColourValues(
          branch.colour,
          settings.style
        );

        settings.style = {
          ...settings.style,
          color: rgba,
          fillColor: rgba,
        };

        // Generate the leaflet layer
        const geoJson = JSON.parse(branch.data);

        const layer = L.geoJSON(geoJson, {
          style: settings.style,
          onEachFeature: function (feature, layer) {
            // Mouse interaction for POLYGON type geometry
            if (settings.interactive) {
              // Forward the mouse events for the map features
              layer.on({
                mouseover: function (event) {
                  _this.dispatchEvent(
                    new CustomEvent(InteractiveMap.Event.Feature.mouseOver, {
                      detail: {
                        containerPoint: event.containerPoint,
                        latlng: event.latlng,
                        layerPoint: event.layerPoint,
                        event: event.originalEvent,
                        target: { ...layer, key: key },
                      },
                    })
                  );

                  // Add highlight formatting to non-point features
                  if (feature.geometry.type !== "Point") {
                    event.target.setStyle({
                      weight: 2,
                      fillOpacity: 0.7,
                    });
                  }
                },
                mouseout: function (event) {
                  _this.dispatchEvent(
                    new CustomEvent(InteractiveMap.Event.Feature.mouseOut, {
                      detail: {
                        containerPoint: event.containerPoint,
                        latlng: event.latlng,
                        layerPoint: event.layerPoint,
                        event: event.originalEvent,
                        target: { ...layer, key: key },
                      },
                    })
                  );

                  // Reset formatting for non-point features
                  if (feature.geometry.type !== "Point") {
                    _this.layers[key].resetStyle(event.target);
                  }
                },
                click: function (event) {
                  // If the map config has this flag set, zoom to the clicked feature
                  if (_this.config.zoomToClickedFeature) {
                    _this.zoomToFeatureLayers(layer);
                  }

                  _this.dispatchEvent(
                    new CustomEvent(InteractiveMap.Event.Feature.click, {
                      detail: {
                        containerPoint: event.containerPoint,
                        latlng: event.latlng,
                        layerPoint: event.layerPoint,
                        event: event.originalEvent,
                        layer: layer,
                        target: { ...layer, key: key },
                      },
                    })
                  );
                },
              });

              // Bind a tooltip to the feature layer if included in layer settings
              if (
                settings.tooltip !== InteractiveMap.defaultLayerSettings.tooltip
              ) {
                layer.bindPopup(function () {
                  return settings.tooltip(feature);
                });
              }
            }
          },
          pointToLayer: (feature, latlng) => {
            // Mouse interaction for the POINT type geometry
            if (feature.geometry.type === "Point" && settings.interactive) {
              return L.marker(latlng).bindPopup(feature.properties.title);
            }
          },
        });

        // Add the layer to the map if the struct has the enabled key set
        if (branch.enabled) {
          layer.addTo(_this.map);
        }

        // Store the layer for later
        layer.options = { ...settings, ...layer.options };
        layer.key = key;
        _this.layers[key] = layer;

        // Trigger event
        _this.dispatchEvent(
          new CustomEvent(InteractiveMap.Event.Layer.created, {
            detail: layer,
          })
        );

        // Return the tree representation
        return {
          label: colorBox + display,
          layer: layer,
        };
      } else {
        // No data or children, so invalid branch
        return null;
      }
    }

    // Begin recursively generating the layer and tree structure.
    structure.forEach((layer) => {
      let result = recurse(layer, undefined);
      if (_this.config.widgets.includes("legend")) {
        layerTree.push(result);
      }
    });
  };

  /**
   * Reloads the InteractiveMap instance.
   */
  this.reload = function () {
    return new Promise((resolve, reject) => {
      // Re-initialize all widgets
      Object.entries(widgetFuncs).forEach(([_, widgetInitFunc]) => {
        widgetInitFunc();
      });

      // Remove any existing layers
      Object.entries(_this.layers).forEach(([key, layer]) => {
        if (_this.map.hasLayer(layer)) {
          _this.map.removeLayer(layer);
        }
      });

      // Remove an existing tree for reinitialization.
      if (_this.layerTree) {
        _this.map.removeControl(_this.layerTree);
      }

      // Initialize our tree
      let layerTree = _this.config.widgets.includes("legend") ? [] : null;

      // Begin fetching data using settings layer definitions
      const fetchPromises = _this.config.layers.map((layerSettings) => {
        if (layerSettings.data) {
          _this.load(layerSettings.data, layerSettings, layerTree);
        } else if (layerSettings.url) {
          const bounds = _this.map.getBounds();
          const ne = bounds.getNorthEast();
          const sw = bounds.getSouthWest();

          return fetch(
            layerSettings.url,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": $("[name=csrfmiddlewaretoken]").val(),
              },
              body: JSON.stringify({
                northEast: { lat: ne.lat, lng: ne.lng },
                southWest: { lat: sw.lat, lng: sw.lng },
              }),
            }
            //
          )
            .then((response) => response.json())
            .then((data) => {
              _this.load(data, layerSettings, layerTree);
              return true;
            })
            .catch((error) => {
              console.error("Error fetching GeoJSON data:", error);
            });
        }

        return Promise.resolve(); // Placeholder for layers without data or url
      });

      // Create a new div element for loading spinner
      $("<div>")
        .attr("id", _this.selector[0].id + "-loader-overlay") // Set an id or class
        .attr("class", "loader-overlay") // Set a class
        .html('<p class="loader"></p>') // Set content
        .insertAfter($("#" + _this.selector[0].id));

      // Check if all promises have been completed.
      Promise.all(fetchPromises)
        .then(() => {
          // Remove any existing layer tree
          if (_this.layerTree) {
            _this.map.removeControl(_this.layerTree);
          }

          // Create our layer tree
          if (_this.config.widgets.includes("legend")) {
            _this.layerTree = L.control.layers
              .tree(null, layerTree, {
                spaceSymbol: " ",
                closedSymbol: "+",
                openedSymbol: "-",
                // collapseAll: 'Collapse all',
                // expandAll: 'Expand all',
                collapsed: false,
                position: "bottomright",
                labelIsSelector: "both",
              })
              .addTo(_this.map);
          }

          _this.dispatchEvent(
            new CustomEvent(InteractiveMap.Event.Layer.postLoad, {
              detail: null,
            })
          );

          resolve();
        })
        .catch((error) => {
          console.error("Error fetching data:", error);

          reject(error);
        })
        .finally(() => {
          // remove spinner here
          $("#" + _this.selector[0].id + "-loader-overlay").remove();
        });
    });
  };

  // Perform initial load
  this.reload().then(() => {
    // Pan the camera to the zone after first load.
    const combinedBounds = _this.getCombinedBounds();
    if (combinedBounds.isValid()) {
      _this.fitBounds(combinedBounds, null);
    }
  });

  // Add pan event
  if (_this.config.reloadOnPan) {
    _this.map.on("moveend", this.reload);
  }

  // executes when a layer is selected
  _this.map.on("overlayadd", function (displayLayer) {
    if (_this.config.widgets.includes("searchBox")) {
      displayLayer.layer.addTo(_this.searchLayer);
    }

    if (_this.config.widgets.includes("toolbar")) {
      // Remove drawnLayer
      _this.widgets.drawnItems.clearLayers();
    }
  });

  // executes when a layer is de-selected
  _this.map.on("overlayremove", function (displayLayer) {
    if (_this.config.widgets.includes("searchBox")) {
      _this.searchLayer.removeLayer(displayLayer.layer);
    }

    if (_this.config.widgets.includes("toolbar")) {
      // Remove drawnLayer
      _this.widgets.drawnItems.clearLayers();
    }
  });

  // Keyboard/Mouse Event Handlers
  this.selector
    .click(() => {
      // some left click event;
      // _this.selector.focus();
    })
    .contextmenu((e) => {
      // some right click event
      e.preventDefault(); // this disables the default right click context menu
    })
    .focusin(() => {
      // the map is in focus
    })
    .focusout(() => {
      // the map is no longer in focus
    })
    .keydown((e) => {
      // Keyboard inputs
      let keyCode = e.keyCode;
    });

  // Return the Map instance
  return this;
};

/**
 * List of Interactive Maps on the current page.
 * @type {*[]}
 */
InteractiveMap.instances = [];
/**
 * Default settings for the InteractiveMap
 * @type {{zoomLevel: number, viewPort: number[], maxZoom: number, reloadOnPan: boolean, width: string, minZoom: number, widgets: *[], height: string}}
 */
InteractiveMap.defaultConfig = {
  // Default view port for the map.
  viewPort: [-20.917574, 142.702789],
  zoomLevel: 6,
  height: "100vh",
  width: "100vw",
  paddingBottom: 0,
  minZoom: 2,
  maxZoom: 19,
  // Enabled widgets for the map.
  widgets: [],
  // Whether to reload map when panned. Will perform any associated layer url requests.
  reloadOnPan: false,
  // Zooms to a feature when it is clicked. Requires the interactive flag set to true.
  zoomToClickedFeature: true,
};
/**
 * Default feature style for a specific layer. This is defined in the GeoJSON tree inputs.
 * @type {{fillColor: string, color: string, fillOpacity: number, weight: number, opacity: number}}
 */
InteractiveMap.defaultFeatureStyle = {
  fillColor: "var(--ofx-gray)",
  color: "var(--ofx-gray)",
  weight: 1,
  opacity: 0.8,
  fillOpacity: 0.5,
};
/**
 * Default settings for layers within the constructors ``layers`` list
 * @type {{selectAllCheckbox: boolean, toolbar: {afterSelection: (function(*, *): null), beforeSelection: (function(*, *): null), selectedFeature: (function(*, *, *): null)}, data: null, collapsed: boolean, interactive: boolean, tooltip: (function(*): null), style: (*|{fillColor: string, color: string, fillOpacity: number, weight: number, opacity: number}), url: null}}
 */
InteractiveMap.defaultLayerSettings = {
  url: null,
  data: null,
  selectAllCheckbox: true,
  collapsed: true,
  interactive: true,
  style: InteractiveMap.defaultFeatureStyle,
  /**
   * Tooltip displayed when a feature is clicked with mouse.
   * @param feature Clicked feature
   * @returns string
   */
  tooltip: (feature) => "",
};

// Set up Event handler prototypes
InteractiveMap.prototype = {
  _events: {},
  /**
   * Adds an event listener to the InteractiveMap instance.
   * @param {string} type - The type of event to listen for.
   * @param {Function} listener - The event handler function.
   */
  addEventListener: function (type, listener) {
    if (!this._events) {
      this._events = {};
    }
    if (!this._events[type]) {
      this._events[type] = [];
    }
    this._events[type].push(listener);

    return this;
  },
  /**
   * Adds an event listener to the InteractiveMap instance.
   * @param {string} type - The type of event to listen for.
   * @param {Function} listener - The event handler function.
   */
  on: function (type, listener) {
    this.addEventListener(type, listener);

    return this;
  },
  /**
   * Removes an event listener from the InteractiveMap instance.
   * @param {string} type - The type of event to remove the listener from.
   * @param {Function} listener - The event handler function to remove.
   */
  removeEventListener: function (type, listener) {
    if (!this._events || !this._events[type]) {
      return;
    }
    const index = this._events[type].indexOf(listener);
    if (index !== -1) {
      this._events[type].splice(index, 1);
    }

    return this;
  },
  /**
   * Dispatches an event to the InteractiveMap instance.
   * @param {Event} event - The event object to dispatch.
   */
  dispatchEvent: function (event) {
    if (!this._events || !this._events[event.type]) {
      return;
    }
    event.target = this;
    this._events[event.type].forEach((listener) => listener(event));
  },
  /**
   * Search across all map layers to find features that partially match a specified property or list of properties.
   * If a list of properties is provided, a partial match in ANY of the properties counts as a match.
   * @param {string | string[]} properties - A property name or an array of property names to search within.
   * @param {string} searchString - The text to search for within the specified properties.
   * @param {boolean} onlyVisible - Whether to only search visible layers.
   * @param {boolean} zoomTo - Zooms to the bounding box of all found features if true.
   * @param {boolean} highlight - Highlights the found feature if true.
   * @returns {Array} - An array of matched features across the map layers.
   */
  findFeature: function (
    properties,
    searchString,
    onlyVisible = true,
    zoomTo = false,
    highlight = true
  ) {
    // Set up results list
    const results = [];
    const searchStrLower = searchString.toLowerCase();

    // Turn the properties into a list if it's a string
    if (typeof properties === "string") {
      properties = [properties];
    }

    // Iterate through each layer
    for (const key in this.layers) {
      const layer = this.layers[key];

      // If only visible flag is set, and the layer is not on the map, skip
      if (onlyVisible && !this.map.hasLayer(layer)) {
        continue;
      }

      // Check if the layer is a GeoJSON layer
      if (layer instanceof L.GeoJSON) {
        layer.eachLayer(function (featureLayer) {
          const feature = featureLayer.feature;

          // Check if the feature properties match the search string
          for (const property of properties) {
            if (
              feature.properties &&
              feature.properties.hasOwnProperty(property)
            ) {
              let searchProperty = feature.properties[property].toLowerCase();

              // Store matched result feature
              if (searchProperty.includes(searchStrLower)) {
                results.push({ key: key, ...featureLayer });
              }
            }
          }
        });
      }
    }

    // If zoom to is true, zoom the camera bounds to the combined bounds of all found features
    if (zoomTo) {
      const combinedBounds = L.latLngBounds();

      // Get the combined bounds of all features
      results.forEach((feature) => {
        const bounds = feature._bounds;
        if (bounds) {
          combinedBounds.extend(bounds);
        }
      });

      // Only zoom if bounds were actually found
      if (combinedBounds) {
        this.fitBounds(combinedBounds);
      }
    }

    if (highlight && results) {
      const featureLayer = results[0];
      this.highlightFeature(featureLayer);
    }

    return results;
  },
  /**
   * Search across all map layers to find features that partially match a specified property or list of properties.
   * If a list of properties is provided, a partial match in ANY of the properties counts as a match.
   * @param {string | string[]} properties - A property name or an array of property names to search within.
   * @param {Object <string : string|number>} searchArr - Javascript Object (Associative Array) with properties to search as keys and properties' value to match as value.
   * @param {boolean} onlyVisible - Whether to only search visible layers.
   * @param {boolean} zoomTo - Zooms to the bounding box of all found features if true.
   * @param {boolean} highlight - Highlights the found feature if true.
   * @returns {Array} - An array of matched features across the map layers.
   */
  autoSelectFeaturesWithSameProperties: function (
    properties,
    searchArr,
    onlyVisible = true,
    zoomTo = false,
    highlight = true
  ) {
    // Set up results list
    const results = [];
    //const searchStrLower = searchString.toLowerCase();

    // Turn the properties into a list if it's a string
    if (typeof properties === "string") {
      properties = [properties];
    }

    // Iterate through each layer
    for (const key in this.layers) {
      const layer = this.layers[key];

      // If only visible flag is set, and the layer is not on the map, skip
      if (onlyVisible && !this.map.hasLayer(layer)) {
        continue;
      }

      // Check if the layer is a GeoJSON layer
      if (layer instanceof L.GeoJSON) {
        layer.eachLayer(function (featureLayer) {
          const feature = featureLayer.feature;
          let matchwithAllProperties = true;
          // Check if the feature properties match the search string
          for (const property of properties) {
            //alert("property "+property + "pp" + searchArr.property)
            if (
              feature.properties &&
              feature.properties.hasOwnProperty(property) &&
              feature.properties[property]
            ) {
              let searchProperty = feature.properties[property].toLowerCase();
              let searchStrLower = "";
              // get searchString for the property from searchArr if it exist

              if (searchArr[property]) {
                let searchStr = searchArr[property];
                searchStrLower = searchStr.toLowerCase();
              } else {
                matchwithAllProperties = false;
                break;
              }
              // Store matched result feature

              if (!(searchProperty === searchStrLower)) {
                matchwithAllProperties = false;
                break;
              }
            } else {
              matchwithAllProperties = false;
            }
          }
          if (matchwithAllProperties) {
            if (highlight) results.push({ key: key, ...featureLayer });
            else results.push(featureLayer);
          }
        });
      }
    }

    // If zoom to is true, zoom the camera bounds to the combined bounds of all found features
    if (zoomTo) {
      const combinedBounds = L.latLngBounds();

      // Get the combined bounds of all features
      results.forEach((feature) => {
        const bounds = feature._bounds;
        if (bounds) {
          combinedBounds.extend(bounds);
        }
      });

      // Only zoom if bounds were actually found
      if (combinedBounds) {
        this.fitBounds(combinedBounds);
      }
    }

    if (highlight && results) {
      results.forEach((result) => {
        const featureLayer = result;
        this.highlightFeature(featureLayer);
      });
    }

    console.log("results", results);
    return results;
  },
  /**
   * Returns the combined bounds of all visible layers.
   * @returns {L.LatLngBounds} - Combined bounds of all visible layers.
   */
  getCombinedBounds: function () {
    return getCombinedBounds(this.map, this.layers);
  },
  /**
   * Alias for the leaflet ``fitBounds(bounds, options)``
   * @param bounds
   * @param options
   */
  fitBounds: function (bounds, options) {
    this.map.fitBounds(bounds, options);
  },
  /**
   * Resets the bounds to the bounding box of all visible feature elements.
   */
  resetBounds: function () {
    this.fitBounds(this.getCombinedBounds());
  },
  /**
   * Zooms the window to the bounding box of a feature layer or multiple feature layers.
   * @param {L.featureLayer | L.featureLayer[]} featureLayers - Feature layer(s) being zoomed to.
   * @param {number} buffer - Added buffer to the bounds as a fixed size in degrees of latitude and longitude.
   */
  zoomToFeatureLayers: function (featureLayers, buffer = 0.01) {
    let bounds;

    if (Array.isArray(featureLayers)) {
      // If it's an array of feature layers, combine their bounds
      bounds = getCombinedBounds(this.map, featureLayers);
    } else {
      // If it's a single feature layer, get its bounds
      bounds = getFeatureLayerBounds(featureLayers, buffer);
    }

    if (bounds) {
      if (buffer > 0.0) {
        bounds = addBuffer(bounds, buffer);
      }

      this.fitBounds(bounds);
    }
  },
  /**
   * Temporarily highlights a feature
   * @param {L.Layer | L.Polygon | L.Marker | L.Point} featureLayer - Feature layer to highlight.
   * @param {number} duration - Duration in milliseconds the feature remains highlighted.
   * @param {object} style - Custom style override for highlighted feature.
   */
  highlightFeature: function (featureLayer, duration = 5000, style = {}) {
    // If the feature layer doesn't have a feature, just leave now
    if (!featureLayer || !featureLayer.feature) {
      return;
    }

    // Override default styles with supplied custom style.
    const highlightStyle = Object.assign(
      {},
      {
        color: "#ff0000",
        fillColor: "#ffffff",
        weight: 3,
        opacity: 0.9,
        fillOpacity: 0.1,
      },
      style
    );

    // Apply the highlight style
    const layer = L.geoJSON(featureLayer.feature, {
      interactive: false,
      style: highlightStyle,
    }).addTo(this.map);

    // TODO: Add some transition styling for the fadeout that happens over the supplied duration before the layer is removed

    // After the specified fadeDuration, remove the container element
    if (duration !== 0) {
      setTimeout(() => {
        this.map.removeLayer(layer);
      }, duration);
    }
  },

  selectFeature: function (featureLayer, style = {}, multiple = false) {
    // Override default styles with supplied custom style.
    const selectStyle = Object.assign(
      {},
      {
        color: "#ffff00",
        fillColor: "#ffff00",
        weight: 7,
        opacity: 0.9,
        fillOpacity: 0.5,
      },
      style
    );

    if (multiple) {
      if (!featureLayer || featureLayer.length < 1) {
        return;
      }

      //  Unselect already selected feature
      this.config.layers.forEach((layer) => {
        if (!layer.url) {
          this.config.layers = this.config.layers.filter(
            (l) => l._leaflet_id !== layer._leaflet_id
          );
          this.map.removeLayer(layer);
        }
      });
      featureLayer.forEach((flayer) => {
        //Apply the select style

        const layer = L.geoJSON(flayer.feature, {
          interactive: false,
          style: selectStyle,
        }).addTo(this.map);
        this.config.layers = [
          ...this.config.layers,
          { parcelid: flayer.feature.properties.parcelid },
        ];
      });
    } else {
      // If the feature layer doesn't have a feature, just leave now
      if (!featureLayer || !featureLayer.feature) {
        return;
      }

      //  Unselect already selected feature
      this.config.layers.forEach((layer) => {
        if (!layer.url) {
          this.config.layers = this.config.layers.filter(
            (l) => l._leaflet_id !== layer._leaflet_id
          );
          this.map.removeLayer(layer);
        }
      });
      //Apply the select style
      const layer = L.geoJSON(featureLayer.feature, {
        interactive: false,
        style: selectStyle,
      }).addTo(this.map);
      this.config.layers = [
        ...this.config.layers,
        { parcelid: featureLayer.feature.properties.parcelid },
      ];
    }
  },
};

InteractiveMap.Event = {
  /**
   * General Layer related events.
   */
  Layer: {
    /**
     * Layer has been created
     *
     * Event Detail:
     * - ...layer (L.Layer): The created layer.
     */
    created: "InteractiveMap.Layer.created",
    /**
     * All layers successfully loaded
     */
    postLoad: "InteractiveMap.Layer.postLoad",
  },
  Feature: {
    /**
     * A feature has been clicked. Requires that layer is interactive.
     *
     * Event Detail
     * - containerPoint (object): Point on the Map Container at the mouse position in pixels.
     * - layerPoint (object): Point on the Layer at the mouse position in pixels.
     * - latlng (object): Map coordinates at the mouse position.
     * - event (object): Mouse event data.
     * - target (object): The feature layer associated with the event.
     */
    click: "InteractiveMap.Feature.click",
    /**
     * A feature has been clicked. Requires that layer is interactive.
     *
     * Event Detail
     * - containerPoint (object): Point on the Map Container at the mouse position in pixels.
     * - layerPoint (object): Point on the Layer at the mouse position in pixels.
     * - latlng (object): Map coordinates at the mouse position.
     * - event (object): Mouse event data.
     * - target (object): The feature layer associated with the event.
     */
    mouseOver: "InteractiveMap.Feature.mouseOver",
    /**
     * A feature has been clicked. Requires that layer is interactive.
     *
     * Event Detail
     * - containerPoint (object): Point on the Map Container at the mouse position in pixels.
     * - layerPoint (object): Point on the Layer at the mouse position in pixels.
     * - latlng (object): Map coordinates at the mouse position.
     * - event (object): Mouse event data.
     * - target (object): The feature layer associated with the event.
     */
    mouseOut: "InteractiveMap.Feature.mouseOut",
  },
  /**
   * Toolbar Widget related events.
   */
  Toolbar: {
    /**
     * A Shape is Drawn and before features have been handled.
     *
     * Event Detail:
     * - drawnLayer (object): The drawn layer.
     * - layerType (string): The kind of drawn layer.
     */
    preDraw: "InteractiveMap.Toolbar.preDraw",
    /**
     * After shape has been handled and after features have been handled.
     *
     * Event Detail:
     * - drawnLayer (object): The drawn layer.
     * - layerType (string): The kind of drawn layer.
     */
    postDraw: "InteractiveMap.Toolbar.postDraw",
    /**
     * A selected feature is being handled.
     * Note: This event is triggered for individual features, not all of them at once.
     *
     * Event Detail:
     * - drawnLayer (object): The drawn feature.
     * - layerType (string): The kind of drawn layer.
     * - target (object): The featureLayer which was selected.
     */
    selectedFeature: "InteractiveMap.Toolbar.selectedFeature",
  },
  /**
   * Marker Widget related events.
   */
  Mark: {
    /**
     * A Mark has been created on the map.
     *
     * Event Detail:
     * - lat (float): Marker latitude.
     * - lon (float): Marker longitude.
     */
    created: "InteractiveMap.Mark.created",
  },
  /**
   * Search Widget related events.
   */
  Search: {
    /**
     * When the search has been submitted.
     *
     * Event Detail:
     * - input (jQuery): The search input.
     * - value (string): The contents of the search field.
     * - widget (jQuery): Map search widget control.
     */
    submit: "InteractiveMap.Search.submit",
    /**
     * When the contents of the search input has been changed.
     *
     * Event Detail:
     * - target (jQuery): The search input.
     * - value (string): The contents of the search field.
     * - previousValue (string): The contents before the input was changed.
     * - isChanged (boolean): Whether the input was actually different.
     * - widget (jQuery): Map search widget control.
     */
    changed: "InteractiveMap.Search.changed",
  },
};

(function ($) {
  $.fn._interactiveMap = function (selector, config) {
    return new InteractiveMap(selector, config);
  };

  /**
   * Creates/retrieves existing `InteractiveMap` from a jQuery selector.
   * @param {object} config - Configuration options for the map. See Also: `InteractiveMap.defaultConfig`
   * @returns {InteractiveMap}
   * @constructor
   */
  $.fn.InteractiveMap = function (config) {
    return $(this)._interactiveMap(this, config);
  };
})(jQuery);

// Convert leaflet geometry source: https://github.com/geoman-io/leaflet-geoman/

function destinationVincenty(lonlat, brng, dist) {
  // rewritten to work with leaflet
  const VincentyConstants = {
    a: 6378137,
    b: 6356752.3142,
    f: 1 / 298.257223563,
  };

  const { a, b, f } = VincentyConstants;
  const lon1 = lonlat.lng;
  const lat1 = lonlat.lat;
  const s = dist;
  const pi = Math.PI;
  const alpha1 = (brng * pi) / 180; // converts brng degrees to radius
  const sinAlpha1 = Math.sin(alpha1);
  const cosAlpha1 = Math.cos(alpha1);
  const tanU1 =
    (1 - f) * Math.tan((lat1 * pi) / 180 /* converts lat1 degrees to radius */);
  const cosU1 = 1 / Math.sqrt(1 + tanU1 * tanU1);
  const sinU1 = tanU1 * cosU1;
  const sigma1 = Math.atan2(tanU1, cosAlpha1);
  const sinAlpha = cosU1 * sinAlpha1;
  const cosSqAlpha = 1 - sinAlpha * sinAlpha;
  const uSq = (cosSqAlpha * (a * a - b * b)) / (b * b);
  const A = 1 + (uSq / 16384) * (4096 + uSq * (-768 + uSq * (320 - 175 * uSq)));
  const B = (uSq / 1024) * (256 + uSq * (-128 + uSq * (74 - 47 * uSq)));
  let sigma = s / (b * A);
  let sigmaP = 2 * Math.PI;

  let cos2SigmaM;
  let sinSigma;
  let cosSigma;
  while (Math.abs(sigma - sigmaP) > 1e-12) {
    cos2SigmaM = Math.cos(2 * sigma1 + sigma);
    sinSigma = Math.sin(sigma);
    cosSigma = Math.cos(sigma);
    const deltaSigma =
      B *
      sinSigma *
      (cos2SigmaM +
        (B / 4) *
          (cosSigma * (-1 + 2 * cos2SigmaM * cos2SigmaM) -
            (B / 6) *
              cos2SigmaM *
              (-3 + 4 * sinSigma * sinSigma) *
              (-3 + 4 * cos2SigmaM * cos2SigmaM)));
    sigmaP = sigma;
    sigma = s / (b * A) + deltaSigma;
  }
  const tmp = sinU1 * sinSigma - cosU1 * cosSigma * cosAlpha1;
  const lat2 = Math.atan2(
    sinU1 * cosSigma + cosU1 * sinSigma * cosAlpha1,
    (1 - f) * Math.sqrt(sinAlpha * sinAlpha + tmp * tmp)
  );
  const lambda = Math.atan2(
    sinSigma * sinAlpha1,
    cosU1 * cosSigma - sinU1 * sinSigma * cosAlpha1
  );
  const C = (f / 16) * cosSqAlpha * (4 + f * (4 - 3 * cosSqAlpha));
  const lam =
    lambda -
    (1 - C) *
      f *
      sinAlpha *
      (sigma +
        C *
          sinSigma *
          (cos2SigmaM + C * cosSigma * (-1 + 2 * cos2SigmaM * cos2SigmaM)));
  // const revAz = Math.atan2(sinAlpha, -tmp);  // final bearing
  const lamFunc = lon1 + (lam * 180) / pi; // converts lam radius to degrees
  const lat2a = (lat2 * 180) / pi; // converts lat2a radius to degrees

  return L.latLng(lamFunc, lat2a);
}

function createGeodesicPolygon(origin, radius, sides, rotation) {
  let angle;
  let newLonlat;
  let geomPoint;
  const points = [];

  for (let i = 0; i < sides; i += 1) {
    angle = (i * 360) / sides + rotation;
    newLonlat = destinationVincenty(origin, angle, radius);
    geomPoint = L.latLng(newLonlat.lng, newLonlat.lat);
    points.push(geomPoint);
  }

  return points;
}

function circleToPolygon(circle, sides = 60, withBearing = true) {
  const origin = circle.getLatLng();
  const radius = circle.getRadius();
  const polys = createGeodesicPolygon(origin, radius, sides, 0, withBearing); // these are the points that make up the circle
  const polygon = [];
  for (let i = 0; i < polys.length; i += 1) {
    const geometry = [polys[i].lat, polys[i].lng];
    polygon.push(geometry);
  }
  return L.polygon(polygon, circle.options);
}

function layerToPolygon(layer) {
  if (layer instanceof L.Circle) {
    return circleToPolygon(layer);
  } else {
    return layer;
  }
}

// Check if two Leaflet geometries intersect using Turf.js
function areGeometriesIntersecting(layer1, layer2) {
  const p1 = layerToPolygon(layer1);
  const p2 = layerToPolygon(layer2);

  if (p1 && p2) {
    return turf.booleanIntersects(p1.toGeoJSON(), p2.toGeoJSON());
  }

  return false;
}

/**
 * Returns the combined bounds of all layers on the map.
 * @param {L.Map} map - The Leaflet map instance.
 * @param {Array|Object} layers - An array or object of Leaflet layers to include in the bounds calculation.
 * @returns {L.LatLngBounds} - The combined bounds of the specified layers.
 */
function getCombinedBounds(map, layers) {
  const combinedBounds = L.latLngBounds();

  function handleLayer(layer) {
    if (map.hasLayer(layer)) {
      const bounds = layer.getBounds();
      if (bounds) {
        combinedBounds.extend(bounds);
      }
    }
  }

  if (Array.isArray(layers)) {
    layers.forEach(handleLayer);
  } else if (typeof layers === "object") {
    Object.values(layers).forEach(handleLayer);
  }

  return combinedBounds;
}

/**
 * Returns the bounds of a featureLayer which can be extended by a buffer represented by degrees of latitude and
 * longitude.
 * @param featureLayer - Feature layer to get the bounds of.
 * @param {number} buffer - Added buffer to the bounds as a fixed size in degrees of latitude and longitude.
 * @returns {L.LatLngBounds} - Resulting bounding box.
 */
function getFeatureLayerBounds(featureLayer, buffer = 0.0) {
  let bounds = null;

  if (featureLayer instanceof L.Marker) {
    bounds = L.latLngBounds([featureLayer.getLatLng()]);
  } else if (
    featureLayer instanceof L.Polygon ||
    featureLayer instanceof L.Circle
  ) {
    bounds = featureLayer.getBounds();
  } else if (featureLayer instanceof L.Polyline) {
    bounds = L.latLngBounds(featureLayer.getLatLngs());
  } else {
    throw new Error(
      "Unsupported Feature Layer type. Must be of type L.Polygon, L.Circle, L.Polyline or L.Marker."
    );
  }

  // Extend the result bounds by adding a buffer
  if (bounds && buffer > 0.0) {
    bounds = addBuffer(bounds, buffer);
  }

  return bounds;
}

/**
 * Adds a buffer of lat/lon in degrees to bounds
 * @param {L.LatLngBounds} bounds - Bounding box to add a buffer to.
 * @param {number} buffer - Added buffer to the bounds as a fixed size in degrees of latitude and longitude.
 * @returns {L.LatLngBounds}
 */
function addBuffer(bounds, buffer) {
  if (bounds <= 0.0) {
    throw new Error("Buffer may not be negative or zero.");
  }

  return L.latLngBounds(
    [bounds.getSouthWest().lat - buffer, bounds.getSouthWest().lng - buffer],
    [bounds.getNorthEast().lat + buffer, bounds.getNorthEast().lng + buffer]
  );
}

/**
 * Returns the feature layer at a lat/lon point on supplied feature layers, only if the layer is visible.
 * @param {L.map} map - Leaflet map instance.
 * @param {L.featureLayer[]} layers - Layers to search through.
 * @param {object} latlng - Object with lat/lng keys.
 * @returns {L.featureLayer | null}
 */
function getFeatureLayerAtPoint(map, layers, latlng) {
  // Init feature variable
  let outFeatureLayer = null;

  // Iterate through each layer
  for (const key in layers) {
    const layer = layers[key];

    // Check if the layer is a GeoJSON layer
    if (layer instanceof L.GeoJSON) {
      // If only visible flag is set, and the layer is not on the map, skip
      if (!map.hasLayer(layer)) {
        continue;
      }

      layer.eachLayer(function (featureLayer) {
        const point = turf.point([latlng.lng, latlng.lat]);
        const geometry = featureLayer.feature.geometry;

        if (turf.booleanPointInPolygon(point, geometry)) {
          outFeatureLayer = featureLayer;
        }
      });
    }
  }

  return outFeatureLayer;
}

function areFeaturesEqual(feature1, feature2) {
  // Check if the feature properties are equal
  if (!feature1 || !feature2) {
    return false;
  }

  const propertiesEqual =
    JSON.stringify(feature1.properties) === JSON.stringify(feature2.properties);

  // Check if the feature geometry is equal
  const geometryEqual =
    JSON.stringify(feature1.geometry) === JSON.stringify(feature2.geometry);

  // Return true if both properties and geometry are equal
  return propertiesEqual && geometryEqual;
}

// Misc Layer Functions
/**
 * Generates the colours required for a data layer of the tree
 * @param colour
 * @param style
 * @returns {{rgba: string, bgColour: string, bdColour: string, colorBox: string}}
 */
function generateColourValues(colour, style) {
  if (!colour) {
    return { rgba: "", bgColour: "", bdColour: "", colorBox: "" };
  }

  const rgba = `rgba(${colour[0] * 255}, ${colour[1] * 255}, ${
    colour[2] * 255
  }, ${colour[3]})`;
  const bgColour = `rgba(${colour[0] * 255}, ${colour[1] * 255}, ${
    colour[2] * 255
  }, ${style.fillOpacity})`;
  const bdColour = `rgba(${colour[0] * 255}, ${colour[1] * 255}, ${
    colour[2] * 255
  }, ${style.opacity})`;
  const colorBox = `<span class="leaflet-layertree-color-box" style="background-color: ${bgColour}; border-color: ${bdColour}"></span>`;

  return { rgba, bgColour, bdColour, colorBox };
}

// Function to generate a color from a string
function getColorForStringHash(str) {
  const hash = str.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const hue = ((hash % 360) + 360) % 360; // Ensure positive hue value
  const saturation = 70; // Adjust as needed
  const lightness = 50; // Adjust as needed
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

function getColorForStringFNV1(str) {
  let hash = 0n; // Use BigInt
  for (let i = 0; i < str.length; i++) {
    hash ^= BigInt(str.charCodeAt(i)); // XOR the low 8 bits
    hash *= 16777619n; // FNV prime
  }

  const hue = Number(hash & 0xffn) % 360; // Use the lower 8 bits for hue
  const saturation = Number((hash & 0x3fn) + 40n) % 100; // Use lower 6 bits with a range of 40-100
  const lightness = Number((hash & 0x1fn) + 40n) % 100; // Use lower 5 bits with a range of 40-100
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

function getColorForStringDJB2(str) {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 33) ^ str.charCodeAt(i);
  }
  const hue = hash % 360;
  const saturation = (hash % 50) + 50;
  const lightness = (hash % 30) + 60;
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

// Select the color gen function
const getColorForString = (str) => getColorForStringHash(str);

function getComplementaryColor(color) {
  let r, g, b, a;

  // Check if the color is in hex format (e.g., "#RRGGBB")
  if (color.startsWith("#")) {
    // Remove any leading '#' from the color string
    color = color.replace("#", "");

    // Parse the color into its RGB components
    r = parseInt(color.slice(0, 2), 16);
    g = parseInt(color.slice(2, 4), 16);
    b = parseInt(color.slice(4, 6), 16);
    a = 1; // Default alpha value for hex color
  } else if (color.startsWith("rgba(")) {
    // Extract the RGBA components from the "rgba" format
    const rgbaMatch = color.match(/rgba\((\d+), (\d+), (\d+), (\d+(\.\d+)?)\)/);

    if (rgbaMatch) {
      r = parseInt(rgbaMatch[1]);
      g = parseInt(rgbaMatch[2]);
      b = parseInt(rgbaMatch[3]);
      a = parseFloat(rgbaMatch[4]);
    } else {
      // Handle invalid rgba format
      throw new Error(
        "Invalid rgba format. Should be in the format 'rgba(r, g, b, a)'."
      );
    }
  } else {
    // Handle unsupported color format
    throw new Error(
      "Unsupported color format. Supported formats: hex ('#RRGGBB') or rgba('rgba(r, g, b, a)')."
    );
  }

  // Calculate the complementary color
  const complementaryR = 255 - r;
  const complementaryG = 255 - g;
  const complementaryB = 255 - b;

  // Return the complementary color in rgba format
  return `rgba(${complementaryR}, ${complementaryG}, ${complementaryB}, ${a})`;
}
