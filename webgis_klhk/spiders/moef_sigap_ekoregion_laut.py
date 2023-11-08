import scrapy
from urllib.parse import urlencode
import json
import os

from webgis_klhk.items import moefSigapKLHKItem

link_name = "/server/rest/services/SIGAP_Interaktif/Ekoregion_Darat_dan_Laut/MapServer/1"

class moefSigapKLHKRegDarat(scrapy.Spider):
    name = "moef_sigap_ekoregion_laut"
    allowed_domains = ["geoportal.menlhk.go.id"]
    
    start_urls = [f"https://geoportal.menlhk.go.id{link_name}"]

    def parse(self, response):
        # get xpath name objectid_name for queries
        objectid_name = response.xpath('/html/body/div/ul[4]/li[1]/text()').get().strip().replace('\r\n', '')
        # print(f'Title: {objectid_name}')
        #layer_name = response.meta.get('layer_name')
        layer_link_name = link_name
        #layer_link_name = "/server/rest/services/SIGAP_Interaktif/NSDH_Kawasan_Hutan/MapServer/0"
        # yield {layer_name: objectid_name}
        page_url = 'https://geoportal.menlhk.go.id' + layer_link_name + '/query'
        
        yield scrapy.Request(page_url, callback = self.parse_query, meta={'oid_name' :objectid_name, 'layer_link_name': layer_link_name })

    def parse_query(self, response):
        oid_name = response.meta.get('oid_name')
        layer_link_name = response.meta.get('layer_link_name')

        with open('./input_json/bbox_indo.json', 'r') as json_file:
        # with open('./input_json/bbox.json', 'r') as json_file:
            dict_data = json.load(json_file)

        str_bbox = str(dict_data)

        params = {
                "where": f"{oid_name} >= -1",
                "text": "",
                "objectIds": "",
                "time": "",
                "timeRelation": "esriTimeRelationOverlaps",
                #"geometry": str_bbox,
                "geometry": '', # this one, we will scrape all the data
                "geometryType": "esriGeometryEnvelope",
                #"inSR": 4326, 
                'inSR': '', # no need to apply this, return '' to scrape without geometry
                "spatialRel": "esriSpatialRelIntersects",
                "units": "esriSRUnit_Foot",
                "outFields": "",
                "returnGeometry": "false",
                "returnTrueCurves": "false",
                "maxAllowableOffset": "",
                "geometryPrecision": "",
                #"outSR": 4326,
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
        layer_name_parts = layer_link_name.split('/')
        layer_name = layer_name_parts[-3]

        output_dir = f'./output_json_{layer_name}_laut'  # Define your output directory
        os.makedirs(output_dir, exist_ok=True)

        data = json.loads(response.text)
        object_ids = data.get('objectIds', [])

        list_json = []

        for object_id in object_ids:
            print(f'performing request for id: {object_id}')
            yield scrapy.Request(
                url=f'https://geoportal.menlhk.go.id{layer_link_name}/{object_id}?f=pjson',
                callback=self.send_item, meta= {'output_dir': output_dir,
                                                'layer_name': layer_name}
            )

    def send_item(self, response):
        output_dir = response.meta.get('output_dir')
        layer_name = response.meta.get('layer_name')
        data_json = json.loads(response.text)

        item = moefSigapKLHKItem()
        
        item['data'] = data_json
        item['output_dir'] = output_dir
        item['layer_name'] = layer_name
        print(f'sending to item : {item["output_dir"]}')
        print(f'sending to item : {item["layer_name"]}')

        yield item
