# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import unittest

from ConnImage import ConnImage

class ConnImageTest(unittest.TestCase):
    def setUp(self):
        self.connImage = ConnImage(None)
        self.assertNotEqual(self.connImage, None)

    def testAddress(self):
        self.assertEqual(self.connImage.setAddress(None), None)
        self.assertEqual(self.connImage.getAddress(), None)

        self.assertEqual(self.connImage.setAddress('http://127.0.0.1'), None)
        self.assertEqual(self.connImage.getAddress(), 'http://127.0.0.1/imageHandler')

    def testAttrManifestSetting(self):
        self.assertEqual(self.connImage.setAttrManifestDict({}), True)
        self.assertEqual(self.connImage.setAttrManifestDict(None), False)
        __manifestRules = dict(put=['x', 'y', 'z', 'phi', 'psi'])
        self.assertEqual(self.connImage.setAttrManifestDict(__manifestRules), True)
        self.assertEqual(self.connImage.getAttrManifestDict(), __manifestRules)

    def testGetAttrSetting(self):
        __getAttrs = ['author', 'psi', 'select', 'theta', 'id']
        self.assertEqual(self.connImage.setAttrManifestDict(dict(get=__getAttrs)), True)

        __screenedVars =self.connImage.filterForRestGet(dict(author=None, psi=-19.98, theta=0.28))
        self.assertNotEqual(None, __screenedVars)
        self.assertEqual(hasattr(__screenedVars, 'keys'), True)
        self.assertNotEqual(list(__screenedVars.keys()), __getAttrs)
        self.assertNotIn('associatedRange_id', __screenedVars)

    def testPutAttrSetting(self):
        __putAttrs = ['x', 'y', 'select', 'associatedImage_id', 'associatedRange_id']
        self.assertEqual(self.connImage.setAttrManifestDict(dict(put=__putAttrs)), True)

        __screenedVars =self.connImage.filterForRestPut(dict(x=10, y=24.0, associatedImage_id=24, id=76, associatedRange_id=25))
        self.assertNotEqual(None, __screenedVars)
        self.assertEqual(hasattr(__screenedVars, 'keys'), True)
        self.assertNotEqual(list(__screenedVars.keys()), __putAttrs)
        self.assertNotIn('id', __screenedVars)

    def testPostAttrSetting(self):
        __postAttrs = ['x', 'y', 'select', 'associatedImage_id', 'associatedRange_id']
        self.assertEqual(self.connImage.setAttrManifestDict(dict(post=__postAttrs)), True)

        __screenedVars = self.connImage.filterForRestPost(dict(y=94, associatedImage_id=23, id=59, associatedRange_id=28))
        self.assertNotEqual(None, __screenedVars)
        self.assertEqual(hasattr(__screenedVars, 'keys'), True)
        self.assertNotEqual(list(__screenedVars.keys()), __postAttrs)

        self.assertNotIn('x', __screenedVars) # Legal variable but was not included in the attribute dict
        self.assertNotIn('id', __screenedVars)

    def testDeleteAttrSetting(self):
        __deleteAttrs = ['x', 'y', 'id']
        self.assertEqual(self.connImage.setAttrManifestDict(dict(delete=__deleteAttrs)), True)

        __screenedVars = self.connImage.filterForRestDelete(dict(x=12, associatedImage_id=45, id=13))
        self.assertNotEqual(None, __screenedVars)
        self.assertEqual(hasattr(__screenedVars, 'keys'), True)
        self.assertNotEqual(list(__screenedVars.keys()), __deleteAttrs)

        self.assertNotIn('y', __screenedVars)
        self.assertNotIn('associatedImage_id', __screenedVars)

    def testDBLiason(self):
        self.assertEqual(self.connImage.initDBLiason(), True)
        __1stDbLiason = self.connImage.getDBLiason()
        self.assertNotEqual(__1stDbLiason, None)

        self.assertEqual(self.connImage.setConnectedAddress('http://127.0.0.1'), True)
        __2ndDbLiason = self.connImage.getDBLiason()
        self.assertNotEqual(__2ndDbLiason, None)

        self.assertNotEqual(__1stDbLiason, __2ndDbLiason)

    def testCrossNetConnections(self):
        self.assertEqual(self.connImage.setConnectedAddress('http://127.0.0.1:8000/gcs/'), True)
        self.assertEqual(self.connImage.getAddress(), 'http://127.0.0.1:8000/gcs/imageHandler')
       
        imageData = dict(
            title='Testing', ppmDifference=234.582, utmNorth=-12.81, speed=123345.98,
            course=-103.89, alt=259.23, author=os.environ.get('USERNAME', 'Anonymous')
        )

        postResult = self.connImage.postConn(imageData)
        print('postResult', postResult)

        getResult = self.connImage.getConn(imageData)
        print('getResult', getResult)

        putResult  = self.connImage.putConn(imageData)
        # Requiring an id for an update/put
        dataReturned = getResult.get('value', {}).get('data', [{}])
        if dataReturned:
            queriedId = dataReturned[0].get('id', -1)
            if queriedId != -1:
                imageData['id'] =  queriedId
            print('putResult', putResult)

        deleteResult = self.connImage.deleteConn(imageData)
        print('deleteResult', deleteResult)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
