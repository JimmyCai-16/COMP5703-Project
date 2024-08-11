# InteractiveMap Documentation

## Introduction

The `InteractiveMap` class is designed to create and manage interactive maps using the Leaflet JavaScript library. It
provides various features and widgets to enhance map functionality.

## Table of Contents

- [Frontend Implementation](#frontend-implementation)
    - [Getting Started](#getting-started)
    - [Instance Creation](#instance-creation)
    - [Config](#config)
    - [Map Event Handling/Callbacks](#map-event-handlingcallbacks)
    - [Widgets](#widgets)
        - [SearchBox](#searchbox)
        - [Toolbar](#toolbar)
    - [Layers](#layers)
    - [Methods](#methods)
    - [Example Usage](#example-usage)

- [Backend Implementation](#backend-implementation)
    - [Important Files](#important-files)
    - [Preparing a QuerySet using GeoJSONSerializer](#preparing-a-queryset-using-geojsonserializer)
    - [Generating GeoJSON Tree](#generating-geojson-tree)
        - [Category Node](#category-node)
        - [Leaf Node](#leaf-node)
    - [Example Implementation](#example-implementation)
        - [utils/app.py](#utilsapppy)
        - [views/app.py](#viewsapppy)


# Frontend Implementation

Javascript documentation below.

## Getting Started

To use the `InteractiveMap` class, include the required libraries, create an HTML container for your map, and initialize
the map using JavaScript. This documentation explains how to create and configure `InteractiveMap` instances.

## Instance Creation

To create an `InteractiveMap` instance, use the following syntax:

```javascript
const selector = $(`#map-container`);
const map1 = new InteractiveMap(selector, settings);

// Or using jQuery
const map2 = selector.InteractiveMap(settings);
```

- `selector` (required): A jQuery selector or DOM element where the map should be initialized.
- `settings` (optional): An object containing configuration settings for the map (see Settings).

Note that re-accessing the `InteractiveMap` for a selector will retrieve any map that has already been created.

## Config

The settings object allows you to configure the behavior of your InteractiveMap. Here are the available settings:

- `viewPort`: An array of [latitude, longitude] representing the initial map view.
- `zoomLevel`: The initial zoom level of the map.
- `width`: The width of the map container (e.g., '100vw' for 100% viewport width).
- `height`: The height of the map container (e.g., '100vh' for 100% viewport height).
- `minZoom`: The minimum allowed zoom level.
- `maxZoom`: The maximum allowed zoom level.
- `widgets`: An array of enabled widgets (e.g., ['minimap', 'fullscreen']).
- `reloadOnPan`: Whether to reload data when the map is panned (boolean).

## Map Event Handling/Callbacks
See `InteractiveMap.Event` for all callbacks and associated docstrings.
Note that this object also includes callbacks for various widgets. Some important events will be discussed within the widgets section.

## Widgets

The `widgets` property allows you to enable or disable specific widgets for your map. Widgets are interactive components
that enhance the map's functionality. Here are the available default widgets:

- `minimap`: Adds a minimap to the map (shows a smaller overview map).
- `fullscreen`: Enables a fullscreen button for expanding the map to fullscreen mode.
- `scale`: Displays a scale indicator on the map.
- `toolbar`: Enables a drawing toolbar for creating shapes on the map. Used to select features and have callbacks for
  each stage of selection (before, after, for each feature).
- `resetBounds`: Adds a button to pan the camera to fit all visible features on the screen.
- `createMark`: Feature to create a mark on the map (custom implementation required).
- `searchBox`: Feature for adding a search box to the map (custom implementation required).
- `mouseCoords`: Displays mouse coordinates on the map.

Adding custom widgets can be done easily by accessing the leaflet instance of an `InteractiveMap` object
via `$(selector).InteractiveMap().map`

### SearchBox
The search box is relatively dynamic in that the user has control over how the functionality
works. Use the `changed` and `submit` events to implement this. Basic search functionality example below:
```javascript
$('#map').InteractiveMap().on(InteractiveMap.Event.Search.changed, function (e) {
    // Calls the filter function which will populate the results UL
    e.detail.widget.filter('permit_id');

}).on(InteractiveMap.Event.Search.submit, function (e) {
    // Find the feature, and zoom to it.
    e.detail.widget.search('permit_id');
});
```
**Events**
- `Search.submit` - When the submit button is clicked.
- `Search.changed` - When the search input has changed.

**Control Methods**
- `control.open()`
- `control.close()`
- `control.reset()`
- `control.filter(property, display)`
- `control.search(property)`
- `control.populateOptions(featureLayers, property, display)`
### Toolbar
The draw toolbar is used to draw shapes on the map. Events are triggered at various stages of the drawing phases so that 
you can implement any desired functionality:

**Events**
- `Toolbar.preDraw` - Triggered before any draw code is run.
- `Toolbar.postDraw` - Triggered after all draw code is run.
- `Toolbar.selectedFeature` - Triggered for each feature that was selected.

## Layers

The `InteractiveMap` class allows you to load and manage map layers. Layers can represent geographical data, and you can
configure their behavior and appearance. Layers are defined in the `settings` object when creating the map instance.

- `url`: Url to fetch GeoJSON data from in tree format.
- `data`: Static GeoJSON alternative.
- `selectAllCheckbox`: Whether the tree for this layer has a checkbox that allows all elements to be selected.
- `collapsed`: Whether the layer tree is collapsed by default,
- `interactive`: Whether the user can interact with a feature layer.
- `style`: Leaflet feature style to be applied to an `L.geoJSON` object. (Defaults `InteractiveMap.defaultFeatureStyle`)
- `toolbar`: Options for the toolbar widget per layer
    - `selectedFeature`: Custom logic per feature on toolbar action.
    - `beforeFeatureSelection`: Custom logic per layer before toolbar action.
    - `afterFeatureSelection`: Custom logic per layer after toolbar action.

Note: See `InteractiveMap.defaultLayerSettings` for default values.

- **Events**
- `Layer.created` - Triggered after a layer has been created.
- `Layer.postLoad` - Triggered after all layers have been loaded.


## Methods

The `InteractiveMap` class provides several methods for interacting with the map:

- `getCombinedBounds()`: Returns the combined bounds of all visible layers on the map.
- `fitBounds(bounds, options)`: Fits the map view to the specified bounds with optional options.
- `load(structure, settings, layerTree)`: Loads GeoJSON data into the map. The `structure` parameter is a tree structure
  representing the layers, `settings` contains layer-specific settings, and `layerTree` is an optional legend container.
- `reload()`: Reloads the InteractiveMap instance, including widgets, layers, and data. This is useful for refreshing
  the map with updated data or settings.

## Example Usage

Here's an example of how to create and configure an `InteractiveMap` instance including the `toolbar` callbacks:

```javascript
const map = $(`#map-container`).InteractiveMap({
    viewPort: [-20.917574, 142.702789],
    zoomLevel: 6,
    width: '100vw',
    height: '100vh',
    minZoom: 2,
    maxZoom: 19,
    widgets: ['minimap', 'fullscreen', 'scale', 'toolbar', 'resetBounds', 'mouseCoords'],
    reloadOnPan: true,
    layers: [
        {
            url: "localhost:8000/interactive_map/api/endpoint/",
            tooltip: (feature) => {
                // Tooltip that shows when you left click a feature on the map layer
                return feature.properties.name;
            }
        }
    ]
});
```

# Backend Implementation

Python/Django documentation below.

## Important Files

- `urls.py`: All endpoints for the map API should be placed here. This should stay true for all installed APPS that use
  the map.
- `utils/`:
    - `/core.py`: Scripts specific to each app, as well as core functionality.
    - `/parcel.py` and `/tenement.py`: Examples for creating generic functions that serialize querysets into the tree
      format used by the `InteractiveMap` frontend.
- `views.py`: Views for associated endpoints. These should return the `JsonResponse` needed to populate a map.

## Preparing a QuerySet using `GeoJSONSerializer`

In order for a queryset to be converted into GeoJSON, it must first be serialized into GeoJSON. This can either be done
manually, or using the `GeoJSONSerializer` from `main/utils/geojson.py`

```python
from tms.models import Tenement
from main.utils.geojson import GeoJSONSerializer

queryset = Tenement.objects.filter(permit_type='EPM')
fields = ['permit_type', 'permit_number', 'permit_id', 'get_permit_status_display']

epm_serialized = GeoJSONSerializer().serialize(queryset, geometry_field='area_polygons', fields=fields)
```

Note that when using fields like `get_permit_status_display` this will call the display function and the resulting
geojson property will be `permit_status_display`.

## Generating GeoJSON Tree

The GeoJSON Tree is an essential component that helps organize and categorize map layers for convenient content filtering. This tree structure consists of two main elements: Nodes and Leaves. Nodes represent categories or subcategories, while Leaves store the actual GeoJSON data.

### Category Node

A Category Node is used to group related layers together.

```python
node = [
    {
        'display': 'Tenements',
        'value': 'tenements',
        'children': [
            {
                # You can add child nodes or leaves here
            }
        ]
    }
]
```

### Leaf Node

A Leaf Node contains specific GeoJSON data along with additional information.
```python
leaf = [
    {
        'display': 'EPM',
        'value': 'epm',
        'colour': (1.0, 1.0, 1.0, 1.0),
        'data': ...  # Some geojson data here.
    }
]
```

## Example Implementation
Here's an example of how to implement the GeoJSON Tree in your Django project:

### utils/app.py
In your `utils/app.py` file, you can define a function to serialize a queryset into GeoJSON format.
```python
from main.utils.geojson import GeoJSONSerializer

def get_tenement_geojson(queryset):
    """Serializes a Tenement QuerySet into GeoJSON"""
    return GeoJSONSerializer().serialize(queryset, geometry_field='area_polygons', fields=['permit_id'])
```

### views/app.py
In your `views/app.py` file, you can create an endpoint that filters a queryset and builds the GeoJSON tree.

```python
from interactive_map.utils.core import ColourMap, map_api_endpoint
from django.http import JsonResponse
from tms.models import Tenement


@map_api_endpoint()
def epm_tenement_endpoint(request, bounding_box):
    """An API endpoint to retrieve a GeoJSON Tree related to the EPM Tenements"""
    # Filter a queryset
    queryset = Tenement.objects.filter(permit_type='EPM', area_polygons__within=bounding_box)

    tree = [
        {
            'display': 'Tenement Tree',
            'value': 'tenement',
            'children': [
                {
                    'display': 'Exploration Permit for Minerals',
                    'value': 'epm',
                    'searchFilter': 'permit_id',
                    'colour': ColourMap.PINK.cmap,
                    'data': get_tenement_geojson(queryset),
                },
            ]
        }
    ]

    # As the JSON is a list, it needs to be sent with safe=false
    return JsonResponse(tree, safe=False, status=200)
```
By following this example, you can create a GeoJSON tree structure that organizes your map layers effectively for use with the InteractiveMap component in your Django project.