import pyodbc
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
driver=os.getenv('driver')
server = os.getenv('server')
database = os.getenv('database')
sqlusername = os.getenv('sqlusername')
sqlpassword = os.getenv('sqlpassword')
conn_string = 'DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+sqlusername+';PWD='+ sqlpassword


with pyodbc.connect(conn_string) as conn:
    with conn.cursor() as cursor:
        sql_query = 'INSERT INTO LastRefresh (Refresh_ID, Refresh_Time) VALUES (?,?)'
        cursor.execute(sql_query, (1,datetime.now()))
        cursor.commit()

