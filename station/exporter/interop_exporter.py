import requests
import ast
import random
from time import time
import threading
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtCore import QRect, QPoint

from . import interop
# baseurl = "http://10.10.130.43"
# username = "U_Alberta"
# password = "2689456278"
baseurl = "http://10.10.130.10:80"
username = "alberta"
password = "1681866885"

from features import Marker
from .common import Exporter

import logging
logger = logging.getLogger(__name__)

def process_target(feature):
    """Processes relevant data into target objects"""
    targetData = []
    for data_column in ["Type", "Orientation", "Shape", "Bkgnd_Color", "Alphanumeric", "Alpha_Color", "Notes"]:
        allocated = False
        for field in feature.data: # Add all marker features we care about
            key = field[0]
            value = field[1]
            if key == data_column:
                allocated = True
                if value == "": # Convert empty strings to None
                    value = None
                targetData.append(value)
        if not allocated:
            targetData.append("")
        lat = feature.position.lat
        lon = feature.position.lon
    if targetData[0] == "qrc" or targetData[0] == "emergent":
        interop_target = interop.interop_types.Target(
            type = targetData[0],
            latitude = lat,
            longitude = lon,
            description = targetData[6]
        )
    elif targetData[0] == "off_axis":
        interop_target = interop.interop_types.Target(
            type = targetData[0],
            orientation = targetData[1],
            shape = targetData[2],
            background_color = targetData[3],
            alphanumeric = targetData[4],
            alphanumeric_color = targetData[5],
            description = targetData[6]
        )
    elif targetData[0] == "standard":
        interop_target = interop.interop_types.Target(
            type = targetData[0],
            latitude = lat,
            longitude = lon,
            orientation = targetData[1],
            shape = targetData[2],
            background_color = targetData[3],
            alphanumeric = targetData[4],
            alphanumeric_color = targetData[5],
            description = targetData[6]
        )
    else:
        msg = "Invalid feature/target type!"
        msg = logger.critical(msg)
        feature.external_refs['interop_target'] = None
        return
    feature.external_refs['interop_target'] = interop_target

class AUVSIJSONExporter(Exporter):
    def export(self, features, output_path):
        self.writeObjectFiles([feature for feature in features if isinstance(feature, Marker)], output_path)

    def writeObjectFiles(self, features, output_path):
        current_id = 1
        for feature in features:
            process_target(feature)

            json_path = os.path.join(output_path, str(current_id) + ".json")
            with open(json_path, 'w') as f:
                json.dump(feature.external_refs['interop_target'].serialize(), f)

            image_path = os.path.join(output_path, str(current_id) + ".jpg")
            feature.thumbnail.save(image_path)

            current_id += 1



class InteropClientV2(Exporter):
    """Newer version that uses the provided library rather than rolling
    our own."""
    def __init__(self):
        self.path = None
        self.client = interop.AsyncClient(baseurl, username, password, timeout=50)
    
    def export(self, features, path):
        self.path = path + "interopSent.json"
        self.features = features
        for feature in self.features:
            if isinstance(feature, Marker):
                process_target(feature)
                self.send_target(feature)


        
    def send_target(self, feature):
        """Sends target data using the interop client library."""
        if 'interoperability' in feature.external_refs:
            target_id = feature.external_refs['interoperability']['id']
            # update target
            try:
                response = self.client.put_target(target_id, feature.external_refs['interop_target']).result()
            except Exception as exception:
                name = type(exception).__name__
                detail = exception.args[0]
                msg = "Target {0} update error: {1}: {2}".format(target_id, name, detail)
                logger.critical(msg)
                return
            else:
                msg = "Target {} updated successfully".format(target_id)
                logger.info(msg)
                print(msg)
        else:
            # upload target
            try:
                returned_target = self.client.post_target(feature.external_refs['interop_target']).result()
            except Exception as exception:
                name = type(exception).__name__
                detail = exception.args[0]
                msg = "New target upload error: {0}: {1}".format(name, detail)
                logger.critical(msg)
                target_id = int(random.random() * 100)
                return
            else:
                target_id = returned_target.id
                msg = "Target {} uploaded successfully".format(target_id)
                logger.info(msg)
                print(msg)
                feature.external_refs['interoperability'] = {}
                feature.external_refs['interoperability']['id'] = target_id
                feature.thumbnail.save('target.jpg')
                # upload image
                image_path = 'target.jpg'
                with open(image_path, 'rb') as image_data:
                    try:
                        response = self.client.post_target_image(target_id, image_data).result()
                    except Exception as exception:
                        name = type(exception).__name__
                        detail = exception.args[0]
                        msg = "Target {0} thumbnail upload error: {1}: {2}".format(target_id, name, detail)
                        logger.critical(msg)
                        return
                    else:
                        msg = "Image thumbnail {} uploaded successfully".format(target_id)
                        logger.info(msg)
                        print(msg)

            target_json = features.external_refs['interop_target'].serialize()
            with open(json_path, 'w') as f:
                json.dump(target_json, f)

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

                    target.thumbnail.save('target.jpg')
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
        response = self.s.post(baseurl + "/api/odlcs", json.dumps(target_data))

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

        thumbnail_url = baseurl + "/api/odlcs/" + str(target_id) + "/image"

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
        response = self.s.put(baseurl + "/api/odlcs/" + str(target_id), json.dumps(target_data))

        if not response.status_code == requests.codes.ok: # 200
            msg = "Target not updated; server responded with code {}: {}".format(response.status_code, response.text)
            logger.error(msg)
            print(msg)
            return None

        msg = "Target {} updated: server responded: {}".format(target_id, response.text)
        logger.info(msg)
        print(msg)
