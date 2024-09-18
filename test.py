import oracledb

un = 'AYUDACOD2024PRO_READ'
cs = 'p8dbejv12kvm.ine.es:1622/PRO19'
pw = 'READAYUDACOD2024'

with oracledb.connect(user=un, password=pw, dsn=cs) as connection:
    with connection.cursor() as cursor:
        sql = """select sysdate from dual"""
        for r in cursor.execute(sql):
            print(r)