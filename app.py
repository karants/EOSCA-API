#This is the EOSCA API running on Flask.

#Importing Pip libraries
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

#Initializing Flask instance
app = Flask(__name__)

#App routes

@app.route("/")
def home():
    return "Hello, Flask!"

#Running the Flask instance
if __name__ == '__main__':
   app.run()