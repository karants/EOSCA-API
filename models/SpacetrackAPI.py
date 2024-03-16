#Import Pip libraries
import requests
import os

class SpaceTrackAPI:

    def __init__(self, immediate_auth=True):

        self.APIHost = "https://www.space-track.org/"
        self.GPEndpoint = "basicspacedata/query/class/gp/decay_date/null-val/epoch/%3Enow-30/orderby/norad_cat_id/"
        self.APIResponseFormat = "format/json"
        self.session = requests.Session()
        self.__apiusername = os.getenv('apiusername')
        self.__apipassword = os.getenv('apipassword')

        if immediate_auth:
            self.AttemptAuth()

    def AttemptAuth(self):
        url = self.APIHost + "ajaxauth/login"
        data = {'identity': self.__apiusername, 'password': self.__apipassword}
        response = self.session.post(url, data=data)
        if not response.ok:
            print("Authentication failed:", response.text) 
            raise Exception("Failed to authenticate with Space-Track API.")


    def GetResponse(self):
        url = self.APIHost + self.GPEndpoint + self.APIResponseFormat
        response = self.session.get(url)
        if response.status_code == 200:
            print("SpaceTrack API Auth Successful. Retrieved Data.")
            return response.json()
        else:
            raise Exception(f"Failed to fetch data. Status code: {response.status_code}")
