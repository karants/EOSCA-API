#This is the EOSCA API running on Flask.

#Importing pip libraries
from flask import Flask, jsonify, request
import flask_swagger_ui
from apscheduler.schedulers.background import BackgroundScheduler

#importing classes from model directory
from models.DBConnection import DBRead, DBWrite

#Instantiating Database Write & Read Connections
DBReadConnection = DBRead()
DBWriteConnection = DBWrite()

#function definition for refreshing
def refreshTelemetry():

    #Recreate the telemetry table
    DBWriteConnection.ClearSpaceObjectTelemetry()
    
    

#Initializing Flask instance
app = Flask(__name__)

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

@app.route('/satellite/ephemeris',methods = ['POST'])

def satelliteephemeris():
    satelliteid = request.form['satid']


#Running the Flask instance
if __name__ == '__main__':
   app.run()