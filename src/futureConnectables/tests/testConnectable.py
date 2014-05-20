# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import unittest

from Connectable import Connectable

class BaseTestCase(unittest.TestCase):
    def assertTruez(self):
        print(self)

class ConnectableTests(BaseTestCase):
    def setUp(self):
        self.connectableObj = Connectable(None)
        self.assertNotEqual(self.connectableObj, None)

    def testAddress(self):
        self.assertEqual(self.connectableObj.setAddress(None), None)
        self.assertEqual(self.connectableObj.getAddress(), None)

        self.assertEqual(self.connectableObj.setAddress('http://127.0.0.1'), None)
        self.assertEqual(self.connectableObj.getAddress(), 'http://127.0.0.1')

    def testAttrManifestSetting(self):
        self.assertEqual(self.connectableObj.setAttrManifestDict({}), True)
        self.assertEqual(self.connectableObj.setAttrManifestDict(None), False)
        __manifestRules = dict(put=['x', 'y', 'z', 'phi', 'psi'])
        self.assertEqual(self.connectableObj.setAttrManifestDict(__manifestRules), True)
        self.assertEqual(self.connectableObj.getAttrManifestDict(), __manifestRules)

    def testGetAttrSetting(self):
        __getAttrs = ['x', 'y', 'select', 'associatedImage_id', 'id']
        self.assertEqual(self.connectableObj.setAttrManifestDict(dict(get=__getAttrs)), True)

        __screenedVars =self.connectableObj.filterForRestGet(dict(x=10, y=24.0, associatedImage_id=24, id=235, associatedRange_id=25))
        self.assertNotEqual(None, __screenedVars)
        self.assertEqual(hasattr(__screenedVars, 'keys'), True)
        self.assertNotEqual(list(__screenedVars.keys()), __getAttrs)
        self.assertNotIn('associatedRange_id', __screenedVars)

    def testPutAttrSetting(self):
        __putAttrs = ['x', 'y', 'select', 'associatedImage_id', 'associatedRange_id']
        self.assertEqual(self.connectableObj.setAttrManifestDict(dict(put=__putAttrs)), True)

        __screenedVars =self.connectableObj.filterForRestPut(dict(x=10, y=24.0, associatedImage_id=24, id=76, associatedRange_id=25))
        self.assertNotEqual(None, __screenedVars)
        self.assertEqual(hasattr(__screenedVars, 'keys'), True)
        self.assertNotEqual(list(__screenedVars.keys()), __putAttrs)
        self.assertNotIn('id', __screenedVars)

    def testPostAttrSetting(self):
        __postAttrs = ['x', 'y', 'select', 'associatedImage_id', 'associatedRange_id']
        self.assertEqual(self.connectableObj.setAttrManifestDict(dict(post=__postAttrs)), True)

        __screenedVars = self.connectableObj.filterForRestPost(dict(y=94, associatedImage_id=23, id=59, associatedRange_id=28))
        self.assertNotEqual(None, __screenedVars)
        self.assertEqual(hasattr(__screenedVars, 'keys'), True)
        self.assertNotEqual(list(__screenedVars.keys()), __postAttrs)

        self.assertNotIn('x', __screenedVars) # Legal variable but was not included in the attribute dict
        self.assertNotIn('id', __screenedVars)

    def testDeleteAttrSetting(self):
        __deleteAttrs = ['x', 'y', 'id']
        self.assertEqual(self.connectableObj.setAttrManifestDict(dict(delete=__deleteAttrs)), True)

        __screenedVars = self.connectableObj.filterForRestDelete(dict(x=12, associatedImage_id=45, id=13))
        self.assertNotEqual(None, __screenedVars)
        self.assertEqual(hasattr(__screenedVars, 'keys'), True)
        self.assertNotEqual(list(__screenedVars.keys()), __deleteAttrs)

        self.assertNotIn('y', __screenedVars)
        self.assertNotIn('associatedImage_id', __screenedVars)

    def testDBLiason(self):
        self.assertEqual(self.connectableObj.initDBLiason(), True)
        __1stDbLiason = self.connectableObj.getDBLiason()
        self.assertNotEqual(__1stDbLiason, None)

        self.assertEqual(self.connectableObj.setConnectedAddress('http://127.0.0.1'), True)
        __2ndDbLiason = self.connectableObj.getDBLiason()
        self.assertNotEqual(__2ndDbLiason, None)

        self.assertNotEqual(__1stDbLiason, __2ndDbLiason)

    def testCrossNetConnections(self):
        limitRules =dict(
            post=['title', 'author', 'uri', 'phi', 'psi', 'alt'], put=['title', 'author', 'uri', 'phi', 'psi', 'alt'],
            get=['title', 'select', 'uri', 'id', 'format', 'psi', 'phi'], delete=['title', 'author', 'id', 'uri', 'alt']
        )
        self.assertEqual(self.connectableObj.setAttrManifestDict(limitRules), True)
        self.assertEqual(self.connectableObj.setConnectedAddress('http://127.0.0.1:8000/gcs/imageHandler'), True)
        self.assertEqual(self.connectableObj.getAddress(), 'http://127.0.0.1:8000/gcs/imageHandler')
       
        imageData = dict(author=os.environ.get('USERNAME', 'Anonymous'), phi=-0.257, title='TestImageHere') 

        postResult = self.connectableObj.postConn(imageData)
        print('postResult', postResult)

        getResult = self.connectableObj.getConn(imageData)
        print('getResult', getResult)

        putResult  = self.connectableObj.putConn(imageData)
        # Requiring an id for an update/put
        queriedId = getResult.get('value', {}).get('data', [{}])[0].get('id', -1)
        if queriedId != -1:
            imageData['id'] =  queriedId
        print('putResult', putResult)

        deleteResult = self.connectableObj.deleteConn(imageData)
        print('deleteResult', deleteResult)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
