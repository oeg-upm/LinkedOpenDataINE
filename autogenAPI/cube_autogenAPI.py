from rdflib import Graph, URIRef, Literal, Namespace, BNode
import os
import sys
import argparse, warnings
import time
from datetime import datetime, timezone

from src.utils import convertNT2TTL, run_morph, run_morph_bigcube_batched, normalizeINE
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
        default="../rdf_vocabularies/inelod-voc-measure.ttl",
        help="Path to the measure ontology file."
    )
    # dimension ontology file
    parser.add_argument(
        "--dimension_ontology_file", 
        type=str,
        default="../rdf_vocabularies/inelod-voc-dimension.ttl",
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
            run_morph_bigcube_batched(paths["mapping_folder"] + "/", paths["output_folder"], paths["file_nt"], batch_size=1, measureOntologyFile=args.measure_ontology_file)
        else:
            run_morph(paths["mapping_file"], paths["file_nt"])
            normalizeINE(paths["file_nt"], args.measure_ontology_file)
            convertNT2TTL(paths["file_nt"], paths["file_ttl"])



if __name__ == "__main__":
    main()

#"https://servicios.ine.es/wstempus/jsCache/ES/DATOS_TABLA/50902?det=2&tip=M&nult=2"
#"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/66615?&tv=19:4581&det=2&tip=M"
#"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/CENSO10053173?nult=3&det=2&tip=M"
#"https://servicios.ine.es/wstempus/js/ES/DATOS_METADATAOPERACION/IPC?g1=115:16&g2=3:84&p=1&nult=5&tip=A"
#"https://servicios.ine.es/wstempus/jsCache/ES/DATOS_TABLA/50902?det=0&nult=10&tip=A"
#"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/66615?tip=A&nult=2"
#"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/HPT62619?nult=3tip=A"





