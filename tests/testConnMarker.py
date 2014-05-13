# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import unittest

from ConnMarker import ConnMarker

class ConnMarkerTest(unittest.TestCase):
    def setUp(self):
        self.connMarker = ConnMarker(None)
        self.assertNotEqual(self.connMarker, None)

    def testAddress(self):
        self.assertEqual(self.connMarker.setAddress(None), None)
        self.assertEqual(self.connMarker.getAddress(), None)

        self.assertEqual(self.connMarker.setAddress('http://127.0.0.1'), None)
        self.assertEqual(self.connMarker.getAddress(), 'http://127.0.0.1/markerHandler')

    def testAttrManifestSetting(self):
        self.assertEqual(self.connMarker.setAttrManifestDict({}), True)
        self.assertEqual(self.connMarker.setAttrManifestDict(None), False)
        __manifestRules = dict(put=['x', 'y', 'z', 'phi', 'psi'])
        self.assertEqual(self.connMarker.setAttrManifestDict(__manifestRules), True)
        self.assertEqual(self.connMarker.getAttrManifestDict(), __manifestRules)

    def testGetAttrSetting(self):
        __getAttrs = ['x', 'y', 'select', 'associatedImage_id', 'id']
        self.assertEqual(self.connMarker.setAttrManifestDict(dict(get=__getAttrs)), True)

        __screenedVars =self.connMarker.filterForRestGet(dict(x=10, y=24.0, associatedImage_id=24, id=235, associatedRange_id=25))
        self.assertNotEqual(None, __screenedVars)
        self.assertEqual(hasattr(__screenedVars, 'keys'), True)
        self.assertNotEqual(list(__screenedVars.keys()), __getAttrs)
        self.assertNotIn('associatedRange_id', __screenedVars)

    def testPutAttrSetting(self):
        __putAttrs = ['x', 'y', 'select', 'associatedImage_id', 'associatedRange_id']
        self.assertEqual(self.connMarker.setAttrManifestDict(dict(put=__putAttrs)), True)

        __screenedVars =self.connMarker.filterForRestPut(dict(x=10, y=24.0, associatedImage_id=24, id=76, associatedRange_id=25))
        self.assertNotEqual(None, __screenedVars)
        self.assertEqual(hasattr(__screenedVars, 'keys'), True)
        self.assertNotEqual(list(__screenedVars.keys()), __putAttrs)
        self.assertNotIn('id', __screenedVars)

    def testPostAttrSetting(self):
        __postAttrs = ['x', 'y', 'select', 'associatedImage_id', 'associatedRange_id']
        self.assertEqual(self.connMarker.setAttrManifestDict(dict(post=__postAttrs)), True)

        __screenedVars = self.connMarker.filterForRestPost(dict(y=94, associatedImage_id=23, id=59, associatedRange_id=28))
        self.assertNotEqual(None, __screenedVars)
        self.assertEqual(hasattr(__screenedVars, 'keys'), True)
        self.assertNotEqual(list(__screenedVars.keys()), __postAttrs)

        self.assertNotIn('x', __screenedVars) # Legal variable but was not included in the attribute dict
        self.assertNotIn('id', __screenedVars)

    def testDeleteAttrSetting(self):
        __deleteAttrs = ['x', 'y', 'id']
        self.assertEqual(self.connMarker.setAttrManifestDict(dict(delete=__deleteAttrs)), True)

        __screenedVars = self.connMarker.filterForRestDelete(dict(x=12, associatedImage_id=45, id=13))
        self.assertNotEqual(None, __screenedVars)
        self.assertEqual(hasattr(__screenedVars, 'keys'), True)
        self.assertNotEqual(list(__screenedVars.keys()), __deleteAttrs)

        self.assertNotIn('y', __screenedVars)
        self.assertNotIn('associatedImage_id', __screenedVars)

    def testDBLiason(self):
        self.assertEqual(self.connMarker.initDBLiason(), True)
        __1stDbLiason = self.connMarker.getDBLiason()
        self.assertNotEqual(__1stDbLiason, None)

        self.assertEqual(self.connMarker.setConnectedAddress('http://127.0.0.1'), True)
        __2ndDbLiason = self.connMarker.getDBLiason()
        self.assertNotEqual(__2ndDbLiason, None)

        self.assertNotEqual(__1stDbLiason, __2ndDbLiason)

    def testCrossNetConnections(self):
        self.assertEqual(self.connMarker.setConnectedAddress('http://127.0.0.1:8000/gcs/'), True)
        self.assertEqual(self.connMarker.getAddress(), 'http://127.0.0.1:8000/gcs/markerHandler')
       
        markerData = dict(x=25.5, y=98.1, author=os.environ.get('USERNAME', 'Anonymous'), comments='Testing one')

        postResult = self.connMarker.postConn(markerData)
        print('postResult', postResult)

        getResult = self.connMarker.getConn(markerData)
        print('getResult', getResult)

        putResult  = self.connMarker.putConn(markerData)
        # Requiring an id for an update/put
        dataReturned = getResult.get('value', {}).get('data', [{}])
        if dataReturned:
            queriedId = dataReturned[0].get('id', -1)
            if queriedId != -1:
                markerData['id'] =  queriedId
            print('putResult', putResult)

        deleteResult = self.connMarker.deleteConn(markerData)
        print('deleteResult', deleteResult)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
