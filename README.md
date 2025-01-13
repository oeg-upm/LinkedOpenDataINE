# LinkedOpenDataINE
Este repositorio existe para subir los recursos semánticos generados para el proyecto LinkedOpenData, colaboración entre el Ontology Engineering Group y el Instituto Nacional de Estadística. Estas instrucciones parten de que el usuario tiene acceso a la VPN, y la base de datos del INE. Para ejecutar el fichero "linkedstats_generation.py" se debe estar conectado a la VPN, y los parámetros "example_usr", y "example_psw" son el usuario y contraseña para acceder a la base de datos. 

Los pasos a seguir para generar estos datos en local son los siguientes:

0. Crear un entorno virtual (Recomendado).
1. Instalar Python.
2. Instalar la librería de Morph-KGC y sus dependencias para que funcione con bases de datos Oracle:
````
 pip install morph-kgc[oracle]
````   
3. Ejecutar el script linkedstats_generation con el usuario y contraseña de la base de datos, y la clasificacion como parámetros:
````
python3 linkedstats_generation.py "example_usr" "example_psw" "CNAE09"
````
#   Autor
- Diego Conde Herreros (OEG-UPM) - main contact  diego.conde.herreros at upm.es
