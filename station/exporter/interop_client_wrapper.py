import requests
import random
import json

from features import Marker
from .common import Exporter

# Interop Client
from auvsi_suas.client.client import AsyncClient
# Interop Data Types
from auvsi_suas.proto import interop_api_pb2

# Serializing our responses to json
from google.protobuf.json_format import MessageToJson


# Credential Configuration 
# ========================

# baseurl = "http://10.10.130.43"
# username = "U_Alberta"
# password = "2689456278"
BASEURL = "http://127.0.0.1:8000"
USERNAME = "testuser"
PASSWORD = "testpass"
MISSION_ID = 1

# Logging
# =======

import logging
logger = logging.getLogger(__name__)

# =============================================

class InteropClientWrapper(Exporter):
    """
    Wrapper for the Interop Client library provided by AUVSI
    Allows the client library to interface properly to our export systems
    """
    def __init__(self):
        """ 
        Class constructor
        Params: None
        """
        self.path = None

        # Construct the AsyncClient object provided by AUVSI
        self.client = AsyncClient(BASEURL, USERNAME, PASSWORD)
    
    def export(self, features, path):
        """
        Exports each feature provided in feeatures to the interop
        """
        self.path = path + "/interopSent.json"
        self.features = features
        for feature in self.features:
            if isinstance(feature, Marker):
                # Map the feature's data to the ODLC class provided by interop
                odlc = self.feature_to_odlc(feature)
                self.send_target(feature)

    def feature_to_odlc(self, feature):
        """ 
        Reads the data provided in feature and converts in into the 
        the protobuff representation used in the AUVSI interop client Library
        The ODLC returned should be passed into client.post_odlc

        Parameters:
            feature (features.Feature) : A feature with data

        Returns: 
            (interop_api_pb2.Odlc) : ODLC representation of feature

        Note, the returned odlc object is also attatched as an external ref
        in the features objects. 
        Access it with feature.external_refs['interop_target']
        """

        # Data conversions mapping from strings to protobuff
        # Idea is to pass type value to get interop protobuff version
        # e.g. orientation_conversion[data['orientation']
        orientation_conversion = {
            'N' : interop_api_pb2.Odlc.N,
            'NE' : interop_api_pb2.Odlc.NE,
            'E' : interop_api_pb2.Odlc.E,
            'SE' : interop_api_pb2.Odlc.SE,
            'S' : interop_api_pb2.Odlc.S,
            'SW' : interop_api_pb2.Odlc.SW,
            'W' : interop_api_pb2.Odlc.W,
            'NW' : interop_api_pb2.Odlc.NW,
        }

        shape_conversions = {
            "circle" :  interop_api_pb2.Odlc.CIRCLE,
            "semicircle" :  interop_api_pb2.Odlc.SEMICIRCLE,
            "quarter_circle" :  interop_api_pb2.Odlc.QUARTER_CIRCLE,
            "triangle" :  interop_api_pb2.Odlc.TRIANGLE,
            "square" :  interop_api_pb2.Odlc.SQUARE,
            "rectangle" :  interop_api_pb2.Odlc.RECTANGLE,
            "trapezoid" :  interop_api_pb2.Odlc.TRAPEZOID,
            "pentagon" :  interop_api_pb2.Odlc.PENTAGON,
            "hexagon" :  interop_api_pb2.Odlc.HEXAGON,
            "heptagon" :  interop_api_pb2.Odlc.HEPTAGON,
            "octagon" :  interop_api_pb2.Odlc.OCTAGON,
            "star" :  interop_api_pb2.Odlc.STAR,
            "cross" :  interop_api_pb2.Odlc.CROSS,
        }

        color_conversions = {
            "white" : interop_api_pb2.Odlc.WHITE,
            "black" : interop_api_pb2.Odlc.BLACK,
            "gray" : interop_api_pb2.Odlc.GRAY,
            "red" : interop_api_pb2.Odlc.RED,
            "blue" : interop_api_pb2.Odlc.BLUE,
            "green" : interop_api_pb2.Odlc.GREEN,
            "yellow" : interop_api_pb2.Odlc.YELLOW,
            "purple" : interop_api_pb2.Odlc.PURPLE,
            "brown" : interop_api_pb2.Odlc.BROWN,
            "orange" : interop_api_pb2.Odlc.ORANGE,
        }

        odlc = interop_api_pb2.Odlc()

        lat = feature.position.lat
        lon = feature.position.lon

        # Get dictionary representation of data
        data = feature.data_as_dict()
        target_type = data["Type"]

        # Standard and off axis ODLCs take latitude, longitude, orientation,
        # shape and color, alphanumeric and color. 
        # Note, we don't include if processed auto as it defaults false

        # Cases for different target types
        if target_type == 'standard':
            odlc.type = interop_api_pb2.Odlc.STANDARD
            odlc.latitude = lat
            odlc.longitude = lon
            odlc.orientation = orientation_conversion[data['Orientation']]
            odlc.shape = shape_conversions[data['Shape']]
            odlc.shape_color = color_conversions[data['Bkgnd_Color']]
            odlc.alphanumeric = data['Alphanumeric']
            odlc.alphanumeric_color = color_conversions[data['Alpha_Color']]
            odlc.mission = MISSION_ID;

        elif target_type == 'emergent':
            raise(NotImplementedError())

        elif target_type == 'off_axis':
            raise(NotImplementedError())

        else:
            msg = "Target Type {} has no defined export".format(target_type)
            logger.critical(msg)
            # No reference to odlc
            odlc = None

        feature.external_refs['interop_target'] = odlc
        return odlc

        
    def send_target(self, feature):
        """
        Sends target data using the interop client library.
        Parameters:
            feature (features.Feature) : The feature to send

        Note that feature should contain external reference to odlc object 
        created by feature_to_odlc
        """

        # Only send items marked to be exported to interop
        if 'interoperability' in feature.external_refs:
            target_id = feature.external_refs['interoperability']['id']
            
            # Update target first if exists already. Note image is not updated
            try:
                response = self.client.put_odlc(
                    target_id, feature.external_refs['interop_target']).result()
            except Exception as exception:
                name = type(exception).__name__
                detail = exception.args[0]
                msg = "Target {0} update error: {1}: {2}".format(target_id, name, detail)
                logger.critical(msg)
                return
            else:
                msg = "Target {} updated successfully".format(target_id)
                logger.info(msg)
        else:
            # Upload target
            try:
                returned_target = self.client.post_odlc(
                    feature.external_refs['interop_target']).result()

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

                feature.external_refs['interoperability'] = {}
                feature.external_refs['interoperability']['id'] = target_id
                feature.thumbnail.save('target.jpg')

                # Upload image
                image_path = 'target.jpg'
                with open(image_path, 'rb') as image_data:
                    try:
                        response = self.client.put_odlc_image(
                            target_id, image_data).result()
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

            target_json = MessageToJson(feature.external_refs['interop_target'])
            
            # Note we create a file if doesn't exist
            with open(self.path, 'w+') as f:
                json.dump(target_json, f)