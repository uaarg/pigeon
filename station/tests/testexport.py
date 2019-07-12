import unittest
import os
import requests

import exporter
from auvsi_suas.proto import interop_api_pb2

#######################
# Main Configurations #
#######################

INTEROP_URL = "http://127.0.0.1:8000"

def test_interop():
    """
    Check if we can reach the interop server
    """
    
    res = requests.get(INTEROP_URL)
    status_code = res.status_code
        
    if status_code == 200:
        # i.e. Don't Skip!
        return False
    else:
        return True

@unittest.skipIf(test_interop(), "Could not connect to interop.")
class FeatureTestCase(unittest.TestCase):
    def test(self):
        print(test_interop)
        self.assertEqual(1,1)
            
