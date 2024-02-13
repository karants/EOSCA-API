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

#Object Pool implementation
class DBReadPool:

    _instance = None

    def __init__(self, size):

        if DBReadPool._instance != None:
            raise Exception("%s is a Singleton object. It can only be instantiated once." % type(self).__name__)
        else:
            DBReadPool._instance = self

        self.conn = DBConnectionString()
        self.conn_string = self.conn.GetConnectionString()

        #array for the pool
        self._reusableconnections = []

        #filling up the pool with DB connections
        for _ in range(size):
            self.conn = pyodbc.connect(self.conn_string)
            self._reusableconnections.append(self.conn.cursor())

    def acquire(self):
        return self._reusableconnections.pop()

    def release(self, reusable):
        self._reusableconnections.append(reusable)

#Executing DB read functions
class DBRead:

    def __init__(self):

        #instantiating the pool with a size
        self.pool = DBReadPool(5)

        # Defining the maximum number of closest approaches to obtain
        self.numberofcas = 50

    # Function to get the values from RefreshState table
    def GetRefreshState(self):

        # Executing the SQL query to get top hits
        self.cursor.execute("SELECT * FROM RefreshState")
        self.rows = self.cursor.fetchall()
    
        # Closing the cursor
        self.cursor.close()

        # Returning rows
        return self.rows
    

DBReadConnection = DBRead()

refreshstate = DBReadConnection.GetRefreshState()

print(refreshstate)