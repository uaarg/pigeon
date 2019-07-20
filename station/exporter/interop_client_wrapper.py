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

# Conversion LUTs
# ===============

# Data conversions mapping from strings to protobuff
# Idea is to pass type value to get interop protobuff version
# e.g. orientation_conversion[data['orientation']
ORIENTATION_CONVERSION = {
    'N' : interop_api_pb2.Odlc.N,
    'NE' : interop_api_pb2.Odlc.NE,
    'E' : interop_api_pb2.Odlc.E,
    'SE' : interop_api_pb2.Odlc.SE,
    'S' : interop_api_pb2.Odlc.S,
    'SW' : interop_api_pb2.Odlc.SW,
    'W' : interop_api_pb2.Odlc.W,
    'NW' : interop_api_pb2.Odlc.NW,
}

SHAPE_CONVERSIONS = {
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

COLOR_CONVERSIONS = {
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
    def __init__(self, init_client=True):
        """ 
        Class constructor
        Params:
            init_client (Bool) : Whether to initialize interop client or not
                                 Setting to false will not allow this to export
        """
        self.path = None

        # Construct the AsyncClient object provided by AUVSI
        if (init_client):
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
                try:
                    odlc = self.feature_to_odlc(feature)
                except Exception as e:
                    # Specific Error messages printed in above function
                    # ... So print this generic one instead
                    msg = ("Error occured during feature conversion "
                           "for feature `{}`. Skipping...").format(feature.data[0][1])
                    logger.critical(msg)
                    logger.critical(e)
                else:
                    # Send only if no errors during covnersion
                    self.send_target(feature)

        msg = "Finished Interop Export Task"
        print(msg)

    def odlc_conversion(self, field_type, value):
        """
        Converts an enum value stored in a feature to the enum value used
        in a protobuff class
        ASSUMES VALUE EXISTS IN CONVERSION LUTS!!

        Parameters:
            field_type (string) : The key/type of the field in a feature
                            Valid Values are:
                                - Orientation
                                - Shape
                                - Color
            value (str)   : The value of the field in a feature
                            e.g. NW, NE, RED BLUE
        
        Return:
            (interop_api_pb2.Odlc.*) : The protobuff conversion
        """
        try:
            if field_type == 'Orientation':
                return ORIENTATION_CONVERSION[value]

            elif field_type == 'Shape':
                return SHAPE_CONVERSIONS[value]

            elif field_type == 'Color':
                return COLOR_CONVERSIONS[value]

        except (TypeError, KeyError) as e:
            msg = ("Invalid Field Value for {} in an export. "
                "Make sure features have all fields filled out").format(field_type)
            logger.critical(msg)
            raise e

        except Exception as e:
            msg = "Unexpected exception while converting ennums: " + str(e)
            logger.critical(msg)
            raise e
        
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

        odlc = interop_api_pb2.Odlc()

        lat = feature.position.lat
        lon = feature.position.lon

        # Get dictionary representation of data
        data = feature.data_as_dict()
        target_type = data["Type"]

        # Standard and off axis ODLCs take latitude, longitude, orientation,
        # shape and color, alphanumeric and color. 
        # Emergent takes latitude, longitude, description, and if process
        # autonomously.
        # Note, we don't include if processed auto as it defaults false

        # Cases for different target types
        if target_type == 'standard':
            odlc.type = interop_api_pb2.Odlc.STANDARD
            odlc.latitude = lat
            odlc.longitude = lon

            odlc.orientation = self.odlc_conversion('Orientation', data['Orientation'])

            odlc.shape = self.odlc_conversion('Shape', data['Shape'])

            odlc.shape_color = self.odlc_conversion('Color', data['Bkgnd_Color'])
            
            odlc.alphanumeric = data['Alphanumeric']

            odlc.alphanumeric_color = self.odlc_conversion(
                'Color', data['Alpha_Color'])

            odlc.mission = MISSION_ID;

        elif target_type == 'off_axis':
            odlc.type = interop_api_pb2.Odlc.off_axis
            odlc.latitude = lat
            odlc.longitude = lon

            odlc.orientation = self.odlc_conversion('Orientation', data['Orientation'])

            odlc.shape = self.odlc_conversion('Shape', data['Shape'])

            odlc.shape_color = self.odlc_conversion('Color', data['Bkgnd_Color'])
            
            odlc.alphanumeric = data['Alphanumeric']

            odlc.alphanumeric_color = self.odlc_conversion(
                'Color', data['Alpha_Color'])

            odlc.mission = MISSION_ID;
        
        elif target_type == 'emergent':
            odlc.type = interop_api_pb2.Odlc.EMERGENT
            odlc.latitude = lat
            odlc.longitude = lon

            odlc.description = data['Notes']

            odlc.mission = MISSION_ID;

        else:
            msg = "Feature `{}` has Target Type `{}` which has no defined export".format(
                    data['Name'], target_type)
            logger.critical(msg)

            raise(NotImplementedError())

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
