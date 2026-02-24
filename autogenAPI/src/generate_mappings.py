from src.prefixes import *
from src.datos_tabla import generate_DATOSTABLA_mappings, generate_DATOS_METADATAOPERACION_mappings
from src.datos_serie import generate_DATOSSERIE_mappings

import sys, time, os, requests
from jsonpath import JSONPath, search
from tqdm import tqdm

def generate_mapping(url, measure_ontology_file, dimension_ontology_file): 
    parsed_data = parse_ine_api_url(url)   
    inputId = parsed_data["inputId"]

    # Modificar la URL para asegurar que contenga det=2 y tip=M. Necesario para extraer la semantica bien
    url = _modify_ine_api_url(url)

    # Medir tiempo de ejecución
    start_time = time.time()
    match parsed_data["function_name"]:
        case "DATOS_TABLA":
            g_mappings = generate_DATOSTABLA_mappings(url, inputId, parsed_data["parameters"], measure_ontology_file, dimension_ontology_file)
        case "DATOS_SERIE":
            g_mappings = generate_DATOSSERIE_mappings(url, inputId, parsed_data["parameters"], measure_ontology_file, dimension_ontology_file)
        case "DATOS_METADATAOPERACION":
            #DATOS_METADATAOPERACION muestra la información igual que DATOS_TABLA
            g_mappings = generate_DATOS_METADATAOPERACION_mappings(url, inputId, parsed_data["parameters"], measure_ontology_file, dimension_ontology_file)
        case None:
            print("Error: No se pudo extraer la función de la URL proporcionada.")
            sys.exit(1) 
    end_time = time.time()
    elapsed_time = end_time - start_time

    return g_mappings, elapsed_time

def generate_mappings_big_cube(url, output_mappings_folder, measure_ontology_file, dimension_ontology_file):
    parsed_data = parse_ine_api_url(url)
    inputId = parsed_data["inputId"]
    param_strings = [f"{k}{v}" for k, v in sorted(parsed_data["parameters"].items())]

    grupos_tabla = requests.get(f"https://servicios.ine.es/wstempus/js/ES/GRUPOS_TABLA/{inputId}").json()

    grupos_tabla_ids = search("$.*.Id", grupos_tabla)
    filters = []

    for gp_id in grupos_tabla_ids:
        valores_grupostabla = requests.get(f"https://servicios.ine.es/wstempus/js/ES/VALORES_GRUPOSTABLA/{inputId}/{gp_id}?det=1").json()
        id_variable = search("$.*.Variable.Id", valores_grupostabla)[0]
        id_valores = search("$.*.Id", valores_grupostabla)
        filterr = [f"{id_variable}:{id_valores[i]}" for i in range(len(id_valores))]
        filters.append(filterr)

    selected_filter_values = filters[_select_filter(filters, inputId)]
    
    base_mapping, elapsed_time = generate_mapping(
            url=url, 
            measure_ontology_file=measure_ontology_file,
            dimension_ontology_file=dimension_ontology_file
    )

    url = _modify_ine_api_url(url) #incluir det=2 y tip=M
    for tv in selected_filter_values:
        # Si la url no tiene parametros, se añade '?tv=...'
        if '?' not in url:
            new_url = url + f"?tv={tv}"
        else:   
            new_url = url + f"&tv={tv}"
        output_mapping_file = os.path.join(
            output_mappings_folder, 
            f"{inputId}_{'_'.join(param_strings)}_tv{tv.replace(':','-')}_mappings.rml.ttl"
        )
        fuente_api_uri = INELOD["FuenteAPI_" + inputId + "_".join(param_strings) + f"_tv{tv.replace(':','-')}"]
        for s, p, o in base_mapping.triples((None, HTV["absoluteURI"], None)):
            base_mapping.remove((s, p, o))
            base_mapping.add((fuente_api_uri, p, Literal(new_url)))
        for s, p, o in base_mapping.triples((None, RML["source"], None)):
            base_mapping.remove((s, p, o))
            base_mapping.add((s, p, fuente_api_uri))

        base_mapping.serialize(output_mapping_file, format="turtle")

    return 0

def _test_restriccion_volumen(inputId, filter):
    url = f"https://servicios.ine.es/wstempus/jsCache/ES/DATOS_TABLA/{inputId}?nult=1&tv={filter}"
    try:
        r = requests.get(url).json()
    except Exception as e:
        return True
    return True if "status" in r else False

