import json
import os

# Number of parts to split the list into
num_parts = 10

def converting_json_geojson(list_all_json):
    geojs = {
        "type": "FeatureCollection",
        "features": []
    }

    for d in list_all_json:
        # Check if 'feature' key exists
        if 'feature' in d:
            feature = d['feature']
            geometry = feature.get('geometry', {})
            coordinates = geometry.get('rings', [])
            attributes = feature.get('attributes', {})

            feature_data = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coordinates,
                },
                "properties": attributes,
            }

            geojs["features"].append(feature_data)

    return geojs


class JsonExportPipeline:

    def __init__(self):
        self.items = []
        self.output_dirs = []
        self.layer_names = []

    def process_item(self, item, spider):
        # Collect the JSON data and metadata from the item
        self.items.append(item['data'])
        print('---\n appending data to items \n --------------')

        self.output_dirs.append(item['output_dir'])
        self.layer_names.append(item['layer_name'])

        return item

    def close_spider(self, spider):
        # Get the output directory and layer name from the first item (assuming all items have the same metadata)
        output_dir = self.output_dirs[0]
        layer_name = self.layer_names[0]

        # Ensure that the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # break into 100 per id chunk to avoid big data (1gb) of json
        chunk_size = 100 # absolute number
        list_chunk = []
        for i in range(0, len(self.items), chunk_size):
            chunk = self.items[i:i + chunk_size]
            list_chunk.append(chunk)

        for i in range(len(list_chunk)):
            # Construct the output file path
            output_file_path = os.path.join(output_dir, f'{layer_name}_{i}.json')

            # Write the data to the JSON file
            with open(output_file_path, 'w') as json_file:
                json.dump(list_chunk[i], json_file)

        # When the spider is closed, perform GeoJSON conversion
        geojson_data = converting_json_geojson(self.items)
        # print(geojson_data)

        # try to still apply one geojson as big file
        # Construct the output file path
        output_file_path = os.path.join(output_dir, f'{layer_name}_geojson.json')
        
        # Write the data to the JSON file
        with open(output_file_path, 'w') as json_file:
            json.dump(geojson_data, json_file)