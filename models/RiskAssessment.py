from datetime import datetime, timedelta
import numpy as np

class RiskAssessment:
    def __init__(self, debris_id, closest_approach_time, closest_approach_distance, probability, risk_level):
        self.debris_id = debris_id
        self.closest_approach_time = closest_approach_time
        self.closest_approach_distance = closest_approach_distance
        self.probability = probability
        self.risk_level = risk_level

class CollisionRiskAssessor:
    
    def __init__(self):

        self.margin_of_error = 3.0 #km
        self.threshold_distance = 10.0 # km A specific distance threshold (10.0 km in this case) beyond which the probability of collision is considered low enough to be negligible.
        self.radius_satellite = 0.12 # km (The Largest Object in Orbit, International Space Station is about 107m wide)
        self.radius_debris = 0.10 # km (worst case scenario: debris field)
        self.risk_boundary = self.margin_of_error + self.threshold_distance #The sum of margin_of_error and threshold_distance, representing a distance beyond which the risk of collision is considered extremely low.
        self.collision_radius = self.radius_satellite + self.radius_debris
        self.start_time = datetime.utcnow()
        self.duration = timedelta(hours=24)
        self.time_step = timedelta(minutes=1)

    @staticmethod
    def calculate_distance(pos1, pos2):
        return np.linalg.norm(np.array(pos1) - np.array(pos2))


    def calculate_probability(self, distance):
        adjusted_distance = max(distance - self.collision_radius, 0)
        if adjusted_distance >= self.risk_boundary:
            return np.exp(-adjusted_distance / self.risk_boundary) #exponential decay function based on the ratio of the adjusted distance to the risk boundary
        else:
            return 1.0

    @staticmethod
    def determine_risk_level(probability):
        if 0.8 <= probability <= 1.0:
            return "Critical"
        elif 0.6 <= probability < 0.8:
            return "High"
        elif 0.3 <= probability < 0.6:
            return "Medium"
        elif 0 <= probability < 0.3:
            return "Low"
        else:
            return "Undefined"
    
    def assess_collision_risk(self, satellite, debris_objects):

        risk_assessments = []
        
        for i, debris in enumerate(debris_objects, start=1):
            closest_approach_distance = float('inf')
            closest_approach_time = None

            current_time = self.start_time
            while current_time < self.start_time + self.duration:
                r_satellite = satellite.get_position(current_time)
                r_debris = debris.get_position(current_time)
                
                distance = self.calculate_distance(r_satellite, r_debris)
                if distance < closest_approach_distance:
                    closest_approach_distance = distance
                    closest_approach_time = current_time

                current_time += self.time_step

            probability = self.calculate_probability(closest_approach_distance)
            risk_level = self.determine_risk_level(probability)
            object_id = debris.getObjectID()
            risk_assessments.append(RiskAssessment(object_id, closest_approach_time, closest_approach_distance, probability, risk_level))

        return risk_assessments
