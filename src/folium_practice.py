import folium
import geopandas as gpd
import jenkspy

# create sample data
geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "id": 1,
                "value": 10
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-122.5, 37.5],
                        [-122.5, 37.6],
                        [-122.6, 37.6],
                        [-122.6, 37.5],
                        [-122.5, 37.5]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "id": 2,
                "value": 20
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-122.4, 37.5],
                        [-122.4, 37.6],
                        [-122.5, 37.6],
                        [-122.5, 37.5],
                        [-122.4, 37.5]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "id": 3,
                "value": 30
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-122.6, 37.4],
                        [-122.6, 37.5],
                        [-122.7, 37.5],
                        [-122.7, 37.4],
                        [-122.6, 37.4]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "id": 4,
                "value": 40
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-122.7, 37.6],
                        [-122.7, 37.7],
                        [-122.8, 37.7],
                        [-122.8, 37.6],
                        [-122.7, 37.6]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "id": 5,
                "value": 50
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-122.4, 37.4],
                        [-122.4, 37.5],
                        [-122.5, 37.5],
                        [-122.5, 37.4],
                        [-122.4, 37.4]
                    ]
                ]
            }
        }
    ]
}

gdf = gpd.GeoDataFrame.from_features(geojson['features'])

# Set CRS for GeoDataFrame
gdf.crs = 'EPSG:4326'

# create map
m = folium.Map(location=[37.5, -122.5], zoom_start=12)

# create choropleth layer
folium.Choropleth(
    geo_data=gdf,
    data=gdf,
    columns=['id', 'value'],
    key_on='feature.properties.id',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Value',
    threshold_scale=jenkspy.jenks_breaks(gdf['value'], 3)
).add_to(m)

m.save('map.html')
m

