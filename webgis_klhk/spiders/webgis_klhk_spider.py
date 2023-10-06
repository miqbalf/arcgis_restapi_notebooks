import scrapy
from urllib.parse import urlencode
import json
import os


class WebgisKlhkSpiderSpider(scrapy.Spider):
    name = "webgis_klhk_spider"
    allowed_domains = ["geoportal.menlhk.go.id"]
    start_urls = ["https://geoportal.menlhk.go.id/server/rest/services/Time_Series"]

    def parse(self, response):
        layer_links = response.css('li')
        for link in layer_links:
            
            layer = link.css('a::attr(href)').extract()[0]
            page_url = 'https://geoportal.menlhk.go.id' + layer
            yield scrapy.Request(page_url, callback=self.parse_individual_layer)

    
    def parse_individual_layer(self, response):
        # Process the data from the individual link here
        # You can use response.xpath or response.css to extract data
        # For example:
        layer_link_name = response.css('ul li a::attr(href)').extract()[0]

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
        with open('./input_json/bbox.json', 'r') as json_file:
            dict_data = json.load(json_file)

        str_bbox = str(dict_data)

        params = {
                "where": f"{oid_name} >= -1",
                "text": "",
                "objectIds": "",
                "time": "",
                "timeRelation": "esriTimeRelationOverlaps",
                "geometry": str_bbox,
                "geometryType": "esriGeometryEnvelope",
                "inSR": 4326,
                "spatialRel": "esriSpatialRelIntersects",
                "units": "esriSRUnit_Foot",
                "outFields": "*",
                "returnGeometry": "false",
                "returnTrueCurves": "false",
                "maxAllowableOffset": "",
                "geometryPrecision": "",
                "outSR": 4326,
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
        output_dir = './output_json'  # Define your output directory
        os.makedirs(output_dir, exist_ok=True)

        layer_link_name = response.meta.get('layer_link_name')

        layer_name_parts = layer_link_name.split('/')
        layer_name = layer_name_parts[-3]

        data = json.loads(response.text)

        dict_oid = {layer_name: data}
        # print(dict_oid)
                
        for key, value in dict_oid.items():
            list_oids = dict_oid[key]['objectIds']
            if list_oids is not None:
                oid_name = dict_oid[key]['objectIdFieldName']
                chunk_size = 1000
                query_chunks = []
                for i in range(0, len(list_oids), chunk_size):
                    chunk = list_oids[i:i + chunk_size]
                    query = ' or '.join([f"{oid_name} = {str(oid)}" for oid in chunk])
                    query_chunks.append(query)
                dict_oid[key]['query'] = query_chunks
                
        # fix_dict = {}
        for key, value in dict_oid.items():
            if dict_oid[key].get('query') is not None:
        #         a +=1
        #         print(a)
        #         print(key)
                # fix_dict[key] = value
                 # Construct the output file path based on layer_name
                
                a = 0
                for q in dict_oid[key]['query']:
                    a += 1
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
                    
                    output_file_path = os.path.join(output_dir, f'{layer_name}_{a}.json')

                    post_url = 'https://geoportal.menlhk.go.id' + layer_link_name + '/query'

                    request = scrapy.FormRequest(url=post_url, formdata=post_data, callback=self.save_json, meta={'output_file_path': output_file_path})

                    yield request

    def save_json(self, response):
        output_file_path = response.meta.get('output_file_path')

        # Write the data to the JSON file
        with open(output_file_path, 'w') as json_file:
            json.dump(json.loads(response.text), json_file)
        
