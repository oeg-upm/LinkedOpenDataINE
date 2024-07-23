# LinkedOpenDataINE
Este repositorio existe para subir los recursos semánticos generados para el proyecto LinkedOpenData, colaboración entre el Ontology Engineering Group y el Instituto Nacional de Estadística.

Los pasos a seguir para generar estos datos en local son los siguientes:

    Tener en el equipo instalado Python3 y pip.

    Descargar el [Oracle Client](https://www.oracle.com/database/technologies/instant-client/downloads.html), la última versión en forma de ZIP.

    Descomprime el ZIP del cliente de Oracle en la carpeta sobre la que se vaya a trabajar.

    Se instala el paquete libaio (libaio1) en algunas distribuciones de Linux con: 
        ```bash
        python3 -m pip install libaio1
        ```      
    Se establece la variable de entorno LD_LIBRARY_PATH al directorio en el que está el cliente de Oracle:
        ```bash
        export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1:$LD_LIBRARY_PATH
        ```
    Se instala la librería cx_Oracle para la ejecución de Morph-KGC sobre bases de datos Oracle:
        ```bash
        python3 -m pip install cx_Oracle --upgrade
        ```
    Instalar la librería de Morph-KGC y su extensión para bases de datos Oracle:
        ```bash
        python3 -m pip install cx_Oracle --upgrade
        ```   
    Ejecutar el script linkedstats_generation con el dataset a regenerar como parámetro:
        ```bash
        python3 linkedstats_generation.py "CNAE09"
        ```
#   Autor
- Diego Conde Herreros (OEG-UPM) - main contact  diego.conde.herreros at upm.es