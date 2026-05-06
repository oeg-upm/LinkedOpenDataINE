from rdflib import Graph, URIRef, Literal, Namespace, BNode
from src.prefixes import *
from src.dimensions_measure import getMeasureFromTTL
import tempfile

def add_logical_sources(logical_sources_map, inputId, urlAPI, parameters, g_mappings):
    param_strings = [f"{k}{v}" for k, v in sorted(parameters.items())]
    params_combined = "_".join(param_strings)

    fuenteAPI = INELOD["FuenteAPI_" + inputId + "_" + params_combined]
    g_mappings.add((fuenteAPI, HTV["absoluteURI"], Literal(urlAPI)))

    for ls_suffix, iterator_value in logical_sources_map.items():
        ls_subject = INELOD[ls_suffix]
        g_mappings.add((ls_subject, RDF.type, RML.logicalSource))
        g_mappings.add((ls_subject, RML.source, fuenteAPI))
        g_mappings.add((ls_subject, RML.iterator, Literal(iterator_value)))
        g_mappings.add((ls_subject, RML.referenceFormulation, RML.HTTPAPI))

def add_pom_obj(triples_map, pred, obj, g_mappings, lang=None):
    pom_bnode = BNode()
    g_mappings.add((triples_map, RML.predicateObjectMap, pom_bnode))
    g_mappings.add((pom_bnode, RML.predicate, pred))
    if lang:
        g_mappings.add((pom_bnode, RML.object, Literal(obj, lang=lang)))
    else:
        g_mappings.add((pom_bnode, RML.object, obj if isinstance(obj, URIRef) else Literal(obj)))

def add_pom_obj_iri(triples_map, pred, obj_uri, g_mappings):
    pom_bnode = BNode()
    g_mappings.add((triples_map, RML.predicateObjectMap, pom_bnode))
    g_mappings.add((pom_bnode, RML.predicate, pred))
    object_map_bnode = BNode()
    g_mappings.add((pom_bnode, RML.objectMap, object_map_bnode))
    g_mappings.add((object_map_bnode, RML.template, Literal(obj_uri)))
    g_mappings.add((object_map_bnode, RML.termType, RML.IRI))

def add_pom_ref(triples_map, pred, ref, g_mappings, datatype=None):
    pom_bnode = BNode()
    g_mappings.add((triples_map, RML.predicateObjectMap, pom_bnode))
    g_mappings.add((pom_bnode, RML.predicate, pred))
    object_map_bnode = BNode()
    g_mappings.add((pom_bnode, RML.objectMap, object_map_bnode))
    g_mappings.add((object_map_bnode, RML.reference, Literal(ref)))
    if datatype:
        g_mappings.add((object_map_bnode, RML.datatype, datatype))

def add_pom_parenttpm(triples_map, pred, parent_triples_map, join_condition_child, join_condition_parent, g_mappings):
    pom_bnode = BNode()
    g_mappings.add((triples_map, RML.predicateObjectMap, pom_bnode))
    g_mappings.add((pom_bnode, RML.predicate, pred))
    object_map_bnode = BNode()
    g_mappings.add((pom_bnode, RML.objectMap, object_map_bnode))
    g_mappings.add((object_map_bnode, RML.parentTriplesMap, parent_triples_map))
    if join_condition_child and join_condition_parent:
        join_condition_bnode = BNode()
        g_mappings.add((object_map_bnode, RML.joinCondition, join_condition_bnode))
        g_mappings.add((join_condition_bnode, RML.child, Literal(join_condition_child)))
        g_mappings.add((join_condition_bnode, RML.parent, Literal(join_condition_parent)))

def add_subject_map(triples_map, class_uri, g_mappings, template=None, constant_uri=None):
    subject_map_bnode = BNode()
    g_mappings.add((triples_map, RML.subjectMap, subject_map_bnode))
    if constant_uri:
        g_mappings.add((subject_map_bnode, RML.constant, constant_uri))
    g_mappings.add((subject_map_bnode, RML["class"], class_uri))
    if template:
        g_mappings.add((subject_map_bnode, RML.template, Literal(template)))
    return subject_map_bnode

def add_subject_map_BN(triples_map, g_mappings):
    subject_map_bnode = BNode()
    g_mappings.add((triples_map, RML.subjectMap, subject_map_bnode))

    g_mappings.add((subject_map_bnode, RML.constant, BNode()))
    g_mappings.add((subject_map_bnode, RML["termType"], RML["BlankNode"]))


def convertNT2TTL(input_file, output_file):
    # Crear un grafo vacío
    graph = Graph(store="Oxigraph")    

    for prefix, namespace in namespaces.items():
        graph.bind(prefix, namespace)

    # Intentar cargar el archivo NT en el grafo
    try:
        graph.parse(input_file, format='nt')

        # Guardar el grafo en formato Turtle (con los prefijos ya registrados)
        graph.serialize(destination=output_file, format='turtle')
        print(f"Conversion completed: {input_file} to {output_file}")
    except Exception as e:
        print(f"Error processing files: {e}")

