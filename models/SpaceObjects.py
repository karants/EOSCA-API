from satellite_czml import satellite_czml as sczml
from satellite_czml import satellite as sat
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import importlib

class DesignElementTemplate(ABC):
    def __init__(self):
        self.show_path = False  
        self.show_label = False  
        self.use_default_image = False
        self.color = [250,250,255]
        self.marker_scale= 10
        self.TLE = []
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(days=1)

    def GetCZML(self):

        self.czml_string = ""

        self.spaceobj = sat(self.TLE, use_default_image=self.use_default_image, 
                             color = self.color, marker_scale=self.marker_scale,
                            show_path=self.show_path,show_label=self.show_label,
                            start_time=self.start_time, end_time=self.end_time)
        
        self.satellitelist = [self.spaceobj]

        self.czml_obj = sczml(satellite_list=self.satellitelist)

        self.czml_string = self.czml_obj.get_czml()

        self.satellitelist.clear()
        del self.spaceobj

        last_sat_key = list(self.czml_obj.satellites.keys())[-1]

        self.czml_obj.satellites.pop(last_sat_key, None)

        return self.czml_string
    
    def getTLE(self):

        return self.TLE

    def toggle_path_visibility(self):
        self.show_path = not self.show_path

class SatelliteElement(DesignElementTemplate):
    def __init__(self, TLE):
        super().__init__()

        self.TLE = TLE
        self.show_path = True  #overriding super


class DebrisElement(DesignElementTemplate):
    def __init__(self):
        super().__init__()

class CriticalRiskDebrisElement(DebrisElement):
    def __init__(self):
        super().__init__()
        self.risk_level = "Critical"
        # Additional attributes or methods specific to critical risk debris

    def display_element(self):
        # Implementation specific to CriticalRiskDebrisElement
        print(f"Displaying Critical Risk Debris Element. Show path: {self.show_path}, Risk level: {self.risk_level}")

class HighRiskDebrisElement(DebrisElement):
    def __init__(self):
        super().__init__()
        self.risk_level = "High"
        # Additional attributes or methods specific to high risk debris

    def display_element(self):
        # Implementation specific to HighRiskDebrisElement
        print(f"Displaying High Risk Debris Element. Show path: {self.show_path}, Risk level: {self.risk_level}")

class MediumLowRiskDebrisElement(DebrisElement):
    def __init__(self):
        super().__init__()
        self.risk_level = "Medium-Low"
        # Additional attributes or methods specific to medium-low risk debris

    def display_element(self):
        # Implementation specific to MediumLowRiskDebrisElement
        print(f"Displaying Medium-Low Risk Debris Element. Show path: {self.show_path}, Risk level: {self.risk_level}")