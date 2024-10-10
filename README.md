# LinkedOpenDataINE
Este repositorio existe para subir los recursos semánticos generados para el proyecto LinkedOpenData, colaboración entre el Ontology Engineering Group y el Instituto Nacional de Estadística.

Los pasos a seguir para generar estos datos en local son los siguientes:

0. Crear un entorno virtual (Recomendado).
1. Tener en el equipo instalado Python 3.10.9 y su versión correspondiente de pip (la herramienta no funciona con versiones posteriores de python).
2. Descargar el [Oracle Client](https://www.oracle.com/database/technologies/instant-client/downloads.html) la última versión en forma de ZIP.
3. Descomprime el ZIP del cliente de Oracle.
4. Para el funcionamiento del cliente de Oracle se requiere que esté instalada una redistribución de Visual Studio para Windows.       
5. Instalar la librería de Morph-KGC y sus dependencias para que funcione con bases de datos Oracle:
````
 python3 -m pip install morph-kgc[all]

````   
6. Ejecutar el script linkedstats_generation con el usuario y contraseña de la base de datos, directorio del cliente de oracle, y la clasificacion como parámetros:
````
python3 linkedstats_generation.py "example_usr" "example_psw" "exampledir" "CNAE09"
````
#   Autor
- Diego Conde Herreros (OEG-UPM) - main contact  diego.conde.herreros at upm.es