import sys
import subprocess
def _generate_config_file(mapping, output_file):
    """
    Genera el contenido para el archivo config.ini usando el argumento proporcionado.
    """
    config_content = f"""[CONFIGURATION]
output_file: {output_file}
output_format: N-TRIPLES
logging_level: INFO

[DataSource1]
mappings: {mapping}
"""
    # Escribir el contenido al archivo config.ini
    try:
        with open('config.ini', 'w') as f:
            f.write(config_content)
        print("'config.ini' file generated and updated successfully.")
    except IOError as e:
        print(f" Error writing to 'config.ini': {e}")
        sys.exit(1)



def run_morph(mapping, output_file):
    _generate_config_file(mapping, output_file)

    try:
        subprocess.run([sys.executable, "-m", "morph_kgc", "config.ini"])
    except subprocess.CalledProcessError as e:
        print(f"morph_kgc failed: {e}")
        sys.exit(1)


import os
import sys
import subprocess
import shutil
from tqdm import tqdm  # Importamos la librería de la barra de progreso

def _generate_config_for_batch(mapping_list, output_file):
    """
    Genera config.ini para el lote actual.
    """
    mappings_string = ",".join(mapping_list)
    config_content = f"""[CONFIGURATION]
output_file: {output_file}
output_format: N-TRIPLES
logging_level: INFO

[DataSource1]
mappings: {mappings_string}
"""
    with open('config.ini', 'w') as f:
        f.write(config_content)


