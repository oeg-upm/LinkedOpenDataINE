from rdflib import Graph, URIRef, Literal, Namespace, BNode
from src.prefixes import *
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
    graph = Graph()

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

def run_morph_bigcube_batched(mapping_folder, output_dir, output_file, batch_size=5):
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

    # ---------------------------------------------------------
    # FASE 1: GENERACIÓN (Con Barra de Progreso)
    # ---------------------------------------------------------
    # tqdm envuelve nuestra lista de 'batches' y muestra la barra automáticamente
    for i in tqdm(batches, desc="Generatings RDFs", unit="lote"):
        
        batch = all_files[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        partial_output = os.path.join(temp_dir, f"temp_part_{batch_num}.nt")

        # Generar config
        _generate_config_for_batch(batch, partial_output)

        try:
            # Ejecutar Morph-KGC
            # stdout=DEVNULL es importante para que los logs de Morph no rompan la barra visual
            subprocess.run(
                [sys.executable, "-m", "morph_kgc", "config.ini"], 
                check=True,
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.PIPE
            )
            
            if os.path.exists(partial_output):
                generated_partial_files.append(partial_output)
            
        except subprocess.CalledProcessError as e:
            log_file = os.path.join(output_dir, f"error_log_batch_{batch_num}.txt")
            error_name = type(e).__name__ 
            tqdm.write(f"\n[!] Error in batch {batch_num}: {error_name} (see {log_file} for details)")

            # 2. Guardamos el log completo en el archivo
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"--- Error in Batch {batch_num} ---\n")
                f.write(e.stderr.decode())
                f.write("\n" + "="*40 + "\n")
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
