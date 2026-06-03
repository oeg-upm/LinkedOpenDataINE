# LinkedOpenDataINE
Este repositorio existe para subir los recursos semánticos generados para el proyecto LinkedOpenData, colaboración entre el Ontology Engineering Group y el Instituto Nacional de Estadística. Estas instrucciones parten de que el usuario tiene acceso a la VPN, y la base de datos del INE. Para ejecutar el fichero "classifications_generation.py" se debe estar conectado a la VPN, y los parámetros "example_usr", y "example_psw" son el usuario y contraseña para acceder a la base de datos. 

Los pasos a seguir para generar estos datos en local son los siguientes:

0. Crear un entorno virtual (Recomendado).
1. Instalar Python.
2. Instalar la librería de Morph-KGC y sus dependencias para que funcione con bases de datos Oracle:
````
 pip install morph-kgc[oracle]
````   
3. Ejecutar el script linkedstats_generation con el usuario y contraseña de la base de datos, y la clasificacion como parámetros:
````
python3 classifications_generation.py "example_usr" "example_psw" "CNAE09"
````

## Cubos de datos

Para la generación correcta del cubo la ontología inelod-voc.ttl debe contener las dimensiones, medidas y conjuntos de medidas que utiliza ese cubo en RDF. Estas pueden ser reutilizadas de los [vocabularios definidos por SDMX](https://raw.githubusercontent.com/UKGovLD/publishing-statistical-data/master/specs/src/main/vocab/sdmx-dimension.ttl), o los [diseñados para este proyecto](inelod-voc.ttl).
Los pasos a seguir para la generación semiautomática de de los cubos de datos en RDF son los siguientes:

0. Crear un entorno virtual (Recomendado).
1. Instalar Python.
2. Ejecutar el script cube_autogen.py con la ruta del cubo a generar en formato csv. Si se desea especificar la medida que se está empleando en esta tabla se incluye el parámetro "--Medida".
````
python .\cube_autogen.py ../datasets/capitulo_66615.csv  --Medida "Personas"

````  

## INE API (AutoGenAPI)
El script `autogenAPI/cube_autogenAPI` genera mappings y cubos de datos a partir de la API del INE. Los argumentos son los siguientes:

| Argumento | Alias | Por defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `INE_API_URL` | - | Requerido | URL de la API del INE para la obtención de datos. |
| `--output_mappings_folder` | - | `mappings/` | Carpeta de destino para los mapeos generados. |
| `--output_folder` | - | `output/` | Carpeta de destino para el cubo de datos final. |
| `--measure_ontology_file` | - | `../rdf_vocabularies/inelod-voc-measure.ttl` | Ruta al archivo de ontología de medidas. |
| `--dimension_ontology_file` | - | `../rdf_vocabularies/inelod-voc-dimension.ttl` | Ruta al archivo de ontología de dimensiones. |
| `--bigcube` | `-b` | False | Flag para habilitar la generación de cubos grandes desde DATOS_TABLA. |
| `--materialize` | `-m` | False | Flag para materializar datos tras los mapeos (no compatible con --bigcube). |

Un ejemplo de uso es el siguiente:
`python autogenAPI/cube_autogenAPI.py --output_mappings_folder . --output_folder . --measure_ontology_file rdf_vocabularies/inelod-voc-measure.ttl --dimension_ontology_file rdf_vocabularies/inelod-voc-dimension.ttl -m "https://servicios.ine.es/wstempus/jsCache/ES/DATOS_TABLA/50954?tip=A nult=2"`
Se generara la carpeta en `/autogenAPI/50954` que contendrá tanto el mapping como la materialización en N-Triples y Turtle.


#   Autor
- Diego Conde Herreros (OEG-UPM) - main contact  diego.conde.herreros at upm.es
- Isaac Noya Vázquez (OEG-UPM) - main contact  isaac.noya at upm.es (AutoGenAPI)
