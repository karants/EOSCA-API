import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()
driver=os.getenv('driver')
server = os.getenv('server')
database = os.getenv('database')
sqlusername = os.getenv('sqlusername')
sqlpassword = os.getenv('sqlpassword')
conn_string = 'DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+sqlusername+';PWD='+ sqlpassword


with pyodbc.connect(conn_string) as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT TOP 3 name, collation_name FROM sys.databases")
        row = cursor.fetchone()
        while row:
            print (str(row[0]) + " " + str(row[1]))
            row = cursor.fetchone()