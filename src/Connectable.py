#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import json

import DbLiason
from mpUtils import JobRunner

class Connectable:
    def __init__(self, address=None, attrManifestDict=None):
        self.__dbLiason = None
        self.__address = address
        self.__jobRunner = JobRunner.JobRunner()
        self.__attrManifestDict = attrManifestDict if isinstance(attrManifestDict, dict) else {}

    def __initDBLiason(self, *args):
        self.__dbLiason = DbLiason.HandlerLiason(self.__address)
        return self.__dbLiason is not None

    def initDBLiason(self, callback=None):
        return self.__jobRunner.run(self.__initDBLiason, None, callback)

    def setConnectedAddress(self, addr):
        self.setAddress(addr)
        if hasattr(self.__dbLiason, 'shutdown'):
            self.__dbLiason.shutdown()

        return self.initDBLiason()

    def getDBLiason(self):
        return self.__dbLiason

    def getAddress(self):
        return self.__address

    def __setAddress(self, newAddress):
        self.__address = newAddress

    def setAddress(self, newAddress, callback=None):
        return self.__jobRunner.run(self.__setAddress, None, callback, newAddress)

    def __setAttrManifestDict(self, attrManifestDict, *args):
        if not isinstance(attrManifestDict, dict):
            return False
        else:
            self.__attrManifestDict = attrManifestDict
            return True

    def setAttrManifestDict(self, attrManifestDict, callback=None):
        return self.__jobRunner.run(self.__setAttrManifestDict, None, callback, attrManifestDict)

    def getAttrManifestDict(self):
        return self.__attrManifestDict

    def __filterAttrsPresentInManifest(self, restMethod, stateDict=None):
        if isinstance(stateDict, dict):
            dictatedManifest = self.__attrManifestDict.get(restMethod, [])
            screenedAttrs = [attr for attr in dictatedManifest if attr in stateDict]
            return dict((okAttr, stateDict[okAttr]) for okAttr in screenedAttrs)

    def filterForRestGet(self, stateDict, callback=None):
        return self.__jobRunner.run(self.__filterAttrsPresentInManifest, None, callback, 'get', stateDict)

    def ___opOnDBLiason(self, varsDict, restMethodName, onFinish):
        okAttrDict = getattr(self, 'filterForRest%s'%(restMethodName))(varsDict)

        relatedDBHandlerMethod = '%sConn'%(restMethodName.lower())
        response = self.__prepareAndParseNetResult(getattr(self.__dbLiason, relatedDBHandlerMethod)(okAttrDict))

        if hasattr(onFinish, '__call__'):
            onFinish(response)
        else:
            return response

    def __getConn(self, varsDict, onFinish):
        return self.___opOnDBLiason(varsDict, 'Get', onFinish)
        
    def getConn(self, varsDict, onFinish=None, callback=None):
        return self.__jobRunner.run(self.__getConn, None, callback, varsDict, onFinish)

    def filterForRestDelete(self, stateDict, callback=None):
        return self.__jobRunner.run(self.__filterAttrsPresentInManifest, None, callback, 'delete', stateDict)

    def __deleteConn(self, varsDict, onFinish):
        return self.___opOnDBLiason(varsDict, 'Delete', onFinish)
    
    def deleteConn(self, varsDict, onFinish=None, callback=None):
        return self.__jobRunner.run(self.__deleteConn, None, callback, varsDict, onFinish)

    def filterForRestPost(self, stateDict, callback=None):
        return self.__jobRunner.run(self.__filterAttrsPresentInManifest, None, callback, 'post', stateDict)

    def __postConn(self, varsDict, onFinish=None):
        return self.___opOnDBLiason(varsDict, 'Post', onFinish)

    def postConn(self, varsDict, onFinish=None, callback=None):
        return self.__jobRunner.run(self.__postConn, None, callback, varsDict, onFinish)

    def filterForRestPut(self, stateDict, callback=None):
        return self.__jobRunner.run(self.__filterAttrsPresentInManifest, None, callback, 'put', stateDict)

    def __putConn(self, varsDict, onFinish):
        return self.___opOnDBLiason(varsDict, 'Put', onFinish)

    def putConn(self, varsDict, onFinish=None, callback=None):
        return self.__jobRunner.run(self.__putConn, None, callback, varsDict, onFinish)

    def __prepareAndParseNetResult(self, httpResponse):
        outData = dict(status_code=httpResponse.get('status_code', 400))
        try:
            outData['value'] = json.loads(httpResponse.get('value', '{}').decode())
        except Exception as e:
            print('\033[91mUnhandled exception\033[00m', e)
        finally:
            return outData
