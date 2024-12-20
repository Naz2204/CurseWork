from kivy.app import App
from kivy.utils import platform
from kivymd.uix.dialog import MDDialog

import requests

class GetData:
    def __init__(self):
        self.location: list = [0, 0]

    def run(self):
        #Request permission on Android
        if platform == "android":
            from android.permitions import Permission, request_permissions
            from plyer import gps

            def callback(permission, results):
                if all([res for res in results]):
                    print("Permission granted")
                else:
                    print("Permission granted")
            #asks for permittion
            request_permissions([Permission.ACCESS_COARSE_LICATION, Permission.ACCESS_FINE_LOCATION], callback)

            gps.configure(on_location=self.__get_coordinates,
                            on_status=self.__on_auth_status)
            gps.start(minTime=1000)


    def __get_coordinates(self, *args, **kwargs):
        self.location[0] = kwargs['lat']
        self.location[1] = kwargs['lon']

    def __on_auth_status(self, general_status, status_message):
        if general_status == "provider-enabled":
            print("GPS found")
        else:
            #TODO викликати вікно з попередженням що потрібний GPS
            pass

    def GPS_turned_off_popup(self):
        dialog = MDDialog(title = "GPS Error", text = "For app functionality turn GPS on")
        dialog.size_hint = (0.8, 0.8)
        dialog.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        dialog.open()

    def get_nearest_locality(self):
        pass

    def get_closest_fuel_station(self):
        latitude, longitude = self.location
        # Define a small bounding box around the point
        fuel_station_url = f"https://overpass-api.de/api/interpreter"
        fuel_station_query = f"""
                [out:json];
                (
                    node["amenity"="fuel"](around:1000,{latitude},{longitude}); 
                    way["amenity"="fuel"](around:1000,{latitude},{longitude});
                ); 
                out center;
                """

        rout_url = "http://router.project-osrm.org/route/v1/driving/"

        response = requests.get(fuel_station_url, params={'data': fuel_station_query})

        if response.status_code == 200:
            data = response.json()
            closest_station = None
            closest_distance = 999999999999999
            for element in data['elements']:
                station_coords = None
                if element['type'] == 'way':
                    station_coords = [element['center']['lon'], element['center']['lat']]
                else:
                    station_coords = [element['lat'], element['lon']]

                distance_result = requests.get(rout_url + longitude + "," + latitude + ";" + station_coords[0]+
                                        "," + station_coords[1] + "?overview=false")

                if distance_result.status_code == 200:
                    distance_result = distance_result.json()
                    if distance_result["code"] == "Ok" and distance_result["routes"]["distance"]:
                        distance = distance_result["routes"]["distance"]
                    else:
                        distance = 999999999999999

                    if element['name'] and distance < closest_distance:
                        closest_station = element['name']

            if not closest_station:
                return "No fuel stations found."
            else:
                return closest_station
        else:
            print("Overpass API error:", response.status_code, response.text)
            return None


    def get_speed(self): pass


    def get_speed_limit(self):
        latitude, longitude = self.location
        # Define a small bounding box around the point
        bbox = f"{latitude - 0.0001},{longitude - 0.0001},{latitude + 0.0001},{longitude + 0.0001}"

        url = f"https://overpass-api.de/api/interpreter"
        query = f"""
                [out:json];
                way
                  [highway]
                  ( {bbox} );
                out tags;
                """
        response = requests.get(url, params={'data': query})
        if response.status_code == 200:
            data = response.json()
            for element in data['elements']:
                if 'maxspeed' in element['tags']:
                    return element['tags']['maxspeed']
            return "No speed limit found."
        else:
            print("Overpass API error:", response.status_code, response.text)
            return None
