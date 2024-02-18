from dotenv import load_dotenv
import os
import pyodbc
import json
from datetime import datetime

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

        file_path = 'spacetrackfeb17.json'

        with open(file_path, 'r') as file:
            data = json.load(file)

        # Function to parse and return datetime object from string
        def parse_datetime(datetime_str):
            try:
                return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
            except ValueError:  # Adjust the format if it doesn't match
                return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%f")

        # Deduplication logic
        unique_records = {}
        for item in data:
            object_id = item["OBJECT_ID"]
            creation_date = parse_datetime(item["CREATION_DATE"])
            if object_id not in unique_records or creation_date > parse_datetime(unique_records[object_id]["CREATION_DATE"]):
                unique_records[object_id] = item

        sql_query = '''
                INSERT INTO SpaceObjectTelemetry (CREATION_DATE, OBJECT_NAME, OBJECT_ID, NORAD_CAT_ID, OBJECT_TYPE, TLE_LINE0, TLE_LINE1, TLE_LINE2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''' 
        i = 1
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
            print(i)
            i=i+1

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
        self.pool = DBReadPool(5)

        # Defining the maximum number of closest approaches to obtain
        self.numberofcas = 50

        self.satellites = []

    # Function to get the values from RefreshState table
    def GetRefreshState(self):

        self.conn = self.pool.acquire()
        self.conn.execute("SELECT * FROM Status")
        self.rows = self.conn.fetchall()
    
        # Closing the cursor
        self.conn.close()

        # Returning rows
        return self.rows[0][1]
    
    def GetLastDataRefreshTime(self):

        self.conn = self.pool.acquire()
        self.conn.execute("SELECT * FROM LastRefresh")
        self.rows = self.conn.fetchall()
    
        # Closing the cursor
        self.conn.close()

        # Returning rows
        return self.rows[0][1]
    
    def GetSatellites(self):

        self.conn = self.pool.acquire()
        self.conn.execute("SELECT OBJECT_NAME, OBJECT_ID FROM SpaceObjectTelemetry WHERE OBJECT_TYPE = 'PAYLOAD'")
        self.rows = self.conn.fetchall()
    
        # Closing the cursor
        self.conn.close()

        # Convert fetched data to a list of dictionaries
        self.satellites = [{"ObjectName": row[0], "ObjectID": row[1]} for row in self.rows]


        # Returning rows
        return self.satellites