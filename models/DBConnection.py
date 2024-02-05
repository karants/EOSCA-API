from dotenv import load_dotenv
import os
import pyodbc

#Defining the connection string to the DB that can be utilized by multiple DB connection objects - reducing code duplication
class DBConnectionString:

    def __init__(self):
        
        #Load Env Variables and Construct Connection String
        load_dotenv()
        self.__conn_string = os.getenv('AZURE_SQL_CONNECTIONSTRING')

    def GetConnectionString(self):
        return self.__conn_string
