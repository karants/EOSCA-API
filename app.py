#This is the EOSCA API running on Flask.

#Importing pip libraries
from flask import Flask, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os
import datetime
from satellite_czml import satellite_czml
from satellite_czml import satellite
import sys
from flask_cors import CORS
from satellite_czml import satellite_czml as sczml
from satellite_czml import satellite as sat
import json

#importing classes from model directory
from models.DBConnection import DBRead, DBWrite, DBConnTest
from models.RiskAssessment import CollisionRiskAssessor
from models.SpaceObjects import DebrisElement, SatelliteElement

#function definition for refreshing
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


runrefreshflag = 0 #ONLY CHANGE TO 1 IF REFRESHING THE TELEMETRY IS REQUIRED

if(runrefreshflag==1):

    refreshTelemetry()

#App routes

@app.route("/", methods=['GET'])
def home():
    return "Welcome to the EOSCA API."

@app.route("/healthcheck/", methods=['GET'])

def healthcheck():
    return jsonify({'message': "I'm up and running :)"})

@app.route("/refresh/status", methods=['GET'])

def getrefreshstatus():

    status = DBReadConnection.GetRefreshState()

    if(status == 1):
        return jsonify({'message': "refreshing"})

    if(status != 1):
        return jsonify({'message': "ready"})

@app.route("/refresh/lastrefreshtime", methods=['GET'])

def getlastrefreshtime():

    lastrefresh = DBReadConnection.GetLastDataRefreshTime()

    print(lastrefresh)

    return jsonify({'lastrefresh': lastrefresh})

    
@app.route('/satellite/list', methods = ['GET'])

def getsatellites():

    satellites = DBReadConnection.GetSatellites()

    return jsonify(satellites)

@app.route('/satellite/ephemeris',methods = ['POST'])

def satelliteephemeris():
    
    satelliteid = request.form['satid']

    SatelliteTLE = DBReadConnection.GetSatelliteTLE(satelliteid)

    SatelliteObject = SatelliteElement(SatelliteTLE)

    satellite_czml_object = SatelliteObject.GetCZML()

    satellitelist = [satellite_czml_object]
    czml_obj = sczml(satellite_list=satellitelist, speed_multiplier=1)
    czml_string = czml_obj.get_czml()
    last_sat_key = list(czml_obj.satellites.keys())[-1]
    czml_obj.satellites.pop(last_sat_key, None)

    return czml_string

@app.route('/debris/list', methods = ['GET'])

def getdebris():

    debris = DBReadConnection.GetDebris()

    return jsonify(debris)

@app.route('/satellite/riskassessment',methods = ['POST'])

def riskassessment():
    
    satelliteid = request.form['satid']

    SatelliteTLE = DBReadConnection.GetSatelliteTLE(satelliteid)

    DebrisTLEs = DBReadConnection.GetDebrisTLEs()

    satellite_object = SatelliteElement(SatelliteTLE)

    debris_objects = [DebrisElement(TLE) for TLE in DebrisTLEs]

    RiskAssessor = CollisionRiskAssessor() 

    risk_assessments = RiskAssessor.assess_collision_risk(satellite_object, debris_objects)

    risk_assessments_sorted = sorted(risk_assessments, key=lambda x: x.closest_approach_distance, reverse=False)[:50]

    risk_assessments_json = []

    for assessment in risk_assessments_sorted:
        assessment_dict = {
            "Time of Closest Approach": assessment.closest_approach_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Closest Approach Distance (km)": assessment.closest_approach_distance,
            "Object": assessment.debris_id,
            "Probability of Collision": assessment.probability,
            "Risk Severity": assessment.risk_level
        }
        risk_assessments_json.append(assessment_dict)

    czml_objects = []

    satellite_czml_object = satellite_object.GetCZML() 
    czml_objects.append(satellite_czml_object)

    for debris in risk_assessments_json:

        DebrisTLEObjects = DBReadConnection.GetDebrisTLEForObject(debris['Object'])

        debris_object = DebrisElement(DebrisTLEObjects,debris['Risk Severity'])

        debris_czml_object = debris_object.GetCZML()

        czml_objects.append(debris_czml_object)

    czml_obj = sczml(satellite_list=czml_objects, speed_multiplier=1)
    czml_string = czml_obj.get_czml()

    czml_obj.satellites.clear()

    risk_assessment_response = {

        "risk_assessment_tabledata": risk_assessments_json,
        "updated_czml": czml_string
    }

    return jsonify(risk_assessment_response)

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