from satellite_czml import satellite_czml as sczml
from satellite_czml import satellite as sat
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from sgp4.api import Satrec
from sgp4.conveniences import jday

class DesignElementTemplate(ABC):

    start_time = datetime.now()
    end_time = start_time + timedelta(days=1)

    def __init__(self):
        self.object_id = ""
        self.show_path = False  
        self.show_label = False  
        self.use_default_image = False
        self.color = [250,250,255]
        self.marker_scale= 20
        self.TLE = []

    def GetCZML(self):

        self.spaceobj = sat(self.TLE, use_default_image=self.use_default_image, 
                             color = self.color, marker_scale=self.marker_scale,
                            show_path=self.show_path,show_label=self.show_label,
                            start_time=self.start_time, end_time=self.end_time)

        return self.spaceobj
    
    def getTLE(self):

        return self.TLE
    
    def getObjectID(self):

        return self.object_id
    
    def get_position(self, current_time):
        jd, fr = jday(current_time.year, current_time.month, current_time.day,
                      current_time.hour, current_time.minute, current_time.second + current_time.microsecond * 1e-6)
        e, r, v = self.satrec.sgp4(jd, fr)

        return r

    def toggle_path_visibility(self):
        self.show_path = not self.show_path

class SatelliteElement(DesignElementTemplate):
    def __init__(self, TLE):
        super().__init__()

        self.object_id = TLE[0]
        self.TLE = TLE[1:]
        self.show_path = True  #overriding super
        self.satrec = Satrec.twoline2rv(*self.TLE[1:])

class DebrisElement(DesignElementTemplate):
    def __init__(self, TLE, risk=None):
        super().__init__()

        self.object_id = TLE[0]
        self.TLE = TLE[1:]
        self.show_path = False  #overriding super
        self.satrec = Satrec.twoline2rv(*self.TLE[1:])       

        if risk == "Critical":
            self.color = [108, 52, 131]
            self.marker_scale= 16

        elif risk == "High":
            self.color = [169, 50, 38]
            self.marker_scale= 12
        
        elif risk == "Medium":
            self.color = [19, 141, 117]
            self.marker_scale= 8
        
        elif risk == "Low":
            self.color = [19, 141, 117]
            self.marker_scale= 6
        
        else:
            self.color = [250,250,255]