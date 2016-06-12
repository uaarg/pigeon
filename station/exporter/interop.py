import requests
import ast
from time import time
import threading
import json
baseurl = "http://localhost"
username = "testuser"
password = "testpass"

from features import Marker

from .common import Exporter

class InteropClient(Exporter):
    def __init__(self):
        self.path = None

    def export(self, features, path):
        self.path = path + "interopSent.json"
        self.sendData([feature for feature in features if isinstance(feature, Marker)])

    def sendData(self, rawdata):
        self.rawdata = rawdata
        self.interopTH = threading.Thread(target = self.runner)
        self.interopTH.start()

    def runner(self):
        self.interoplink = Connection()
        for target in self.rawdata:
            target_data = {
                # 'type':str(target.type),
                # 'latitude':float(target.lon),
                # 'longitude':float(target.lon),
                # 'orientation':str(target.orentation),
                # 'shape':str(target.shape),
                # 'background_color':str(target.bgcolor),
                # 'alphanumeric':str(target.alphanumeric),
                # 'alphanumeric_color':str(target.alphanumeric_color)
                "type": "standard",
                "latitude": 38.1478,
                "longitude": -76.4275,
                "orientation": "n",
                "shape": "star",
                "background_color": "orange",
                "alphanumeric": "X",
                "alphanumeric_color": "black"
            }

            if 'interoperability' in target.external_refs:
                target_id = target.external_refs['interoperability']['id']
                target_data = target.external_refs['interoperability']
                self.interoplink.updateTarget(target_data, target_id)
            else:
                target_id = self.interoplink.submitTarget(target_data)
                if target_id:
                    target.external_refs['interoperability'] = {}
                    target.external_refs['interoperability']['id'] = target_id
                    target.picture.save('target.jpg')
                    self.interoplink.submitTargetThumbnail(target_id, 'target.jpg')

class Connection:
    def __init__(self):
        self.loginsucess = False
        self.s = requests.Session()
        self.lasttele = 0
        self.json_decoder = json.JSONDecoder()
        data = {"username": username, "password": password}
        loginurl = "/api/login"
        try:
            self.login = self.s.post(baseurl + loginurl, data=data)
            self.loginsucess = True
            pass
        except requests.exceptions.ConnectionError as e:
            print("Failed to login to interop server")
            pass

    def getobstacleinfo(self):
        ob = self.s.get(baseurl + "/api/obstacles")
        objects = ast.literal_eval(ob.text)
        return objects

    def updatetelemetry(self, tele):
        tl = self.s.post(baseurl + "/api/telemetry", tele)
        print(tl.status_code)

    def submitTarget(self, target_data):
        """
        Uploads a new target to the interoperability server.
        Returns the ID assigned by the interop server upon successful upload.
        """
        response = self.s.post(baseurl + "/api/targets", json.dumps(target_data))

        if not response.status_code == requests.codes.created: # 201
            print("Target not created; server responded: {} {}".format(response.status_code, response.text))
            return None

        # Parse response and get id
        response_dict = self.json_decoder.decode(response.text)
        target_id = response_dict['id']

        return target_id

    def submitTargetThumbnail(self, target_id, image_path):
        """
        Uploads a target image thumbnail to the interoperability server,
        for the given target ID.
        """

        thumbnail_url = baseurl + "/api/targets/" + str(target_id) + "/image"
        
        # Upload thumbnail
        with open(image_path, 'rb') as image_data:
            response = self.s.post(thumbnail_url, image_data)

        if not response.status_code == requests.codes.ok: # 200
            print("Image thumbnail not uploaded; server responded: {} {}".format(response.status_code, response.text))
            return None

    def updateTarget(self, target_data, target_id):
        """
        Updates the data for a target whose information has already
        been uploaded to the interoperability server.
        """
        response = self.s.put(baseurl + "/api/targets/" + str(target_id), json.dumps(target_data))

        if not response.status_code == requests.codes.ok: # 200
            print("Target not updated; server responded: {} {}".format(response.status_code, response.text))
            return None