from concurrent.futures import ThreadPoolExecutor
def run_morph_bigcube_batched(mapping_folder, output_dir, output_file, batch_size=5, measureOntologyFile=None):
    # 1. Obtener y preparar lista de archivos
    if not os.path.isdir(mapping_folder):
        print("Error: Folder does not exist.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    final_output_file = output_file

    # ---------------------------------------------

    all_files = sorted([
        os.path.join(mapping_folder, f) 
        for f in os.listdir(mapping_folder) 
        if os.path.isfile(os.path.join(mapping_folder, f))
    ])
    
    total_files = len(all_files)
    generated_partial_files = []
    
    print(f"--- Initialazing proccess: {total_files} total files ---")
    
    # Preparamos los índices para los lotes
    # range(0, total_files, batch_size) nos da los saltos: 0, 5, 10, 15...
    batches = list(range(0, total_files, batch_size))

    temp_dir = tempfile.gettempdir()

    # Creamos un pool de hilos. 
    # max_workers=None usará la cantidad de CPUs de tu máquina.
    with ThreadPoolExecutor() as executor:
        futures = []
        # ---------------------------------------------------------
        # FASE 1: GENERACIÓN + NORMALIZACIÓN PARALELA
        # ---------------------------------------------------------
        for i in tqdm(batches, desc="Processing Batches", unit="lote"):
            batch = all_files[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            partial_output = os.path.join(temp_dir, f"temp_part_{batch_num}.nt")

            _generate_config_for_batch(batch, partial_output)

            try:
                # Ejecutar Morph-KGC (Sincrónico: esperamos a que genere el RDF)
                subprocess.run(
                    [sys.executable, "-m", "morph_kgc", "config.ini"], 
                    check=True,
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.PIPE
                )
                
                if os.path.exists(partial_output):
                    generated_partial_files.append(partial_output)
                    
                    # --- LANZAR NORMALIZACIÓN EN PARALELO ---
                    # Esto no bloquea. El bucle sigue al siguiente lote de inmediato.
                    #tqdm.write(f" -> Batch {batch_num} generated. Normalizing in background...")
                    executor.submit(normalizeINE, partial_output, measureOntologyFile)

            except subprocess.CalledProcessError as e:
                log_file = os.path.join(output_dir, f"error_log_batch_{batch_num}.txt")
                error_name = type(e).__name__ 
                tqdm.write(f"\n[!] Error in batch {batch_num}: {error_name} (see {log_file} for details)")

                # 2. Guardamos el log completo en el archivo
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"--- Error in Batch {batch_num} ---\n")
                    f.write(e.stderr.decode())
                    f.write("\n" + "="*40 + "\n")

        # Importante: Antes de pasar a la Fusión, esperamos a que 
        # todos los hilos de normalización terminen.
        print("\n[*] Waiting for all background post-processing to finish...")
        # El bloque 'with ThreadPoolExecutor' esperará automáticamente aquí al cerrarse.
        
    # ---------------------------------------------------------
    # FASE 2: FUSIÓN (Con Barra de Progreso)
    # ---------------------------------------------------------
    if generated_partial_files:
        print("\nMerging local RDF files...")
        try:
            with open(final_output_file, 'wb') as outfile:
                for partial_file in tqdm(generated_partial_files, desc="Merging", unit="file"):                    
                    with open(partial_file, 'rb') as infile:
                        shutil.copyfileobj(infile, outfile, length=16*1024*1024)
                    
                    outfile.write(b"\n") 
                    
        except IOError as e:
            print(f"Error creating final output file: {e}")
            sys.exit(1)

        # ---------------------------------------------------------
        # FASE 3: LIMPIEZA
        # ---------------------------------------------------------
        print("Cleaning temporary files...")
        for partial_file in generated_partial_files:
            try:
                os.remove(partial_file)
            except OSError:
                pass
        
        if os.path.exists("config.ini"):
            os.remove("config.ini")
            
        print(f"--- Done! Generated file: {final_output_file} ---")
    else:
        print("Warning: No output file was generated.")

from rdflib import Graph, URIRef, RDF, Namespace
import warnings
import datetime
from datetime import timezone
def normalizeINE(datacube_path, measureOntologyFile):
    g = Graph(store="Oxigraph")    
    g.parse(datacube_path, format="nt")
    
    unique_measures = set(str(o) for o in g.objects(None, QB.measure))    
    for old_measure_label in unique_measures:
        new_predicate_uri = getMeasureFromTTL(old_measure_label, measureOntologyFile)
        if new_predicate_uri and new_predicate_uri != SDMX_MEASURE["obsValue"]:
            # 3. Consultas para colocar el predicado de measures donde es estandar por el RDF Data Cube
            old_uri = Literal(old_measure_label)

            new_uri = URIRef(new_predicate_uri)

            update_query = """
                DELETE { ?s qb:measure ?old }
                INSERT { ?s qb:measure ?new }
                WHERE  { ?s qb:measure ?old }
            """
            # Pass the variables via initBindings
            g.update(update_query, initBindings={'old': old_uri, 'new': new_uri}, initNs={'qb': QB})
    update_query = """
        INSERT {
            ?slicedsd qb:component [ 
                qb:measure ?measure ; 
                qb:order "1"^^xsd:int 
            ] .
        }
        WHERE {
            SELECT DISTINCT ?slicedsd ?measure
            WHERE {
                # Buscamos la relación, pero filtramos duplicados con el DISTINCT
                ?slice qb:measure ?measure ;
                    qb:sliceStructure ?sliceKey .
                ?slicedsd qb:sliceKey ?sliceKey .
            
            }
        }
    """      
    g.update(update_query, initNs={'qb': QB})
    update_query = """
        DELETE {
            ?slice qb:measure ?measure .
        }
        WHERE {
            ?slice qb:measure ?measure ;
                qb:sliceStructure ?sliceKey .
            ?slicedsd qb:sliceKey ?sliceKey .
        }
        """
    g.update(update_query, initNs={'qb': QB})
    # Conectar lod slices a dataset directamente
    update_query = """
        INSERT {
            ?dataset qb:slice ?slice .
        }
        WHERE {
            ?obs qb:dataSet ?dataset ;
                qb:slice ?slice .
        }
    """
    g.update(update_query, initNs={'qb': QB})

    # Subir el measure a nivel de DataStructureDefinition del dataset
    update_query = """
        INSERT {
            ?mainDSD qb:component [ qb:measure ?measure ] .
        }
        WHERE {
            {
                SELECT DISTINCT ?mainDSD ?measure
                WHERE {
                    ?dataset a qb:DataSet ;
                            qb:structure ?mainDSD ;
                            qb:slice ?slice .
                    ?slice qb:sliceStructure ?sliceKey .
                    ?sliceDSD qb:sliceKey ?sliceKey ;
                            qb:component ?sliceComponent .
                    ?sliceComponent qb:measure ?measure .
                }
            }
        }
    """
    g.update(update_query, initNs={'qb': QB})

    replace_obs_query = """
        PREFIX qb: <http://purl.org/linked-data/cube#>
        PREFIX sdmx-measure: <http://purl.org/linked-data/sdmx/2009/measure#>

        DELETE {
            ?obs sdmx-measure:obsValue ?val .
        }
        INSERT {
            ?obs ?specificMeasure ?val .
        }
        WHERE {
            # 1. Seleccionamos observaciones que tengan el valor genérico
            ?obs sdmx-measure:obsValue ?val .

            # 2. Navegamos hacia arriba para descubrir la medida real
            ?obs qb:slice ?slice .                   # La obs pertenece a un Slice
            ?slice qb:sliceStructure ?sliceKey .     # El Slice tiene una estructura (Key)
            
            # 3. Buscamos la DSD parcial que define esa Key (donde guardaste las measures)
            ?sliceDSD qb:sliceKey ?sliceKey ;
                    qb:component ?comp .
                    
            # 4. Extraemos la URI de la medida específica (ej. ine:rate, ine:index)
            ?comp qb:measure ?specificMeasure .
        }
        """

     # Ejecutar en tu grafo
    g.update(replace_obs_query)

    
    for s, p, o in g.triples((None, SDMX_DIMENSION.date, None)):
        if o.datatype == XSD.long:
            timestamp = int(o)
            dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            
            g.remove((s, p, o))
            g.add((s, p, Literal(dt.isoformat(), datatype=XSD.dateTime)))


    warnings.filterwarnings("ignore", message="NTSerializer always uses UTF-8 encoding")
    g.serialize(destination=datacube_path, format="nt")
    

    return g

