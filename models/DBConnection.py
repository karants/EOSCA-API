from dotenv import load_dotenv
import os
import pyodbc
from datetime import datetime
import time

from models.SpacetrackAPI import SpaceTrackAPI 

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
        self.__conn_string = 'DRIVER='+self.__driver+';SERVER=tcp:'+self.__server+';PORT=1433;DATABASE='+self.__database+';UID='+self.__sqlusername+';PWD='+ self.__sqlpassword + ';TrustServerCertificate=yes;'


    def GetConnectionString(self):
        return self.__conn_string
    
class DBConnTest:
    def __init__(self):
        self.conn_string = DBConnectionString().GetConnectionString()

    def TestConnection(self):
        max_retries = 10
        attempt_count = 0
        while attempt_count < max_retries:
            try:
                conn = pyodbc.connect(self.conn_string, timeout=10)
                conn.close()
                print("Connected to SQL successfully.")
                return True
            except Exception as e:
                print(f"Connection failed: {e}")
                attempt_count += 1
                print(f"Retry attempt {attempt_count} of {max_retries}...")
                time.sleep(2)  # Wait for 2 seconds before retrying
        print("Failed to connect after maximum retries.")
        return False

#Singleton Pattern Implementation for Logging Data to the DB

class DBWrite:
    _instance = None

    def __init__(self):

        if DBWrite._instance != None:
            raise Exception("%s is a Singleton object. It can only be instantiated once." % type(self).__name__)
        else:
            DBWrite._instance = self

        self.conn = DBConnectionString()
        self.conn_string = self.conn.GetConnectionString()
        self.conn = pyodbc.connect(self.conn_string)
        self.cursor = self.conn.cursor()

    def ClearSpaceObjectTelemetry(self):

        #Drop the table
        self.conn.execute("DROP TABLE IF EXISTS SpaceObjectTelemetry;")

        #Create the table. Object ID is the primary key.
        self.conn.execute(""" CREATE TABLE SpaceObjectTelemetry (
                                    CREATION_DATE DATETIME2,
                                    OBJECT_NAME VARCHAR(255),
                                    OBJECT_ID VARCHAR(50) PRIMARY KEY,
                                    NORAD_CAT_ID INT,
                                    OBJECT_TYPE VARCHAR(50),
                                    TLE_LINE0 VARCHAR(255),
                                    TLE_LINE1 VARCHAR(255),
                                    TLE_LINE2 VARCHAR(255)
                            )""")
        self.conn.commit()

    def CopySpaceObjectTelemetry(self):

        APISession = SpaceTrackAPI()
        APIResponse = APISession.GetResponse()

        # Function to parse and return datetime object from string
        def parse_datetime(datetime_str):
            try:
                return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
            except ValueError:  # Adjust the format if it doesn't match
                return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%f")

        # Deduplication logic
        unique_records = {}
        for item in APIResponse:
            object_id = item["OBJECT_ID"]
            creation_date = parse_datetime(item["CREATION_DATE"])
            if object_id not in unique_records or creation_date > parse_datetime(unique_records[object_id]["CREATION_DATE"]):
                unique_records[object_id] = item

        sql_query = '''
                INSERT INTO SpaceObjectTelemetry (CREATION_DATE, OBJECT_NAME, OBJECT_ID, NORAD_CAT_ID, OBJECT_TYPE, TLE_LINE0, TLE_LINE1, TLE_LINE2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''' 
        # Iterate over each item in the JSON data and insert it into the database
        for item in unique_records.values():
            self.conn.execute(sql_query, (
                item.get("CREATION_DATE"),
                item.get("OBJECT_NAME"),
                item.get("OBJECT_ID"),
                item.get("NORAD_CAT_ID"),
                item.get("OBJECT_TYPE"),
                item.get("TLE_LINE0"),
                item.get("TLE_LINE1"),
                item.get("TLE_LINE2")
            ))

            # Commit the transaction for each insert to ensure data integrity
            self.conn.commit()

        sql_query = "UPDATE LastRefresh SET Refresh_Time = ? WHERE Refresh_ID = 1"
        self.conn.execute(sql_query, (datetime.now()))
        self.conn.commit()

