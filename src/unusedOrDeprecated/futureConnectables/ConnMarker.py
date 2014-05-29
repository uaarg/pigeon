#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import ElementBase

class ConnMarker(ElementBase.ElementBase):
    def __init__(self, body, address='http://127.0.0.1/gcs/', attrManifestDict=None):
        super(ConnMarker, self).__init__(address, 'markerHandler', attrManifestDict)

    def initStateVars(self):
        __postOrPutRules =['x', 'y', 'associatedImage_id', 'iconPath', 'author', 'comments']
        super.setAttrManifestDict(dict(
            post=__postOrPutRules, put=__postOrPutRules, delete=['id'] + __postOrPutRules,
            get=['select', 'format', 'sort', 'limit', 'offset'] + __postOrPutRules
        ))
