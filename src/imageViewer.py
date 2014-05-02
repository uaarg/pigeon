#!/usr/bin/python3

# Author: Cindy Xiao <dixin@ualberta.ca>
#         Emmanuel Odeke <odeke@ualberta.ca>

import time
import collections
from threading import Thread

from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QImage, QCursor, QPixmap

import utils # Local module
import Marker # Local module
import DbLiason # Local module
import mpUtils.JobRunner

class ImageViewer(QtWidgets.QLabel):
    # TODO: Provide configuration for the DBLiason
    __gcsH = DbLiason.GCSHandler('http://127.0.0.1:8000/gcs')
    __imageHandler  = __gcsH.imageHandler
    __markerHandler = __gcsH.markerHandler
    __jobRunner     = mpUtils.JobRunner.JobRunner()

    def __init__(self, parent=None, treeMap=None):
        super(ImageViewer, self).__init__(parent)

        # Set up cursor
        self.cursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.cursor)

        self.initResources()

    def initResources(self):
        self.__fileOnDisplay = None

        self.imgPixMap = None
        self._childMap = None
        self.__childrenMap = collections.defaultdict(lambda key: None)
        self.__resourcePool = dict()

        self.initLastEditTimeMap()

    def initLastEditTimeMap(self):
        self.lastEditTimeMap = collections.defaultdict(lambda : (-1, -1))

    @property
    def childMap(self):
        return self._childMap

    def close(self, **kwargs):
        for markerMap in self.__childrenMap.values():
            for marker in markerMap.values():
                if marker and hasattr(marker, 'close'):
                    marker.close()

        super().close()

    def deleteImageFromDb(self, title, isSynchronous=False):
      if isSynchronous:
        return self.__deleteImageFromDb(title)
      else:
        return self.__jobRunner.run(self.__deleteImageFromDb, None, None, title)

    def popAllMarkers(self, path):
        return self.__jobRunner.run(self.__popAllMarkers, None, None, path)

    def __popAllMarkers(self, path, **kwargs):
        markers = self.__childrenMap.pop(path, [])
        for marker in markers.values():
            marker.close()

    def __deleteImageFromDb(self, *args):
        title = args[0]
        localName = utils.getLocalName(title) or title
        memData = self.__resourcePool.pop(localName, None)

        if memData and memData.get('id', -1) != -1:
            mDelResponse = utils.produceAndParse(
                self.__markerHandler.deleteConn, dict(associatedImage_id=memData['id'])
            )
            print('mDelResponse', mDelResponse)

        imgDelResponse = utils.produceAndParse(
            self.__imageHandler.deleteConn, dict(title=title)
        )

        print('imgDelResponse', imgDelResponse, title)

        data = imgDelResponse.get('data', dict()) 
        if not hasattr(data, 'get'):
            print('Probably image was not saved to the db')
        else:
            self.lastEditTimeMap.pop(title, None)
            self.__popAllMarkers(title)

    def deleteMarkerFromDb(self, x, y):
        savValue = self.lastEditTimeMap[self.__fileOnDisplay]

        iId, savedLastEditTime = savValue
        if iId > 0:
            mDelResponse = utils.produceAndParse(
                self.__markerHandler.deleteConn,
                dict(x=x, y=y, associatedImage_id=iId)
            )

            print('After markerDeletion', mDelResponse)
            # Now lets clear the marker from the actual object map
        
            return mDelResponse

    def getCurrentFilePath(self):
        return self.__fileOnDisplay

    def getFromResourcePool(self, key, notFoundValue=None):
        return self.__resourcePool.get(key, notFoundValue)

    def setIntoResourcePool(self, key, value):
        memValue = self.__resourcePool.get(key, {})

        for k in value:
            memValue[k] = value[k]

        self.__resourcePool[key] = memValue

    def saveImageAttributes(self, imageTitle, imageAttributeDict):
        isFirstEntry = True
        key = utils.getLocalName(imageTitle) or imageTitle
        memData = self.__resourcePool.get(key, None)
        needsPut = memData is not None and memData.get('id', -1) != -1

        if needsPut:
            isFirstEntry = False
            imageAttributeDict['id'] = memData['id'] # Checking with the old

            parsedResponse = utils.produceAndParse(func=self.__imageHandler.putConn, dataIn=imageAttributeDict)

            # Now getting attributes returned from db syncing
        else:
            imageAttributeDict['title'] = imageTitle
            parsedResponse = utils.produceAndParse(func=self.__imageHandler.postConn, dataIn=imageAttributeDict)

            imageAttributeDict['id'] = parsedResponse.get('id', -1)
            
        return isFirstEntry, imageAttributeDict

    def openImage(self, fPath, markerSet=[], pixMap=None):
        if self._childMap is not None:
            for k, v in self._childMap.items():
                v.hide()

        filename = fPath if fPath else utils._PLACE_HOLDER_PATH

        image = None
        if pixMap is None:
            image =  QImage(filename)
            if image.isNull():
                QtWidgets.QMessageBox.information(self, "Error", "Can't load image %s." %(filename))
                return
            else:
                self.imgPixMap = QPixmap.fromImage(image)
        
        else:
            self.imgPixMap = pixMap

        if self.imgPixMap:
            self.__fileOnDisplay = filename

            self._childMap = self.__childrenMap.get(self.__fileOnDisplay, None)

            if self._childMap is None:
                self._childMap = dict()
 
                self.__childrenMap[self.__fileOnDisplay] = self._childMap

                for mData in markerSet:
                    if mData:
                        m = self.createMarker(
                            utils.DynaItem(dict(
                                x=lambda : int(mData['x']), y=lambda : int(mData['y']),
                                author=mData['author'], mComments=mData['comments']
                            ))
                        )
                        m.show()
                        m.toggleSaved()

            else:
                for k, v in self._childMap.items():
                    v.show()
            
            self.setPixmap(self.imgPixMap)

            # Return the most current state information
            key = utils.getLocalName(filename) or filename
            return self.__resourcePool.get(key, None)

    def getContentFromDB(self, syncForCurrentImageOnly=False):
        connArgs = dict(sort='lastTimeEdit_r') # Getting the most recently edited first
        if syncForCurrentImageOnly:
            connArgs['title'] =  self.__fileOnDisplay

        parsedResponse = utils.produceAndParse(
            self.__imageHandler.getConn, connArgs
        )
    
        data = parsedResponse.get('data', [])
        return data

    def loadContentFromDb(self, syncForCurrentImageOnly=False):
        data = self.getContentFromDB(syncForCurrentImageOnly)

        if data:
            inOrderItems = [] 
        
            if self.lastEditTimeMap:
                self.lastEditTimeMap.clear()

            for v in data:
                title, uri = v.get('title', None), v.get('uri', None) 
                markerSet = v.get('marker_set', [])

                # Saving titles here since comparisons are to made with
                # data local to your ground station
                pathSelector = uri if uri else title

                self.lastEditTimeMap[pathSelector] = (v['id'], float(v['lastTimeEdit']))

                inOrderItems.append(v)

                if self.__fileOnDisplay == title:
                    childMap = self.__childrenMap.get(pathSelector, dict()) 
                    # We need to create a copy of keys of a dict
                    # that we shall be popping from to avoid data
                    # contention issues
                    markerCopy = list(childMap.keys())[:] 
                    for mKey in markerCopy:
                        mk = childMap[mKey]
                        if mk:
                            print(mk.memComments)
                            mk.erase(mk.x, mk.y, needsFlush=False)
       
                    # Now create the markers that are recognized by the DB 
                    for mData in markerSet:
                        if mData:
                            print('mData', mData)
                            m = self.createMarker(
                                utils.DynaItem(dict(
                                    x=lambda : int(mData['x']), y=lambda : int(mData['y']),
                                    author=mData['author'], mComments=mData['comments']
                                ))
                            )
                            m.show()
                            m.toggleSaved()

                    self.__resourcePool[utils.getLocalName(pathSelector) or pathSelector] = v

            return inOrderItems
        else: return []
        
    def mousePressEvent(self, e):
        # Event handler for mouse clicks on image area.
        if e.button() == 2: # Right click
            curPos = self.mapFromGlobal(self.cursor.pos())
            m = self.createMarker(utils.DynaItem(
                dict(x=curPos.x, y=curPos.y, mComments='', author=None))
            )
            m.show()
            m.toggleUnsaved()

    def createMarker(self, curPos, **kwargs): 
        return self.__jobRunner.run(
            self.__createMarker, None, None, curPos, **kwargs
        )

    def __createMarker(self, curPos, **kwargs):
        marker = Marker.Marker(
            parent=self, x=curPos.x(), y=curPos.y(), tree=self.childMap, author=curPos.author,
            mComments=curPos.mComments, onDeleteCallback=self.deleteMarkerFromDb, **kwargs
        )

        return marker
     
    def checkSyncOfEditTimes(self, path=None, onlyRequiresLastTimeCheck=True): 
        return self.__jobRunner.run(self.__checkSyncOfEditTimes, None, None, path, onlyRequiresLastTimeCheck)

    def __checkSyncOfEditTimes(self, *args):
        path, onlyRequiresLastTimeCheck = args
        queryDict = dict(format='short', title=path)

        if onlyRequiresLastTimeCheck:
            queryDict['select'] = 'lastTimeEdit'

        parsedResponse = utils.produceAndParse(
          func=self.__imageHandler.getConn, dataIn=queryDict
        )

        data = parsedResponse.get('data', None) if hasattr(parsedResponse, 'get') else None

        if data:
            key = utils.getLocalName(self.__fileOnDisplay) or self.__fileOnDisplay
            savedValueTuple = self.lastEditTimeMap[self.__fileOnDisplay]
            iId, savedLastEditTime = savedValueTuple

            itemInfo = data[0]

            # if not onlyRequiresLastTimeCheck: # Extra attributes of the image were queried for 
            self.__resourcePool[key] = itemInfo

            lastEditTimeFromDb = float(itemInfo['lastTimeEdit'])

            if (lastEditTimeFromDb > savedLastEditTime):
                print('\033[47mDetected a need for saving here since')
                print('your last memoized local editTime was', savedLastEditTime)
                print('Most recent db editTime is\033[00m', lastEditTimeFromDb)
                self.lastEditTimeMap[self.__fileOnDisplay] =\
                            (itemInfo['id'], lastEditTimeFromDb,)
                return False
            else:
                print('\033[42mAll good! No need for an extra save for',\
                     self.__fileOnDisplay, '\033[00m'
                )
                return True
        else:
            print("\033[41mNo data back from querying about lastTimeEdit\033[00m")

    def syncCurrentItem(self, isSynchronous=False, path=None):
        if isSynchronous:
            print('\033[46mSaving synchronously\033[00m')
            return self.__jobRunner.run(self.__syncCurrentItem, None, None, path)
        else:
            print('\033[47mSaving using created thread\033[00m')
            return self.__jobRunner.run(self.__syncCurrentItem, None, print, path)

    def __syncCurrentItem(self, path, *args):
        return self.__syncByPath(path[0])

    def __syncByPath(self, path):
        print('\033[96mPath', path, '\033[00m')
        if self.checkSyncOfEditTimes(path=path):
            print('No edit was recently performed for', path)
        else: # First time image is being registered
            parsedResponse = utils.produceAndParse(
              func=self.__imageHandler.postConn,
              dataIn= dict(uri=path, title=path, author=utils.getDefaultUserName())
            )

            syncResponse = parsedResponse.get('data', None)

            if syncResponse:
                dbItem = syncResponse
                print('Memoizing a lastTimeEdit for ', path, dbItem)

                self.checkSyncOfEditTimes(path=path)
            else:
                print("Could not post the data to the DB.Try again later")

        # Markers may have changed
        childMap = self.__childrenMap.get(path, None)

        if childMap:
            targetId = self.lastEditTimeMap[path][0]
            print('targetId', targetId)
            if targetId > 0: # Save only markers of registered images
              for k, m in childMap.items():
                markerMap = dict(
                  iconPath=m.iconPath, x=str(m.x), y=str(m.y), associatedImage_id=targetId,
                  format='short', select='comments' # No need for foreign keys and extras
                )
                markerQuery = utils.produceAndParse(
                  self.__markerHandler.getConn, markerMap
                )
                data = markerQuery.get('data', None)
                currentComments = ''
                mInfo = m.entryData
                if mInfo:
                    currentComments = mInfo.get('Comments', dict()).get('entryText', '')

                if not data: # First time this marker is being created
                    markerMap['author'] = utils.getDefaultUserName()
                    markerMap['comments'] = currentComments

                    postResponse = utils.produceAndParse(
                      self.__markerHandler.postConn, markerMap
                    )
                    m.toggleSaved()
                else:
                    for retr in data:
                        commentsFromDb = retr['comments']
                        # print('currentComments', currentComments, commentsFromDb)
                        if currentComments != commentsFromDb: # Time for a put here
                            putResponse = utils.produceAndParse(
                                self.__markerHandler.putConn, dict(id=retr['id'], comments=currentComments)
                            )
                            print('putResponse', putResponse)

                            m.toggleSaved()

def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    imViewer = ImageViewer()
    imViewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
  main()