#Object Pool + Singleton implementation for DB Read
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
        self.pool = DBReadPool(12)

        # Defining the maximum number of closest approaches to obtain
        self.numberofcas = 50

        self.satellites = []
        self.satelliteTLE = []

    # Function to get the values from RefreshState table
    def GetRefreshState(self):

        self.conn = self.pool.acquire()
        self.conn.execute("SELECT * FROM Status")
        self.rows = self.conn.fetchall()
    
        # release the conn
        self.pool.release(self.conn)

        # Returning rows
        return self.rows[0][1]
    
    def GetLastDataRefreshTime(self):

        self.conn = self.pool.acquire()
        self.conn.execute("SELECT * FROM LastRefresh")
        self.rows = self.conn.fetchall()
    
        # release the conn
        self.pool.release(self.conn)

        # Returning rows
        return self.rows[0][1]
    
    def GetSatellites(self):

        self.conn = self.pool.acquire()
        self.conn.execute("SELECT OBJECT_NAME, OBJECT_ID FROM SpaceObjectTelemetry WHERE OBJECT_TYPE = 'PAYLOAD'")
        self.rows = self.conn.fetchall()
    
        # release the conn
        self.pool.release(self.conn)

        # Convert fetched data to a list of dictionaries
        self.satellites = [{"ObjectName": row[0], "ObjectID": row[1]} for row in self.rows]


        # Returning rows
        return self.satellites
    
    def GetSatelliteTLE(self, SatelliteID):

        self.conn = self.pool.acquire()
        sql_query = "SELECT OBJECT_ID, TLE_LINE0, TLE_LINE1, TLE_LINE2 FROM SpaceObjectTelemetry WHERE OBJECT_ID = ?"
        self.conn.execute(sql_query, (SatelliteID,))
        self.row = self.conn.fetchone()
    
        # release the conn
        self.pool.release(self.conn)

        # Convert fetched data to a list of dictionaries
        if self.row:
            self.satelliteTLE = [self.row[0], self.row[1], self.row[2], self.row[3]]
        else:
            self.satelliteTLE = []  # In case there is no result for the given SatelliteID

        # Returning rows
        return self.satelliteTLE
    
    def GetDebris(self):

        self.conn = self.pool.acquire()
        self.conn.execute("SELECT OBJECT_NAME, OBJECT_ID FROM SpaceObjectTelemetry WHERE OBJECT_TYPE = 'DEBRIS'")
        self.rows = self.conn.fetchall()
    
        # release the conn
        self.pool.release(self.conn)

        # Convert fetched data to a list of dictionaries
        self.debris = [{"ObjectName": row[0], "ObjectID": row[1]} for row in self.rows]


        # Returning rows
        return self.debris
    
    def GetDebrisTLEs(self):

        self.conn = self.pool.acquire()
        sql_query = "SELECT OBJECT_ID, TLE_LINE0, TLE_LINE1, TLE_LINE2 FROM SpaceObjectTelemetry WHERE OBJECT_TYPE = 'DEBRIS'"
        self.conn.execute(sql_query)
        rows = self.conn.fetchall()
    
        # release the conn
        self.pool.release(self.conn)

         # Initialize a list to hold all the TLEs
        self.DebrisTLEs = []

        # Convert fetched data to a list of dictionaries
        if rows:
            for row in rows:
                # Append each TLE set to the list
                self.DebrisTLEs.append([row[0], row[1], row[2], row[3]])
        else:
            self.DebrisTLEs = []  # In case there are no results

        # Return the list of TLEs
        return self.DebrisTLEs
    
    def GetDebrisTLEForObject(self,objectid):

        self.conn = self.pool.acquire()
        sql_query = "SELECT OBJECT_ID, TLE_LINE0, TLE_LINE1, TLE_LINE2 FROM SpaceObjectTelemetry WHERE OBJECT_ID = ?"
        self.conn.execute(sql_query, (objectid,))
        self.row = self.conn.fetchone()
    
        # release the conn
        self.pool.release(self.conn)

        # Convert fetched data to a list of dictionaries
        if self.row:
            self.debrisTLE = [self.row[0], self.row[1], self.row[2], self.row[3]]
        else:
            self.debrisTLE = []  # In case there is no result for the given SatelliteID

        # Returning rows
        return self.debrisTLE
    