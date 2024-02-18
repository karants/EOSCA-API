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
                                    CCSDS_OMM_VERS VARCHAR(50),
                                    COMMENT VARCHAR(255),
                                    CREATION_DATE DATETIME2,
                                    ORIGINATOR VARCHAR(50),
                                    OBJECT_NAME VARCHAR(255),
                                    OBJECT_ID VARCHAR(50) PRIMARY KEY,
                                    CENTER_NAME VARCHAR(50),
                                    REF_FRAME VARCHAR(50),
                                    TIME_SYSTEM VARCHAR(50),
                                    MEAN_ELEMENT_THEORY VARCHAR(50),
                                    EPOCH DATETIME2,
                                    MEAN_MOTION FLOAT,
                                    ECCENTRICITY FLOAT,
                                    INCLINATION FLOAT,
                                    RA_OF_ASC_NODE FLOAT,
                                    ARG_OF_PERICENTER FLOAT,
                                    MEAN_ANOMALY FLOAT,
                                    EPHEMERIS_TYPE INT,
                                    CLASSIFICATION_TYPE CHAR(1),
                                    NORAD_CAT_ID INT,
                                    ELEMENT_SET_NO VARCHAR(50),
                                    REV_AT_EPOCH INT,
                                    BSTAR FLOAT,
                                    MEAN_MOTION_DOT FLOAT,
                                    MEAN_MOTION_DDOT FLOAT,
                                    SEMIMAJOR_AXIS FLOAT,
                                    PERIOD_NUM FLOAT,
                                    APOAPSIS FLOAT,
                                    PERIAPSIS FLOAT,
                                    OBJECT_TYPE VARCHAR(50),
                                    RCS_SIZE VARCHAR(50),
                                    COUNTRY_CODE CHAR(2),
                                    LAUNCH_DATE DATE,
                                    SITE VARCHAR(50),
                                    DECAY_DATE DATE,
                                    FILE_NUM BIGINT,
                                    GP_ID BIGINT,
                                    TLE_LINE0 VARCHAR(255),
                                    TLE_LINE1 VARCHAR(255),
                                    TLE_LINE2 VARCHAR(255)
                            )""")
        self.conn.commit()


#Object Pool implementation for DB Read
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