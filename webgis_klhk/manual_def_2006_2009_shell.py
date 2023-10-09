a = 0
for q in query_example['query']:
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
    
    output_file_path = os.path.join('./output_json', f'DEF_2006_2009_{a}.json')

    post_url = "https://geoportal.menlhk.go.id/server/rest/services/Time_Series/DEF_2006_2009/MapServer/0" +'/query'

    request = scrapy.FormRequest(url=post_url, formdata=post_data)

    fetch(request)

    with open(output_file_path, 'w') as json_file:
        json.dump(json.loads(response.text), json_file)