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
    def __init__(self, size, connection_string):
        self.conn_string = connection_string
        self._reusableconnections = []

        for _ in range(size):
            self.conn = pyodbc.connect(self.conn_string)
            self._reusableconnections.append(self.conn.cursor())

    def acquire(self):
        return self._reusableconnections.pop()

    def release(self, reusable):
        self._reusableconnections.append(reusable)

#Executing DB read functions
class DBRead:

    def __init__(self, connection_string):
        # Connect to DB 
        self.conn = pyodbc.connect(connection_string)
        self.cursor = self.conn.cursor()

        # Defining the maximum number of hits to obtain
        self.maxhits = 10

    # Function to get the top hits from the hits table
    def GetTopHits(self):
        # Executing the SQL query to get top hits
        self.cursor.execute("SELECT * FROM RefreshState ORDER BY hits DESC LIMIT ?", (self.maxhits,))
        self.hits = self.cursor.fetchall()
        
        # Extracting exoplanet names from the results
        self.tophits = [row[0] for row in self.hits]

        # Closing the cursor
        self.cursor.close()

        # Returning array of exoplanet names
        return self.tophits