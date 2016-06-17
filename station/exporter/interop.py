import requests
import ast
from time import time
import threading
import json
# baseurl = "http://10.10.130.43"
# username = "U_Alberta"
# password = "2689456278"
baseurl = "http://localhost"
username = "testuser"
password = "testpass"

from features import Marker
from .common import Exporter

import logging
logger = logging.getLogger(__name__)

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
            targetData = []
            for data_column in ["Type", "Orientation", "Shape", "Bkgnd_Color", "Alphanumeric", "Alpha_Color", "Notes"]:
                allocated = False
                for field in target.data: # Add all marker features we care about
                    key = field[0]
                    value = field[1]
                    if key == data_column:
                        allocated = True
                        if value == "": # Convert empty strings to None
                            value = None
                        targetData.append(value)
                if not allocated:
                    targetData.append("")

            if targetData[0] == "qrc" or targetData[0] == "emergent":
                target_data = {
                    "type": targetData[0],
                    "latitude": target.position.lat,
                    "longitude": target.position.lon,
                    "description": targetData[6]
                }

            elif targetData[0] == "off_axis":
                target_data = {
                    "type": targetData[0],
                    "orientation": targetData[1],
                    "shape": targetData[2],
                    "background_color": targetData[3],
                    "alphanumeric": targetData[4],
                    "alphanumeric_color": targetData[5],
                    "description": targetData[6]
                }

            else:
                target_data = {
                    "type": targetData[0],
                    "latitude": target.position.lat,
                    "longitude": target.position.lon,
                    "orientation": targetData[1],
                    "shape": targetData[2],
                    "background_color": targetData[3],
                    "alphanumeric": targetData[4],
                    "alphanumeric_color": targetData[5],
                    "description": targetData[6]
                }

            if 'interoperability' in target.external_refs:
                target_id = target.external_refs['interoperability']['id']
                self.interoplink.updateTarget(target_id, target_data)
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

    def submitTarget(self, target_data):
        """
        Uploads a new target to the interoperability server.
        Returns the ID assigned by the interop server upon successful upload.
        """
        response = self.s.post(baseurl + "/api/targets", json.dumps(target_data))

        if not response.status_code == requests.codes.created: # 201
            msg = "Target not created; server responded: {} {}".format(response.status_code, response.text)
            logger.error(msg)
            print(msg)
            return None

        # Parse response and get id
        response_dict = self.json_decoder.decode(response.text)
        target_id = response_dict['id']

        msg = "Target {} created: server responded: {}".format(target_id, response.text)
        logger.info(msg)
        print(msg)

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
            msg = "Image thumbnail not uploaded; server responded with code {}: {}".format(response.status_code, response.text)
            logger.error(msg)
            print(msg)
            return None

        msg = "Image thumbnail {} uploaded: server responded: {}".format(target_id, response.text)
        logger.info(msg)
        print(msg)

    def updateTarget(self, target_id, target_data):
        """
        Updates the data for a target whose information has already
        been uploaded to the interoperability server.
        """
        response = self.s.put(baseurl + "/api/targets/" + str(target_id), json.dumps(target_data))

        if not response.status_code == requests.codes.ok: # 200
            msg = "Target not updated; server responded with code {}: {}".format(response.status_code, response.text)
            logger.error(msg)
            print(msg)
            return None

        msg = "Target {} updated: server responded: {}".format(target_id, response.text)
        logger.info(msg)
        print(msg)
