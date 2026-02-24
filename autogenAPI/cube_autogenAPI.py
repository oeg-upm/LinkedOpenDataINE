from rdflib import Graph, URIRef, Literal, Namespace, BNode
import os
import sys
import argparse, warnings
import time

from src.utils import convertNT2TTL, run_morph, run_morph_bigcube_batched
from src.prefixes import *
from src.generate_mappings import generate_mapping, generate_mappings_big_cube, parse_ine_api_url
from src.dimensions_measure import getMeasureFromTTL


def generate_api_paths(url, base_dir, mappings_folder_name, output_folder_name, bigcube):
    """
    Parsea la URL, crea las carpetas necesarias y devuelve las rutas de los archivos.
    """
    # 1. Procesamiento de datos iniciales
    parsed_data = parse_ine_api_url(url)
    # Ordenamos parámetros para que el nombre del archivo sea consistente
    param_strings = [f"{k}{v}" for k, v in sorted(parsed_data["parameters"].items())]
    params_combined = "_".join(param_strings)
    input_id = parsed_data["inputId"]

    # 2. Generar rutas de carpetas
    output_mapping_folder = os.path.join(base_dir, mappings_folder_name, input_id)
    output_folder = os.path.join(base_dir, output_folder_name, input_id, "".join(param_strings))

    if bigcube:
        output_mapping_folder = os.path.join(
            output_mapping_folder, 
            f"{input_id}_{'_'.join(param_strings)}_big_cube"
        )
    # 3. Crear carpetas si no existen
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(output_mapping_folder, exist_ok=True)

    # 4. Generar rutas de archivos finales
    # Usamos f-strings para que sea más fácil de leer que concatenar con +
    output_mapping_file = os.path.join(
        output_mapping_folder, 
        f"{input_id}_{params_combined}_mappings.rml.ttl"
    )
    
    if bigcube:
        output_file_nt = os.path.join(output_folder, f"{input_id}_{params_combined}_big_cube.nt")
        output_file_ttl = os.path.join(output_folder, f"{input_id}_{params_combined}_big_cube.ttl")
    else:
        output_file_nt = os.path.join(output_folder, f"{input_id}_{params_combined}.nt")
        output_file_ttl = os.path.join(output_folder, f"{input_id}_{params_combined}.ttl")

    return {
        "mapping_file": output_mapping_file,
        "file_nt": output_file_nt,
        "file_ttl": output_file_ttl,
        "mapping_folder": output_mapping_folder,
        "output_folder": output_folder
    }


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    parser = argparse.ArgumentParser(
        description="Data cube generator based on the INE API.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "INE_API_URL", 
        type=str, 
        help="The INE API URL to retrieve data for the cube."
    )
    parser.add_argument(
        "--output_mappings_folder", 
        type=str,
        default="mappings/", 
        help="Folder to save the output mappings. Optional."
    )
    parser.add_argument(
        "--output_folder", 
        type=str,
        default="output/",
        help="Output folder where the generated cube will be saved. Optional."
    )
    # measure ontology file
    parser.add_argument(
        "--measure_ontology_file", 
        type=str,
        default="autogen/rdf_vocabularies/inelod-voc-measure.ttl",
        help="Path to the measure ontology file."
    )
    # dimension ontology file
    parser.add_argument(
        "--dimension_ontology_file", 
        type=str,
        default="autogen/rdf_vocabularies/inelod-voc-dimension.ttl",
        help="Path to the dimension ontology file."
    )
    parser.add_argument(
        "-b", 
        "--bigcube", 
        action="store_true",
        help="Flag to indicate that a big cube could be generated. Only from DATOS_TABLA."
    )
    parser.add_argument(
        "-m", 
        "--materialize", 
        default=False,
        action="store_true",
        help="Flag to materialize the data after generating the mappings. Not used if --bigcube is set."
    )
    args = parser.parse_args()

    if args.bigcube and "DATOS_TABLA" not in args.INE_API_URL:
        print("Error: The --bigcube option is only available for DATOS_TABLA endpoints.")
        sys.exit(0)

    paths = generate_api_paths(
        args.INE_API_URL, 
        BASE_DIR, 
        args.output_mappings_folder, 
        args.output_folder,
        args.bigcube
    )

    if args.bigcube:
        print("Generating big cube mappings...")
        start_time = time.time()
        generate_mappings_big_cube(
            url=args.INE_API_URL,
            output_mappings_folder=paths["mapping_folder"],
            measure_ontology_file=args.measure_ontology_file,
            dimension_ontology_file=args.dimension_ontology_file
        )
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Big cube mappings  {args.INE_API_URL} generated in {elapsed_time:.3f} seconds.")
    else: 
        print("Generating mappings...")
        mappings, elapsed_time = generate_mapping(
            url=args.INE_API_URL, 
            measure_ontology_file=args.measure_ontology_file,
            dimension_ontology_file=args.dimension_ontology_file
        )
        mappings.serialize(paths["mapping_file"], format="turtle")
        print(f"Mappings {args.INE_API_URL} generated in {elapsed_time:.3f} seconds.")

    if args.materialize:
        print("Materializing data...")
        if args.bigcube:
            run_morph_bigcube_batched(paths["mapping_folder"] + "/", paths["output_folder"], paths["file_nt"], batch_size=1)
        else:
            run_morph(paths["mapping_file"], paths["file_nt"])

        if not args.bigcube:
            normalizeINE(paths["file_nt"], args.measure_ontology_file)
            convertNT2TTL(paths["file_nt"], paths["file_ttl"])


