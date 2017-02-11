import requests
import ast
from time import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtCore import QRect, QPoint

from . import interop
# baseurl = "http://10.10.130.43"
# username = "U_Alberta"
# password = "2689456278"
baseurl = "http://localhost:8000"
username = "testuser"
password = "testpass"

from features import Marker
from .common import Exporter

import logging
logger = logging.getLogger(__name__)

class InteropClientV2(Exporter):
    """Newer version that uses the provided library rather than rolling
    our own."""
    def __init__(self, username, password):
        self.path = None
        self.client = interop.AsyncClient(username, password, timeout=1, workers=8)
    
    def export(self, raw_target, path):
        self.path = path + "interopSent.json"
        targets = [target for target in raw_target if isinstance(feature, Marker)]
        processed_targets = []
        for target in targets:
            processed_targets.append(self.process_target(target))
        for target in processed_targets:
            self.send_target(target)

    def process_target(self, raw_target):
        """Processes relevant data into target objects"""
        targetData = []
        for data_column in ["Type", "Orientation", "Shape", "Bkgnd_Color", "Alphanumeric", "Alpha_Color", "Notes"]:
            allocated = False
            for field in raw_target.data: # Add all marker features we care about
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
            target = interop.types.Target(
                type = targetData[0],
                latitude = target.position.lat,
                longitude = target.position.lon,
                description = targetData[6]
            )
        elif targetData[0] == "off_axis":
            target = interop.types.Target(
                type = targetData[0],
                orientation = targetData[1],
                shape = targetData[2],
                background_color = targetData[3],
                alphanumeric = targetData[4],
                alphanumeric_color = targetData[5],
                description = targetData[6]
            )
        else:
            target = interop.types.Target(
                type = targetData[0],
                latitude = target.position.lat,
                longitude = target.position.lon,
                orientation = targetData[1],
                shape = targetData[2],
                background_color = targetData[3],
                alphanumeric = targetData[4],
                alphanumeric_color = targetData[5],
                description = targetData[6]
            )
        return target
        
    def send_target(self, raw_target):
        """Sends target data using the async interop library."""
        if 'interoperability' in raw_target.external_refs:
            target_id = raw_target.external_refs['interoperability']['id']
            # update target
            try:
                self.client.put_target(target_id, target)
            except interop.InteropError:
                msg = "Target {} update error: interop.InteropError".format(target_id)
                logger.critical(msg)
                print(msg)
                return
            except requests.Timeout:
                msg = "Target {} update error: requests.Timeout".format(target_id)
                logger.critical(msg)
                print(msg)
                return
            except ValueError or AttributeError:
                msg = "Target {} update error: Malformed response from server".format(target_id)
                logger.critical(msg)
                print(msg)
                return
            except:
                msg = "Target {} update error: Unanticipated error".format(target_id)
                logger.critical(msg)
                print(msg)
                return
            msg = "Target {} updated successfully".format(target_id)
            logger.info(msg)
            print(msg)
        else:
            # upload target
            try:
                returned_target = self.client.post_target(target).result()
            except interop.InteropError:
                msg = "Target {} upload error: interop.InteropError".format(target_id)
                logger.critical(msg)
                print(msg)
                return
            except requests.Timeout:
                msg = "Target {} upload error: requests.Timeout".format(target_id)
                logger.critical(msg)
                print(msg)
                return
            except ValueError or AttributeError:
                msg = "Target {} upload error: Malformed response from server".format(target_id)
                logger.critical(msg)
                print(msg)
                return
            except:
                msg = "Target {} upload error: Unanticipated error".format(target_id)
                logger.critical(msg)
                print(msg)
                return
            target_id = returned_target.id
            msg = "Target {} uploaded successfully".format(target_id)
            logger.info(msg)
            print(msg)
            raw_target.external_refs['interoperability'] = {}
            raw_target.external_refs['interoperability']['id'] = target_id
            raw_target.picture.save('target.jpg')
            # upload image
            with open(image_path, 'rb') as image_data:
                try:
                    self.client.post_target_image(target_id, image_data)
                except interop.InteropError:
                    msg = "Target {} thumbnail upload error: interop.InteropError".format(target_id)
                    logger.critical(msg)
                    print(msg)
                    return
                except requests.Timeout:
                    msg = "Target {} thumbnail upload error: requests.Timeout".format(target_id)
                    logger.critical(msg)
                    print(msg)
                    return
                except:
                    msg = "Target {} thumbnail upload error: Unanticipated error".format(target_id)
                    logger.critical(msg)
                    print(msg)
                    return
                msg = "Image thumbnail {} uploaded successfully".format(target_id)
                logger.info(msg)
                print(msg)

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
