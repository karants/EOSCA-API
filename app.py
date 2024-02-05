#This is the EOSCA API running on Flask.

#Importing pip libraries
from flask import Flask, jsonify, request
import flask_swagger_ui

#Initializing Flask instance
app = Flask(__name__)

#App routes

@app.route("/", methods=['GET'])
def home():
    return "Welcome to the EOSCA API."

@app.route("/healthcheck/", methods=['GET'])
def healthcheck():
    return jsonify({'message': "I'm up and running :)"})

@app.route('/satellite/ephemeris',methods = ['POST'])
def satelliteephemeris():
    satelliteid = request.form['satid']


#Running the Flask instance
if __name__ == '__main__':
   app.run()