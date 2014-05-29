#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import Connectable

class ElementBase(Connectable.Connectable):
    def __init__(self, body, addrSuffix, address='http://127.0.0.1/gcs/', attrManifestDict=None):
        super(ElementBase, self).__init__(self.__prepareOwnAddress(address), attrManifestDict)

        self.__body = body or {}
        self.__addrSuffix = addrSuffix

    def __runOnSupersJobRunner(self, *args, **kwargs):
        __jobRunner = super().getJobRunner()
        if hasattr(__jobRunner, 'run'):
            return __jobRunner.run(*args, **kwargs)

    def __setStateVars(self, attrDict=None): 
        if isinstance(attrDict, dict):
            for k, v in attrDict.items():
                self.__body[k] = v

    def setStateVars(self, attrDict=None, callback=None): 
        return self.__runOnSupersJobRunner(self.__setStateVars, None, callback, attrDict)

    def setAddress(self, newAddress, callback=None):
        return super().setAddress(self.__prepareOwnAddress(newAddress), callback)

    def __prepareOwnAddress(self, address):
        return address.strip('/') + '/' + self.__addrSuffix if hasattr(address, 'strip') else address
        
    def setAttrManifestDict(self, manifest):
        return super().setAttrManifestDict(manifest)

    def __setKeyValue(self, key, value, callback=None):
        self.__body[key] = value

    def getKeyValue(self, key, altValue=None):
        return self.__body.get(key, altValue)

    def setKeyValue(self, key, value, callback=None):
        return  self.__runOnSupersJobRunner(self.__setKeyValue, None, callback, key, value)

    def putConn(self, varsDict=None, onFinish=None, callback=None):
        return super().putConn(varsDict or self.__body, onFinish, callback)

    def postConn(self, varsDict=None, onFinish=None, callback=None):
        return super().postConn(varsDict or self.__body, onFinish, callback)

    def getConn(self, varsDict=None, onFinish=None, callback=None):
        return super().getConn(varsDict or self.__body, onFinish, callback)

    def deleteConn(self, varsDict=None, onFinish=None, callback=None):
        return super().deleteConn(varsDict or self.__body, onFinish, callback)