def _select_filter(filters, inputId):
    # Seleccion naive del orden de los filtros a usar, de menor a mayor cantidad de valores.
    filter_lengths = [len(f) for f in filters]
    sorted_indices = sorted(range(len(filter_lengths)), key=lambda k: filter_lengths[k], reverse=True)

    # list of 1/0 indicating if the filter is still valid
    valid_filters = [1 for _ in filters]

    print("Selecting filter to avoid volume restrictions...")

    for fi in tqdm(sorted_indices, desc="Searching valid filters", unit="index"):
        total_filtros = len(filters[fi])
        f = 0    
        with tqdm(total=total_filtros, desc=f" -> Index {fi}", leave=False) as pbar:
            while valid_filters[fi] and f < total_filtros:
                if _test_restriccion_volumen(inputId, filters[fi][f]):
                    valid_filters[fi] = 0
                
                f += 1
                pbar.update(1) # Actualizamos la barra manualmente en cada paso
        if valid_filters[fi]:
            return fi
    raise Exception("No valid filter found.")

from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
def parse_ine_api_url(url: str) -> dict:
    """
    Parsea una URL de la API del INE (Servicios Tempus) para extraer
    el nombre de la función, el ID de la tabla y los parámetros de la query.

    Args:
        url: La cadena de la URL a parsear.

    Returns:
        Un diccionario con 'function_name', 'table_id' y 'parameters'.
    """
    # 1. Parsear la URL en sus componentes
    parsed_url = urlparse(url)
    
    # 2. Extraer los segmentos de la ruta
    # La ruta es '/wstempus/jsCache/ES/DATOS_TABLA/50902'
    path_segments = parsed_url.path.strip('/').split('/')
    
    # El nombre de la función y el table_id están al final de la ruta
    # Ejemplo: ['wstempus', 'jsCache', 'ES', 'DATOS_TABLA', '50902']
    function_name = None
    inputId = None
    
    if len(path_segments) >= 2:
        # Se asume que los dos últimos segmentos son FUNCTION y TABLE_ID
        function_name = path_segments[-2]
        inputId = path_segments[-1]
    
    # 3. Extraer los parámetros de la query
    # La query es 'det=2&tip=M&nult=2'
    query_params = parse_qs(parsed_url.query)
    
    # Opcional: convertir las listas de parse_qs a valores únicos si es posible
    # (parse_qs devuelve listas porque una clave puede tener múltiples valores)
    simplified_params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}

    if 'tip' not in simplified_params:
        simplified_params['tip'] = ""
        
    # Si 'det' no está en el diccionario, se añade con el valor por defecto "0"
    if 'det' not in simplified_params:
        simplified_params['det'] = "0"
    
    # 4. Construir el resultado
    result = {
        "function_name": function_name,
        "inputId": inputId,
        "parameters": simplified_params
    }
    
    return result

def _modify_ine_api_url(url: str) -> str:
    """
    Modifica una URL de la API del INE para asegurar la inclusión de ciertos 
    parámetros de query: 'det' siempre será '2', y 'tip' será 'M' .
    
    Args:
        url: La cadena de la URL a modificar.

    Returns:
        La URL modificada como una cadena.
    """
    
    # 1. Descomponer la URL en sus partes (esquema, netloc, ruta, etc.)
    parsed_url = urlparse(url)
    
    # 2. Descomponer la cadena de query en un diccionario
    # parse_qs devuelve listas de valores, lo cual es correcto para reconstruir
    query_params = parse_qs(parsed_url.query)
    
    # --- Lógica de Modificación de Parámetros ---
    
    # 3. Forzar det=2
    query_params['det'] = ['2']
    
        
    query_params['tip'] = ['M']
    
    # --- Reconstrucción de la URL ---

    # 5. Codificar el diccionario de parámetros modificado de nuevo a una cadena de query
    # El `doseq=True` es importante para manejar listas de valores, aunque en este caso
    # las hemos asegurado a listas de un solo elemento (ej: {'det': ['2']}).
    new_query = urlencode(query_params, doseq=True)
    
    # 6. Reconstruir la URL completa
    # Se crea un objeto ParseResult con la query modificada
    modified_parsed_url = parsed_url._replace(query=new_query)
    
    # 7. Convertir el objeto ParseResult de nuevo a una cadena de URL
    return urlunparse(modified_parsed_url)
    