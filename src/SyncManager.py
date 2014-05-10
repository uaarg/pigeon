#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import utils
import DbLiason
import constants
import mpUtils.JobRunner

class SyncManager:
    def __init__(self, dbHandler):
        self.__dbHandler = dbHandler

        self.initResourcePool()
        self.initMProcessingUtils()

    def initMProcessingUtils(self):
        self.__jobRunner = mpUtils.JobRunner.JobRunner()

    def initResourcePool(self):
        self.__resourcePool = dict()
        self.__reverseMarkerPool = dict()

    def mapToLocalKey(self, path):
        return utils.getLocalName(path) or path

    def getImageAttrsByKey(self, key):
        return self.__resourcePool.get(key, {})

    def getImageId(self, key):
        return self.getImageAttrsByKey().get('id', -1)

    def getMarkerSetByKey(self, key):
        return self.getImageAttrsByKey(key).get('marker_set', [])

    def syncFromDB(self, callback=None, title=None, uri=None, metaDict=None, qId=-1):
        return self.__jobRunner.run(self.__syncFromDB, None, callback, (title, uri, metaDict, qId,))

    def __syncFromDB(self, *args, **kwargs):
        title, uri, metaDict, qId = args[0]
        # print('title', title, 'uri', uri, 'metaDict', metaDict, 'qId', qId)
        queryDict = dict(sort='lastTimeEdit_r')

        if title:
            queryDict['title'] = title

        if uri:
            queryDict['uri'] = uri

        if qId and qId > 0:
            queryDict['id'] = qId

        queryResponse = utils.produceAndParse(self.__dbHandler.imageHandler.getConn, dataIn=queryDict)
        if hasattr(queryResponse, 'reason'):  # An error here
            print('queryResponse', queryResponse['reason'])
        else:
            data = queryResponse.get('data', [])
            # print('data', data)
            for item in data:
                keySelector = item.get('title', None) or item.get('uri', None)
                localKey = self.mapToLocalKey(keySelector)

                self.__resourcePool[localKey] = item

                dbMarkerSet = item.get('marker_set', [])
                targetID = item.get('id', -1)

                for index, m in enumerate(dbMarkerSet):
                    self.__reverseMarkerPool[(m.get('id', -1), targetID,)] = (index, localKey,)

            if hasattr(metaDict, 'get'):
                dbMetaDict = queryResponse.get('meta', {})
                for k, v in  dbMetaDict.items():
                    metaDict[k] = v

            # print('data', data)
            return data

    def __needsSync(self, path=None):
        pass
 
    def needsSync(self, path=None): 
        queryDict = dict(format='short', uri=path, select='lastTimeEdit')

        parsedResponse = utils.produceAndParse(
          func=self.__dbHandler.imageHandler.getConn, dataIn=queryDict
        )

        data = parsedResponse.get('data', None) if hasattr(parsedResponse, 'get') else None

        if data:
            key = self.mapToLocalKey(path)
            memAttrMap = self.getImageAttrsByKey(key)

            memId, memlastTimeEdit = int(memAttrMap.get('id', -1)), float(memAttrMap.get('lastTimeEdit', -1))

            itemInfo = data[0]
            idOnCloud = int(itemInfo.get('id', -1))
            imageOnCloudlastTimeEdit = float(itemInfo['lastTimeEdit'])

            if idOnCloud < 1:
                print('\033[48mThis data is not present on cloud, path:', path, '\033[00m')
                return constants.IS_FIRST_TIME_SAVE
            elif imageOnCloudlastTimeEdit > memlastTimeEdit:
                print('\033[47mDetected a need for saving here since')
                print('your last memoized local editTime was', memlastTimeEdit)
                print('Most recent db editTime is\033[00m', imageOnCloudlastTimeEdit)
                return constants.IS_OUT_OF_SYNC
            else:
                print('\033[42mAll good! No need for an extra save for',\
                     path, '\033[00m'
                )
                return constants.IS_IN_SYNC
        else:
            print("\033[41mNo data back from querying about lastTimeEdit\033[00m")
            #TODO: Handle this special case
            return constants.NO_DATA_BACK

    def bulkSaveMarkers(self, associatedKey, markerDictList):
        associatedImageId = self.getImageAttrsByKey(associatedKey).get('id', -1)
        results = None
        if associatedImageId > 0:
            resMap = []
            
            for markerDict in markerDictList:
                getterFunc = markerDict.get('getter', lambda: {})
                dataDict = getterFunc()
                dataDict['associatedImage_id'] = associatedImageId
                # print('dataDict', dataDict)
                
                saveResult = self.saveMarkerToDB(dataDict)
                print('saveResult', dataDict, saveResult) 
                if (saveResult.get('data', {}).get('id', -1) != -1) or (saveResult.get('id', -1) != -1):
                    onSuccess = markerDict.get('onSuccess', lambda: {})
                    onSuccess(saveResult)
                else:
                    print('failure', saveResult)
                    onFailure = markerDict.get('onFailure', lambda: {})
                    onFailure()

                resMap.append(saveResult)

            results = dict(associatedImageId=associatedImageId, data=resMap)
            
        return results

    def syncImageToDB(self, path, callback=None):
        return self.__jobRunner.run(self.__syncImageToDB, None, callback, path)

    def __syncImageToDB(self, pathArgs):
        path = pathArgs[0]
        elemData = self.getImageAttrsByKey(path)
        elemAttrDict = dict((k, v) for k, v in elemData.items() if k != 'marker_set')

        memId = int(elemData.get('id', -1))
        methodName = 'putConn'

        if memId <= 0:
            methodName = 'postConn'
            elemAttrDict.pop('id', None) # Let the DB decide what Id to assign to you

        func = getattr(self.__dbHandler.imageHandler, methodName)
        parsedResponse = utils.produceAndParse(func, elemAttrDict)
        idFromDB = parsedResponse.get('id', -1)
       
        pathDict = self.__resourcePool.get(path, None) 
        if pathDict is None:
            pathDict = dict()

        pathDict['id'] = idFromDB
        print('idFromDB', path, parsedResponse)
        self.__resourcePool[path] = pathDict
            
        return 200

    def getKeys(self):
        return self.__resourcePool.keys()

    def saveMarkerToDB(self, mData, isPost=True):
        queryDict = dict(
            x=mData.get('x', 0), y=mData.get('y', 0), associateImage_id=mData.get('associatedImage_id', -1)
        )
        getQuery = utils.produceAndParse(self.__dbHandler.markerHandler.getConn, queryDict)
        data = getQuery.get('data', [])
        func = self.__dbHandler.markerHandler.postConn
        if data:
            mData['id'] = data[0].get('id', -1)
            func = self.__dbHandler.markerHandler.putConn 
        else:
            mData.pop('id', -1) # Safety net

        print('queryDict', queryDict, 'dataToBeSaved', mData)
        markerSaveResponse = utils.produceAndParse(func, dataIn=mData)
        return markerSaveResponse

    def deleteMarkerByAttrsFromDB(self, markerAttrDict):
        markerDelResponse = utils.produceAndParse(
            self.__dbHandler.markerHandler.deleteConn, dataIn=markerAttrDict
        )

        deletedIDs = markerDelResponse.get('data', [])
        for mId in deletedIDs:
            popKey = (mId, imageId,)
            indexKeyTuple = self.__reverseMarkerPool.pop(popKey, None)
            if indexKeyTuple is not None:
                mIndex, key = indexKeyTuple
                markerMap = self.__resourcePool.get(key, None) 
                if markerMap is not None:
                    markerList = markerMap.get('marker_set', [])
                    if mIndex < len(markerList):
                        markerList.pop(mIndex)

    def keyInResourcePool(self, key):
        return key in self.__resourcePool

    def deleteImageByKeyFromDB(self, localKey, isGlobalDelete=False, callback=None):
        return self.__jobRunner.run(self.__deleteImageByKeyFromDB, None, callback, (localKey, isGlobalDelete,))

    def __deleteImageByKeyFromDB(self, *args):
        localKey, isGlobalDelete = args[0]
        memData = self.__resourcePool.get(localKey, {})

        # Clear out all the markers first
        markerSet = memData.get('marker_set', [])

        for elem in markerSet:
            markerAttrDict = dict(associatedImage_id=memData.get('id', -1), id=elem.get('id', -1))
            markerDelResponse = self.__dbHandler.markerHandler.deleteConn(markerAttrDict)
            print(markerDelResponse)

        delAttrDict = dict(id=memData.get('id', -1))
        delResponse = self.__dbHandler.imageHandler.deleteConn(delAttrDict)
        delStatusCode = delResponse.get('status_code', 400)

        if delStatusCode == 200:
            if isGlobalDelete:
                popdItem = self.__resourcePool.pop(localKey, None)
                print('popd', popdItem)

        return delResponse

    def editLocalImage(self, key, attrDict):
        memDict = self.getImageAttrsByKey(key)
        for k, v in attrDict.items():
            memDict[k] = v

        self.__resourcePool[key] = memDict

    def saveImageToDB(self, key, attrDict, needsCloudSave=False):
        editResponse = self.editLocalImage(key, attrDict)

        return self.syncImageToDB(key)

def main():
    args, options = utils.cliParser()

    # Time to get address that the DB can be connected to via
    dbAddress = '{ip}:{port}/gcs'.format(ip=args.ip.strip('/'), port=args.port.strip('/'))
    print('Connecting via: \033[92m dbAddress', dbAddress, '\033[00m')
       
    dbConnector = DbLiason.GCSHandler(dbAddress)

    syncManager = SyncManager(dbConnector)
    print('syncFromDB', syncManager.syncFromDB())
    print('syncImageToDB', syncManager.syncImageToDB(None))

    keys = list(syncManager.getKeys())
    for k in keys:
        print(syncManager.deleteImageByKeyFromDB(k))

if __name__ == '__main__':
    main()
