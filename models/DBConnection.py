from dotenv import load_dotenv
import os
import pyodbc

#Defining the connection string to the DB that can be utilized by multiple DB connection objects - reducing code duplication
class DBConnectionString:

    def __init__(self):
        
        #Load Env Variables and Construct Connection String
        load_dotenv()
        self.__driver=os.getenv('driver')
        self.__server = os.getenv('server')
        self.__database = os.getenv('database')
        self.__sqlusername = os.getenv('sqlusername')
        self.__sqlpassword = os.getenv('sqlpassword')
        self.__conn_string = 'DRIVER='+self.__driver+';SERVER=tcp:'+self.__server+';PORT=1433;DATABASE='+self.__database+';UID='+self.__sqlusername+';PWD='+ self.__sqlpassword


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

        self.conn = self.pool.acquire()
        self.conn.execute("SELECT * FROM Status")
        self.rows = self.conn.fetchall()
    
        # Closing the cursor
        self.conn.close()

        # Returning rows
        return self.rows[0][1]