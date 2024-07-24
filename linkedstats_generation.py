#This is the script for the automatic generation of the data of the linkedstats project for reuse within the INE. 
import morph_kgc
import sys
input_data = sys.argv[1]
client_dir = sys.argv[2]
config = """
        [CONFIGURATION]
        oracle_client_lib_dir:"""+client_dir+"""
        output_file: nt_data/clasificaciones_"""+input_data+"""_BD.nt
        infer_sql_datatypes: yes
        [DataSource1]
        mappings: mappings/mappings_"""+input_data+""".ttl
        db_url: oracle+cx_oracle://AYUDACOD2024PRO_READ:READAYUDACOD2024@http://p8dbejv12kvm.ine.es:1622/PRO19
        """
morph_kgc.materialize(config)