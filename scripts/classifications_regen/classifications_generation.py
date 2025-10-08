#This is the script for the automatic generation of the data of the linkedstats project for reuse within the INE. 
import morph_kgc
import sys
db_usr = sys.argv[1]
db_psw = sys.argv[2]
data = sys.argv[3]
config = """
[CONFIGURATION]
output_file: nt_data/clasificaciones_"""+data+""".nt
na_values: None, ,null
[ORACLE_DB]
mappings: test_mappings_"""+data+""".ttl
db_url=oracle+cx_oracle://"""+db_usr+""":"""+db_psw+"""@(DESCRIPTION = (ADDRESS =(PROTOCOL = TCP)(HOST=p8dbejv12kvm.ine.es)(PORT = 1622))(CONNECT_DATA =(SERVER = DEDICATED)(SERVICE_NAME = PRO19)))
        """
morph_kgc.materialize(config)