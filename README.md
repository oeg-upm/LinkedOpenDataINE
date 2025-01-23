# LinkedOpenDataINE
Este repositorio existe para subir los recursos semánticos generados para el proyecto LinkedOpenData, colaboración entre el Ontology Engineering Group y el Instituto Nacional de Estadística.

## Clasificaciones

Los pasos a seguir para generar estos datos en local son los siguientes:

0. Crear un entorno virtual (Recomendado).
1. Instalar Python.
2. Instalar SQL Alchemy, y oracledb
````
 python3 -m pip install sqlalchemy
 python3 -m pip install oracledb

````
3. Instalar la librería de Morph-KGC y sus dependencias para que funcione con bases de datos Oracle:
````
 pip install morph-kgc[oracle]

````   
4. Ejecutar el script linkedstats_generation con el usuario y contraseña de la base de datos, y la clasificacion como parámetros:
````
python3 linkedstats_generation.py "example_usr" "example_psw" "CNAE09"
````

## Cubos de datos

Para la generación correcta del cubo el fichero "variables_correspondece.txt" debe contener las variables que emplea ese cubo y su correspondecia con la medida o dimensión en RDF. Estas pueden ser reutilizadas de los [vocabularios definidos por SDMX](https://raw.githubusercontent.com/UKGovLD/publishing-statistical-data/master/specs/src/main/vocab/sdmx-dimension.ttl), o los [diseñados para este proyecto](inelod-voc.ttl).
Los pasos a seguir para la generación semiautomática de de los cubos de datos en RDF son los siguientes:

0. Crear un entorno virtual (Recomendado).
1. Instalar Python.
2. Ejecutar el script cube_semiauto_generation.py con la ruta del cubo a generar en formato csv. 
````
python .\cube_semiauto_generation.py ../datasets/capitulo_66615.csv

````  

#   Autor
- Diego Conde Herreros (OEG-UPM) - main contact  diego.conde.herreros at upm.es
