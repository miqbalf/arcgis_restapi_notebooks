def converting_json_geojson(list_all_json):
    geojs = {   "type": "FeatureCollection",
               "features":  [
          {
               "type": "Feature",
               "geometry": {
                    "type": "Polygon",
                    "coordinates": d['feature']['geometry']['rings'],
               },
               "properties": {j:v for j,v in d['feature']['attributes'].items()},
          }
            for d in list_all_json
          ],
          }
    return geojs