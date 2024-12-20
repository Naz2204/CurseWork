from kivy.app import App
from kivy.utils import platform
from kivymd.uix.dialog import MDDialog
from geopy.distance import geodesic
import requests

INFINITE = 999999999999999

class GetData:
    def __init__(self):

        self.__location: list = [INFINITE, INFINITE]
        self.__old_location: list = [0, 0]

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
        self.__old_location[0] = self.__location[0]
        self.__old_location[1] = self.__location[1]

        self.__location[0] = kwargs['lat']
        self.__location[1] = kwargs['lon']


    def __on_auth_status(self, general_status, status_message):
        if general_status == "provider-enabled":
            print("GPS found")
        else:
            self.GPS_turned_off_popup()

    def GPS_turned_off_popup(self):
        dialog = MDDialog(title = "GPS Error", text = "For app functionality turn GPS on")
        dialog.size_hint = (0.8, 0.8)
        dialog.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        dialog.open()

    def get_nearest_locality(self):
        latitude, longitude = self.__location

        url = "http://overpass-api.de/api/interpreter"

        query = f"""
        [out:json];
        node(around:5000,{latitude},{longitude})["place"~"city|town|village"];
        out;
        """

        response = requests.get(url, data={"data": query})

        if response.status_code == 200:
            data = response.json()
            places = []

            for entry in data:
                if entry["tags"]["name"]:
                    place = {
                        "name": entry["tags"]["name"],
                        "distance": geodesic((latitude, longitude), (entry["lat"], entry["lon"])).meters
                    }
                    places.append(place)

            places.sort(key=lambda distance: distance["distance"])

            if places:
                return places[0]["name"]
            else:
                return "No nearby cities, towns, or villages found."

        else:
            print("Overpass API error:", response.status_code, response.text)
            return None

    def get_closest_fuel_station(self):
        latitude, longitude = self.__location
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
            closest_distance = INFINITE
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
                        distance = INFINITE

                    if element['name'] and distance < closest_distance:
                        closest_station = element['name']

            if not closest_station:
                return "No fuel stations found."
            else:
                return closest_station
        else:
            print("Overpass API error:", response.status_code, response.text)
            return None

    def get_speed(self):
        if INFINITE in self.__old_location:
            return 0

        distance = geodesic(self.__old_location, self.__location).meters

        time = 5 #in seconds

        speed = (distance / time) * 3.6 # converting to km/h

        return speed

    def get_speed_limit(self):
        latitude, longitude = self.__location
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