from rdflib import Graph, URIRef, RDF, Namespace
def normalizeINE(datacube_path, measureOntologyFile):
    g = Graph()
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
                
                # Opcional: Verificar que no exista ya para no duplicar si lanzas la query 2 veces
                FILTER NOT EXISTS { 
                    ?slicedsd qb:component [ qb:measure ?measure ] 
                }
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
            ?obs qb:Dataset ?dataset ;
                qb:slice ?slice .
        }
    """
    g.update(update_query, initNs={'qb': QB})

    # Subir el measure a nivel de DataStructureDefinition del dataset
    # TO-DO
    update_query = """
        INSERT {
            ?mainDSD qb:component [ qb:measure ?measure ] .
        }
        WHERE {
            {
                SELECT DISTINCT ?mainDSD ?measure
                WHERE {
                    ?dataset a qb:Dataset ;
                            qb:structure ?mainDSD ;
                            qb:slice ?slice .
                    ?slice qb:sliceStructure ?sliceKey .
                    ?sliceDSD qb:sliceKey ?sliceKey ;
                            qb:component ?sliceComponent .
                    ?sliceComponent qb:measure ?measure .
                    FILTER NOT EXISTS {
                        ?mainDSD qb:component ?existingComp .
                        ?existingComp qb:measure ?measure .
                    }
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

    warnings.filterwarnings("ignore", message="NTSerializer always uses UTF-8 encoding")
    g.serialize(destination=datacube_path, format="nt")
    
    return g

if __name__ == "__main__":
    main()

#"https://servicios.ine.es/wstempus/jsCache/ES/DATOS_TABLA/50954?det=2&tip=M&nult=2"
#"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/66615?&tv=19:4581&det=2&tip=M"
#"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/CENSO10053173?nult=3&det=2&tip=M"
#"https://servicios.ine.es/wstempus/js/ES/DATOS_METADATAOPERACION/IPC?g1=115:16&g2=3:84&p=1&nult=5&tip=A"
#"https://servicios.ine.es/wstempus/jsCache/ES/DATOS_TABLA/50902?det=0&nult=10&tip=A"
#"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/66615?tip=A&nult=2"
#"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/HPT62619?nult=3tip=A"





