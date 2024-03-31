#This is the EOSCA API running on Flask.

#Importing pip libraries
from flask import Flask, jsonify, request
import sys
from flask_cors import CORS

#Importing classes from model directory
from models.DBConnection import DBRead, DBWrite, DBConnTest
from models.RiskAssessment import CollisionRiskAssessor
from models.SpaceObjects import  SatelliteElement

#Function definition for refreshing telemetry
def refreshTelemetry():

    #Recreate the telemetry table
    DBWriteConnection.ClearSpaceObjectTelemetry()
    DBWriteConnection.CopySpaceObjectTelemetry()
    

#Initializing Flask instance
app = Flask(__name__)
CORS(app)

#Instantiating Database Write & Read Connections
DBReadConnection = DBRead()
DBWriteConnection = DBWrite()
DBConnectionTest = DBConnTest()

runrefreshflag = 0 #ONLY CHANGE TO 1 IF REFRESHING THE TELEMETRY IS REQUIRED. IF THIS WAS HOSTED ON A WEB SERVER, AUTOMATION WOULD BE IN PLACE TO REFRESH TELEMETRY EVERY 24 HOURS

if(runrefreshflag==1):

    refreshTelemetry()

#App routes

@app.route("/", methods=['GET'])
def home():
    return "Welcome to the EOSCA API."

@app.route("/healthcheck/", methods=['GET'])

def HealthCheck():
    return jsonify({'message': "I'm up and running :)"})

@app.route("/refresh/status", methods=['GET'])

def GetRefreshStatus():

    status = DBReadConnection.GetRefreshState()

    if(status == 1):
        return jsonify({'message': "refreshing"})

    if(status != 1):
        return jsonify({'message': "ready"})

@app.route("/refresh/lastrefreshtime", methods=['GET'])

def GetLastRefresh():

    LastRefresh = DBReadConnection.GetLastDataRefreshTime()

    return jsonify({'lastrefresh': LastRefresh})

    
@app.route('/satellite/list', methods = ['GET'])

def GetSatellites():

    Satellites = DBReadConnection.GetSatellites() #Get a list of all satellites

    return jsonify(Satellites)

@app.route('/satellite/ephemeris',methods = ['POST'])

def SatelliteEphemeris(): #Retrieves ephemeris in CZML format for the chosen satellite
    
    #Retrieve satid from the form
    SatelliteID = request.form['satid']

    #Read TLE data from the database for the chosen satellite
    SatelliteTLE = DBReadConnection.GetSatelliteTLE(SatelliteID)

    #Create a SatelliteElement object for the satellite using the TLE data that is retrieved
    SatelliteObject = SatelliteElement(SatelliteTLE)

    return SatelliteObject.GetCZMLString()

@app.route('/debris/list', methods = ['GET'])

def GetDebris():

    debris = DBReadConnection.GetDebris() #Get a list of all the Debris

    return jsonify(debris)

@app.route('/satellite/riskassessment',methods = ['POST'])

def RiskAssessment():
    
    #Get the satellite id from frontend
    SatelliteID = request.form['satid']

    #Read the TLE data from the database for the chosen satellite
    SatelliteTLE = DBReadConnection.GetSatelliteTLE(SatelliteID)

    #Read the TLE data from the database for all of the Debris objects
    DebrisTLEs = DBReadConnection.GetDebrisTLEs()

    #Initiate the SatelliteObject
    SatelliteObject = SatelliteElement(SatelliteTLE)

    #Initiate the RiskAssessor Object
    RiskAssessor = CollisionRiskAssessor() 

    #Retrieve risk assessment results between the satellite and all of the debris
    RiskAssessments = RiskAssessor.AssessCollisionRiskParallel(SatelliteTLE, DebrisTLEs, TimeInterval=1)

    #Convert risk assessment results to JSON
    RiskAssessmentsJSON = RiskAssessor.GetAssessmentJSON(RiskAssessments)

    #Get the updated CZML after the risk assessment with the top 50 debris objects and the satellite
    UpdatedCZML = RiskAssessor.UpdateCZMLPostAssessment(DBReadConnection, SatelliteObject, RiskAssessmentsJSON)

    #Create a nested JSON for the response
    RiskAssessmentResponse = {

        "risk_assessment_tabledata": RiskAssessmentsJSON,
        "updated_czml": UpdatedCZML
    }

    return jsonify(RiskAssessmentResponse)

@app.route('/reassess/debris',methods = ['POST'])

def RefineAssessment():

    #Get the ObjectIDs from frontend
    ObjectIDs = request.get_json()

    OneSecondInterval = 0.0167

    #Read the TLE data from the database for the chosen satellite
    SatelliteTLE = DBReadConnection.GetSatelliteTLE(ObjectIDs['SatelliteID'])

    #Retrieve Debris TLEs
    DebrisTLEs = []
    for DebrisID in ObjectIDs['DebrisIDs']:
      DebrisTLEObject = DBReadConnection.GetDebrisTLEForObject(DebrisID)
      DebrisTLEs.append(DebrisTLEObject)

    #Initiate the RiskAssessor Object
    RiskAssessor = CollisionRiskAssessor() 

    #Retrieve enhanced risk assessment results between the satellite and all of the debris for 1 second intervals
    RiskAssessments = RiskAssessor.AssessCollisionRiskParallel(SatelliteTLE, DebrisTLEs, TimeInterval=OneSecondInterval)

    #Convert risk assessment results to JSON
    RiskAssessmentsJSON = RiskAssessor.GetAssessmentJSON(RiskAssessments)

    #Initiate the SatelliteObject
    SatelliteObject = SatelliteElement(SatelliteTLE)

    #Get the updated CZML after the risk assessment with the top 50 debris objects and the satellite
    UpdatedCZML = RiskAssessor.UpdateCZMLPostAssessment(DBReadConnection, SatelliteObject, RiskAssessmentsJSON)

    #Create a nested JSON for the response
    RiskAssessmentResponse = {

        "risk_assessment_tabledata": RiskAssessmentsJSON,
        "updated_czml": UpdatedCZML
    }

    return jsonify(RiskAssessmentResponse)

#Running the Flask instance
if __name__ == '__main__':
    
    DBConnectionTest = DBConnTest()
    if not DBConnectionTest.TestConnection():
        print("Unable to connect to the database after multiple retries. Please check the database status.")
        sys.exit(1)
        
    else:
        # Proceed with running the Flask app if the connection is successful
        if __name__ == '__main__':
            app.run()