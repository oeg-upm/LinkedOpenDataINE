# LinkedOpenDataINE
Este repositorio existe para subir los recursos semánticos generados para el proyecto LinkedOpenData, colaboración entre el Ontology Engineering Group y el Instituto Nacional de Estadística.

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
 pip install git+https://github.com/morph-kgc/morph-kgc.git

````   
4. Ejecutar el script linkedstats_generation con el usuario y contraseña de la base de datos, y la clasificacion como parámetros:
````
python3 linkedstats_generation.py "example_usr" "example_psw" "CNAE09"
````
#   Autor
- Diego Conde Herreros (OEG-UPM) - main contact  diego.conde.herreros at upm.es
