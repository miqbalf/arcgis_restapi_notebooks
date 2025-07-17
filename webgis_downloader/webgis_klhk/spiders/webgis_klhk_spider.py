import scrapy
from urllib.parse import urlencode
import json
import os

from pathlib import Path

# force to put variable in this root level
#name project bbox, change this later if you change the filename json in input_json
aoi_name = 'bbox_muna.json'


# The path to the script's directory is combined with the JSON filename
output_path = os.path.dirname(os.path.dirname(Path(__file__).parent)) # root dir

aoi_input_folder = os.path.join(output_path,'input_json')
aoi_input = os.path.join(aoi_input_folder, aoi_name)

# CHANGE THIS PLEASE! or in the var above (name)
# with open('./input_json/bbox_indo.json', 'r') as json_file:
with open(aoi_input, 'r') as json_file:
    dict_data = json.load(json_file)

str_bbox = str(dict_data)

class WebgisKlhkSpiderSpider(scrapy.Spider):
    name = "webgis_klhk_spider"
    allowed_domains = ["geoportal.menlhk.go.id"]
    start_urls = ["https://geoportal.menlhk.go.id/server/rest/services/Time_Series"]

    def parse(self, response):
        layer_links = response.css('li')
        for link in layer_links:
            
            layer = link.css('a::attr(href)').extract()[0]
            page_url = 'https://geoportal.menlhk.go.id' + layer

            ### this one to iterate to all but exclude these layers
            # excluded_data_toscrape = ['PL_1990', 'PL_1996', 'PL_2000', 'PL_2003', 'PL_2006', 
            #                      'PL_2009','PL_2011', 'PL_2012', 'PL_2013', 'PL_2014', 
            #                      'PL_2015'] # not sure why, but the MoF not publish the feature data of these
            
            # # Check if NONE of the excluded keywords are in the URL
            # if not any(keyword in page_url for keyword in excluded_data_toscrape):
            #     print('page_url:', page_url)
            #     yield scrapy.Request(page_url, callback=self.parse_individual_layer)

            ### this one to iterate ONLY these layers in included_data_toscrape
            included_data_toscrape = ['PL_2023', 'PL_2024']
            
            # Check if NONE of the excluded keywords are in the URL
            if any(keyword in page_url for keyword in included_data_toscrape):
                print('page_url:', page_url)
                yield scrapy.Request(page_url, callback=self.parse_individual_layer)

    
    def parse_individual_layer(self, response):
        # Process the data from the individual link here
        # You can use response.xpath or response.css to extract data
        # For example:
        layer_link_name = response.css('ul li a::attr(href)').extract()[0]
        print('layer_link_name: ',layer_link_name)

        page_url = 'https://geoportal.menlhk.go.id' + layer_link_name
        #print(f'Title: {title}')
        # yield {'link': layer_link_name}
        yield scrapy.Request(page_url, callback=self.parse_objectid, meta={'layer_name': layer_link_name})

    def parse_objectid(self, response):
        # get xpath name objectid_name for queries
        objectid_name = response.xpath('/html/body/div/ul[4]/li[1]/text()').get().strip().replace('\r\n', '')
        # print(f'Title: {objectid_name}')
        layer_name = response.meta.get('layer_name')
        # yield {layer_name: objectid_name}
        page_url = 'https://geoportal.menlhk.go.id' + layer_name + '/query'
        
        yield scrapy.Request(page_url, callback = self.parse_query, meta={'oid_name' :objectid_name, 'layer_name': layer_name })

    def parse_query(self, response):
        oid_name = response.meta.get('oid_name')
        layer_name = response.meta.get('layer_name')
        layer_link_name = layer_name

        params = {
                "where": f"{oid_name} >= -1",
                "text": "",
                "objectIds": "",
                "time": "",
                "timeRelation": "esriTimeRelationOverlaps",
                "geometry": str_bbox,
                "geometryType": "esriGeometryEnvelope",
                "inSR": '4326', 
                "spatialRel": "esriSpatialRelIntersects",
                "units": "esriSRUnit_Foot",
                "outFields": "",
                "returnGeometry": "false",
                "returnTrueCurves": "false",
                "maxAllowableOffset": "",
                "geometryPrecision": "",
                "outSR": '4326',
                "havingClause": "",
                "returnIdsOnly": "true",
                "returnCountOnly": "false",
                "orderByFields": "",
                "groupByFieldsForStatistics": "",
                "outStatistics": "",
                "returnZ": "false",
                "returnM": "false",
                "gdbVersion": "",
                "historicMoment": "",
                "returnDistinctValues": "false",
                "resultOffset": "",
                "resultRecordCount": "",
                "returnExtentOnly": "false",
                "sqlFormat": "none",
                "datumTransformation": "",
                "parameterValues": "",
                "rangeValues": "",
                "quantizationParameters": "",
                "featureEncoding": "esriDefault",
                "f": "pjson"
            }
        
        page_url = 'https://geoportal.menlhk.go.id' + layer_link_name + '/query?' + urlencode(params)

        yield scrapy.Request(page_url, self.parse_query_post, meta={'layer_link_name':layer_link_name})

    def parse_query_post(self, response):
        layer_link_name = response.meta.get('layer_link_name')

        # print(f'\n------- THIS IS THE LAYER LINK NAME CHECK PLEASE!! \n: {layer_link_name} -------- \n')

        layer_name_parts = layer_link_name.split('/')
        layer_name = layer_name_parts[-3]

        output_dir = os.path.join(output_path,f'json_raw/output_json_{layer_name}')  # Define your output directory
        os.makedirs(output_dir, exist_ok=True)

        data = json.loads(response.text)

        dict_oid = {layer_link_name: data}
        # print(dict_oid)
                
        # keep the loop, since previous result, missing first index, not sure why
        for key, value in dict_oid.items():
            # print(f'\n------- THIS IS THE  VALUE QUERY  CHECK PLEASE!! \n: {value} -------- \n')
            list_oids = dict_oid[key]['objectIds']
            if list_oids is not None:
                oid_name = dict_oid[key]['objectIdFieldName']
                chunk_size = 1000
                query_chunks = []
                oid_chunk = []
                for i in range(0, len(list_oids), chunk_size):
                    chunk = list_oids[i:i + chunk_size]
                    query = ' or '.join([f"{oid_name} = {str(oid)}" for oid in chunk])
                    query_chunks.append(query)
                    oid_chunk.append(chunk)

                dict_oid[key]['query'] = query_chunks
                dict_oid[key]['chunk_oid'] = oid_chunk

                print(len(oid_chunk),'-----------------')

                with open(f'./json_raw/{layer_name}_input_id_query.json','w') as json_file:
                    json.dump(dict_oid, json_file) # this one important to save and track back again later if error happening in the files (file_small) not acquiring features

            elif list_oids is None:
                # print(list_oids)
                output_file_path = os.path.join(output_dir, f'failed_layers_{layer_name}.json')

                with open(output_file_path,'w') as json_file:
                    json.dump({'error_id_layer':layer_name}, json_file)

        # fix_dict = {}
        for key, value in dict_oid.items():
            if dict_oid[key].get('query') is not None:
                # print(f'\n------- THIS IS THE  VALUE QUERY  CHECK PLEASE!! \n: {dict_oid[key].get("query")} -------- \n')
        #         a +=1
        #         print(a)
        #         print(key)
                # fix_dict[key] = value
                 # Construct the output file path based on layer_name
                
                a = 0
                for q in dict_oid[key]['query']:
                    # print(f'\n------- THIS IS THE  VALUE QUERY  CHECK PLEASE!! \n: {q} -------- \n') #debug mode
                    a += 1 # this one is producing interation batch download in file json
                    obj_ids_query = q
                    post_data  = { 'where': obj_ids_query,
                                'text': '',
                                'objectIds': '',
                                'time': '',
                                'timeRelation': 'esriTimeRelationOverlaps',
                                'geometry': str_bbox,
                                'geometryType': 'esriGeometryEnvelope',
                                'inSR': '4326',
                                'spatialRel': 'esriSpatialRelIntersects',
                                'distance': '',
                                'units': 'esriSRUnit_Foot',
                                'relationParam': '',
                                'outFields': '*',
                                'returnGeometry': 'true',
                                'returnTrueCurves': 'false',
                                'maxAllowableOffset': '',
                                'geometryPrecision': '',
                                'outSR': '4326',
                                'havingClause': '',
                                'returnIdsOnly': 'false',
                                'returnCountOnly': 'false',
                                'orderByFields': '',
                                'groupByFieldsForStatistics':  '',
                                'outStatistics': '',
                                'returnZ': 'false',
                                'returnM': 'false',
                                'gdbVersion': '',
                                'historicMoment': '',
                                'returnDistinctValues': 'false',
                                'resultOffset': '',
                                'resultRecordCount': '',
                                'returnExtentOnly': 'false',
                                'sqlFormat': 'none',
                                'datumTransformation': '',
                                'parameterValues': '',
                                'rangeValues': '',
                                'quantizationParameters': '',
                                'featureEncoding': 'esriDefault',
                                'f': 'geojson',
                            }
                    
                    # print(post_data)
                    
                    output_file_path = os.path.join(output_dir, f'{layer_name}_{a}.json')

                    post_url = 'https://geoportal.menlhk.go.id' + layer_link_name + '/query'

                    request = scrapy.FormRequest(url=post_url, formdata=post_data, callback=self.save_json, meta={'output_file_path': output_file_path,
                                                                                                              'output_file_name':f'{layer_name}_{a}.json',
                                                                                                              'layer_name': layer_name,
                                                                                                              'layer_link_name':layer_link_name,
                                                                                                              'output_dir': output_dir})

                    yield request

    def save_json(self, response):
        layer_name = response.meta.get('layer_name')
        output_dir = response.meta.get('output_dir')
        output_file_path = response.meta.get('output_file_path')
        output_file_name = response.meta.get('output_file_name')
        layer_link_name = response.meta.get('layer_link_name')

        # Write the data to the JSON file from previous query above (get the geometry and other field)
        with open(output_file_path, 'w') as json_file:
            json.dump(json.loads(response.text), json_file)

        # print('HERE IS THE RESULT: \n',json.loads(response.text))

        dict_response = json.loads(response.text)
        sample_first_row_geometry = dict_response.get('features',[{'geometry':None}])[0]['geometry'] # if the dict is not exist with feature, which means that it is equivalent to empty geometry

        fileSize = os.stat(output_file_path).st_size
        print (f"checking file size {output_file_path}, (error 500 or 400 indicator: if Filesize < 1kb): file size is --> {fileSize}")

        # with open(f'Z:\\GIS_ArcGISPro\\jupyter_notebook\\webgis_klhk\\arcgis_restapi_notebooks\\{layer_name}_input_id_query.json','r') as json_file:
        with open(f'{output_path}/json_raw/{layer_name}_input_id_query.json','r') as json_file:
            dict_oid_2 = json.load(json_file)

        if fileSize < 100 or sample_first_row_geometry is None :
            print(f're-do the chunk 50 with {output_file_path}')
            print('get the number suffix _(i+1): therefore use -1 to apply index')

            #  get the _somenumber of i.e layer_name_somenumber.json
            suffix_iter = output_file_name.split('_')[-1].replace('.json','')
            list_oids = dict_oid_2[layer_link_name]['chunk_oid'][int(suffix_iter)-1] # since index start from 0 but you added a+=1 at the top above in for loop

            if list_oids is not None:
                oid_name = dict_oid_2[layer_link_name]['objectIdFieldName']
                chunk_size = 50
                print("initiating multiplier chunk " + str(chunk_size))
                query_chunks = []
                oid_chunk = []
                for i in range(0, len(list_oids), chunk_size):
                    chunk = list_oids[i:i + chunk_size]
                    query = ' or '.join([f"{oid_name} = {str(oid)}" for oid in chunk])
                    query_chunks.append(query)
                    oid_chunk.append(chunk)
                dict_oid_2[layer_link_name]['query'] = query_chunks
                dict_oid_2[layer_link_name]['chunk_oid'] = oid_chunk

                print(len(oid_chunk)) # should return =< 2 now

                # with open(f'Z:\\GIS_ArcGISPro\\jupyter_notebook\\webgis_klhk\\arcgis_restapi_notebooks\\{layer_name}_input_id_query_2.json','w') as json_file:
                with open(f'{output_path}\\json_raw\\{layer_name}_input_id_query_2.json','w') as json_file:
                    json.dump(dict_oid_2, json_file) # this one important to save and track back again later if error happening in the files (file_small) not acquiring features

            elif list_oids is None:
                # print(list_oids)
                output_file_path = os.path.join(output_dir, f'failed_layers_{layer_name}_2.json')

                with open(output_file_path,'w') as json_file:
                    json.dump({'error_id_layer_2':layer_name}, json_file)

            if dict_oid_2[layer_link_name].get('query') is not None:
            #         a +=1
            #         print(a)
            #         print(key)
                    # fix_dict[key] = value
                    # Construct the output file path based on layer_name
                    
                a = 0
                for q in dict_oid_2[layer_link_name]['query']:
                    a += 1 # this one is producing interation batch download in file json
                    obj_ids_query = q
                    post_data  = { 'where': obj_ids_query,
                                'text': '',
                                'objectIds': '',
                                'time': '',
                                'timeRelation': 'esriTimeRelationOverlaps',
                                'geometry': '',
                                'geometryType': 'esriGeometryEnvelope',
                                'inSR': '',
                                'spatialRel': 'esriSpatialRelIntersects',
                                'distance': '',
                                'units': 'esriSRUnit_Foot',
                                'relationParam': '',
                                'outFields': '*',
                                'returnGeometry': 'true',
                                'returnTrueCurves': 'false',
                                'maxAllowableOffset': '',
                                'geometryPrecision': '',
                                'outSR': '',
                                'havingClause': '',
                                'returnIdsOnly': 'false',
                                'returnCountOnly': 'false',
                                'orderByFields': '',
                                'groupByFieldsForStatistics':  '',
                                'outStatistics': '',
                                'returnZ': 'false',
                                'returnM': 'false',
                                'gdbVersion': '',
                                'historicMoment': '',
                                'returnDistinctValues': 'false',
                                'resultOffset': '',
                                'resultRecordCount': '',
                                'returnExtentOnly': 'false',
                                'sqlFormat': 'none',
                                'datumTransformation': '',
                                'parameterValues': '',
                                'rangeValues': '',
                                'quantizationParameters': '',
                                'featureEncoding': 'esriDefault',
                                'f': 'geojson',
                            }
                    
                    output_file_path = os.path.join(output_dir, f'{layer_name}_n50_{suffix_iter}_{a}.json') # nested 500 means, the data use chunk 500 instead 1000

                    post_url = 'https://geoportal.menlhk.go.id' + layer_link_name + '/query'

                    request = scrapy.FormRequest(url=post_url, formdata=post_data, callback=self.save_json_2, meta={'output_file_path': output_file_path,
                                                                                                                'output_file_name':f'{layer_name}_n50_{suffix_iter}_{a}.json',
                                                                                                                'layer_name': layer_name})

                    yield request

        else:
            print(f'no error in file output feature {layer_name}')

    def save_json_2(self, response):
        
        output_file_path = response.meta.get('output_file_path')

        # Write the data to the JSON file
        with open(output_file_path, 'w') as json_file:
            json.dump(json.loads(response.text), json_file)
            



        
        
