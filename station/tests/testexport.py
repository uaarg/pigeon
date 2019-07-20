import unittest
import os
import requests

from exporter.interop_client_wrapper import InteropClientWrapper as InteropClient 
from auvsi_suas.proto import interop_api_pb2
import features
from geo import Position


#######################
# Main Configurations #
#######################

INTEROP_URL = "http://127.0.0.1:8000"

def can_connect_to_interop():
    """
    Check if we can reach the interop server
    """
    
    res = requests.get(INTEROP_URL)
    status_code = res.status_code
        
    if status_code == 200:
        # i.e. Don't Skip!
        return True
    else:
        return False

class FeatureTestCase(unittest.TestCase):

    def testOrientationConversion(self):
        exporter = InteropClient(init_client=False)
    
        res = exporter.odlc_conversion('Orientation', 'NW')
        self.assertEqual(res, interop_api_pb2.Odlc.NW)


    def testShapeConversion(self):
        exporter = InteropClient(init_client=False)
    
        res = exporter.odlc_conversion('Shape', 'circle')
        self.assertEqual(res, interop_api_pb2.Odlc.CIRCLE)

    def testColorConversion(self):
        exporter = InteropClient(init_client=False)
    
        res = exporter.odlc_conversion('Color', 'white')
        self.assertEqual(res, interop_api_pb2.Odlc.WHITE)

    def testInvalidConversions(self):
        exporter = InteropClient(init_client=False)
    
        res = exporter.odlc_conversion('DNE', 'DNE')
        self.assertEqual(res, None)


    def testFeatureConversion(self):
        """
        Tests whether a Feature can be converted to odlc type
        """
        exporter = InteropClient(init_client=False)
        
        # Input Feature
        test_feature = features.Feature()
        test_feature.position = Position(0, 0)

#        test_feature.data[0] = ('Name', 'Test_target')
        test_feature.data[1] = ('Type', 'standard')
        test_feature.data[2] = ('Shape', 'circle')
        test_feature.data[3] = ('Orientation', 'N')
        test_feature.data[4] = ('Bkgnd_Color', 'white')
        test_feature.data[5] = ('Alphanumeric', 'A')
        test_feature.data[6] = ('Alpha_Color', 'white')
#        test_feature.data[7] = ('Notes', 'Test target here.')

        # Create output odlc
        test_odlc = interop_api_pb2.Odlc()

        test_odlc.mission = 1
        test_odlc.latitude = 0
        test_odlc.longitude = 0
        test_odlc.type = interop_api_pb2.Odlc.STANDARD
        test_odlc.orientation = interop_api_pb2.Odlc.N 
        test_odlc.shape = interop_api_pb2.Odlc.CIRCLE 
        test_odlc.shape_color = interop_api_pb2.Odlc.WHITE
        test_odlc.alphanumeric = 'A' 
        test_odlc.alphanumeric_color = interop_api_pb2.Odlc.WHITE

        # Run the conversion 
        res_odlc = exporter.feature_to_odlc(test_feature)

        self.assertEqual(res_odlc, test_odlc)
