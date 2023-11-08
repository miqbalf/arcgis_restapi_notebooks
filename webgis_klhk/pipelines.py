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
        #self.output_dirs = []
        
        self.data = []

        # self.items = { self.layer_names:  self.data }
        self.layer_names = []
        self.index_dir = {}

        

    def process_item(self, item, spider):
        
        self.data.append(item['data'])

        # generate a repeating layer_names every index (later we need to identify the actual unique layer_name)
        self.layer_names.append(item['layer_name'])

        # get pair unique only for layer_name : output_dir path (string)
        self.index_dir[item['layer_name']] = item['output_dir']

        return item

    def close_spider(self, spider):

        # init to reconstruct the dictionary, {layer_name1:[data1]...layer_namex:[datax]}
        data_all = {}

        # iterate only unique layer_name,
        for lyr_name in set(self.layer_names):
            # reset to empty list of next unique lyr_name after if in nested loop below
            each_layer_data = []
            for i in range(len(self.layer_names)):
                if lyr_name == self.layer_names[i]:
                    each_layer_data += self.data[i]
                    data_all[lyr_name] = each_layer_data
        
        for layer_name, data in data_all.items():
            chunk_size = 100 # absolute number
            list_chunk = []
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                list_chunk.append(chunk)

            for i in range(len(list_chunk)):
                # Construct the output file path
                output_file_path = os.path.join(self.index_dir[layer_name], f'{layer_name}_{i}.json')

                # Write the data to the JSON file
                with open(output_file_path, 'w') as json_file:
                    json.dump(list_chunk[i], json_file)

            # When the spider is closed, perform GeoJSON conversion
            geojson_data = converting_json_geojson(data)
            # print(geojson_data)

            # try to still apply one geojson as big file
            # Construct the output file path and merge all of each layer_name
            output_file_path = os.path.join(self.index_dir[layer_name], f'{layer_name}_geojson.json')
            
            # Write the data to the JSON file
            with open(output_file_path, 'w') as json_file:
                json.dump(geojson_data, json_file)