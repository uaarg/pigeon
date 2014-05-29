#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import ElementBase

class ConnImage(ElementBase.ElementBase):
    def __init__(self, body, address='http://127.0.0.1/gcs/', attrManifestDict=None):
        super(ConnImage, self).__init__(address, 'imageHandler', attrManifestDict)

    def initStateVars(self):
        __postOrPutRules =[
            'author', 'title', 'uri', 'metaData', 'blob', 'phi', 'psi', 'alt', 'captureTimeEpoch',
            'theta',  'course', 'speed', 'utmEast', 'utmNorth', 'pixelPerMeter', 'ppmDifference'
        ]

        super.setAttrManifestDict(dict(
            post=__postOrPutRules, put=__postOrPutRules, delete=['id'] + __postOrPutRules,
            get=['select', 'format', 'sort', 'limit', 'offset'] + __postOrPutRules
        ))
