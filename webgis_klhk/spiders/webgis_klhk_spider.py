import scrapy
from urllib.parse import urlencode
import json


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
        
        page_url = 'https://geoportal.menlhk.go.id' + layer_name + '/query?' + urlencode(params)

        yield scrapy.Request(page_url, self.parse_query_get, meta={'layer_name':layer_name})

    def parse_query_get(self, response):
        layer_name = response.meta.get('layer_name')

        data = json.loads(response.text)


        yield {layer_name: data}
        
