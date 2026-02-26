import requests
from jsonpath import JSONPath, search
from rdflib import Graph
from src.prefixes import INE, SDMX_MEASURE

def getOperationsDimensions(operacion, ontologyDimensionsFile):
    variables_operacion = requests.get(f"https://servicios.ine.es/wstempus/jsCache/ES/VARIABLES_OPERACION/{operacion}?").json()

    dimension_ids = search("$.*.(Nombre,Id)", variables_operacion)

    dimensions = Graph().parse(ontologyDimensionsFile, format="turtle")
    results = {}

    for dim in dimension_ids:
        ask_dim = f' PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>' \
              f' ASK {{ ?s rdfs:label "{dim['Nombre']}"@es .}}'
        res_dim = dimensions.query(ask_dim)
        if res_dim.askAnswer:
            select_query = f' PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>' \
                          f' SELECT ?s WHERE {{ ?s rdfs:label "{dim['Nombre']}"@es .}}'
            res_select = dimensions.query(select_query)
            for row in res_select:
                dimensions_uri = row.s
            results[dimensions_uri] = dim['Id']
        else:
            results[INE.unknownDimension] = dim['Id']
    return results



def getTableDimensions(tableId, ontologyDimensionsFile):
    # Usar API para Hacer consulta a SERIES_TABLA para obtener una serie
    series_tabla = requests.get(f"https://servicios.ine.es/wstempus/jsCache/ES/SERIES_TABLA/{tableId}?").json()

    # Caso de cubos muy grandes (SERIES_TABLA no devuelve los datos, entonces hay que usar GRUPOS_TABLA y VALORES_GRUPOSTABLA)
    grupos_tabla = requests.get(f"https://servicios.ine.es/wstempus/jsCache/ES/GRUPOS_TABLA/{tableId}?").json()
    #grupos_ids = JSONPath("$.*.Id").parse(grupos_tabla)
    grupos_ids = search("$.*.Id", grupos_tabla)
    dimension_ids = []
    for grupo_id in grupos_ids:
        valor_grupostabla = requests.get(f"https://servicios.ine.es/wstempus/jsCache/ES/VALORES_GRUPOSTABLA/{tableId}/{grupo_id}?det=1").json()
        #dim_id = JSONPath("$.*.Variable.(Nombre,Id)").parse(valor_grupostabla)
        dim_id = search("$.*.Variable.(Nombre,Id)", valor_grupostabla)
        for dim_idx in dim_id:
            dimension_ids.append(dim_idx)
            
    #Eliminar duplicados
    dimension_ids = [dict(t) for t in {tuple(d.items()) for d in dimension_ids}]
    dimensions = Graph().parse(ontologyDimensionsFile, format="turtle")
    results = {}

    for dim in dimension_ids:
        ask_dim = f' PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>' \
              f' ASK {{ ?s rdfs:label "{dim['Nombre']}"@es .}}'
        res_dim = dimensions.query(ask_dim)
        if res_dim.askAnswer:
            select_query = f' PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>' \
                          f' SELECT ?s WHERE {{ ?s rdfs:label "{dim['Nombre']}"@es .}}'
            res_select = dimensions.query(select_query)
            for row in res_select:
                dimensions_uri = row.s
            results[dimensions_uri] = dim['Id']
        else:
            results[INE.unknownDimension] = dim['Id']
    return results

def getSeriesDimensions(cod, ontologyDimensionsFile):
    valores_serie = requests.get(f"https://servicios.ine.es/wstempus/jsCache/ES/VALORES_SERIE/{cod}?det=1").json()
    dimension_ids = JSONPath("$.*.Variable.(Nombre,Id)").parse(valores_serie)
    

    dimensions = Graph().parse(ontologyDimensionsFile, format="turtle")
    results = {}

    for dim in dimension_ids:
        ask_dim = f' PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>' \
              f' ASK {{ ?s rdfs:label "{dim['Nombre']}"@es .}}'
        res_dim = dimensions.query(ask_dim)
        if res_dim.askAnswer:
            select_query = f' PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>' \
                          f' SELECT ?s WHERE {{ ?s rdfs:label "{dim['Nombre']}"@es .}}'
            res_select = dimensions.query(select_query)
            for row in res_select:
                dimensions_uri = row.s
            #results[dimensions_uri] = JSONPath(f"$[?(@.Variable.Id=={dim['Id']})].Nombre").parse(valores_serie)
            results[dimensions_uri] = search(f"$[?(@.Variable.Id=={dim['Id']})].Nombre", valores_serie)[0]
        else:
            #results[INE.unknownDimension] = JSONPath(f"$[?(@.Variable.Id=={dim['Id']})].Nombre").parse(valores_serie)
            results[INE.unknownDimension] = search(f"$[?(@.Variable.Id=={dim['Id']})].Nombre", valores_serie)[0]
    
    return results

def getMeausure(cod, meausureOntologyFile):
    serie = requests.get(f"https://servicios.ine.es/wstempus/jsCache/ES/SERIE/{cod}?det=1").json()
    label = JSONPath("$.Unidad.Nombre").parse(serie)[0]

    return getMeasureFromTTL(label, meausureOntologyFile)
    
def getMeasureFromTTL(label, meausureOntologyFile):
    measures = Graph().parse(meausureOntologyFile, format="turtle")

    ask_measure = f'''
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX qb: <http://purl.org/linked-data/cube#>
        PREFIX ine: <https://stats.linkeddata.es/voc/cubes/vocabulary#> 

        ASK {{
            {{ ?s a qb:MeasureProperty ; rdfs:label "{label}"@es . }}
            UNION
            {{ ?s a ine:MeasureSet ; rdfs:label "{label}"@es . }}
        }}
    '''
    res_measure = measures.query(ask_measure)

    if res_measure.askAnswer:
        select_query = f' PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>' \
                               f' SELECT ?s WHERE {{ ?s rdfs:label "{label}"@es .}}'
        res_select = measures.query(select_query)
        for row in res_select:
            measure_uri = row.s
        return measure_uri
    else:
        return SDMX_MEASURE.obsValue
