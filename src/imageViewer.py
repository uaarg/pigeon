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
    __gcsH = DbLiason.GCSHandler('http://142.244.112.66:8000/gcs')
    __imageHandler  = __gcsH.imageHandler
    __markerHandler = __gcsH.markerHandler
    __jobRunner     = mpUtils.JobRunner.JobRunner()

    def __init__(self, parent=None, treeMap=None):
        super(ImageViewer, self).__init__(parent)

        # Set up cursor
        self.cursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.cursor)

        self.__fileOnDisplay = None

        self.imgPixMap = None
        self._childMap = None
        self.__childrenMap = collections.defaultdict(lambda : None)

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

    def __deleteImageFromDb(self, title):
        imgDelResponse = utils.produceAndParse(
            self.__imageHandler.deleteConn, dict(title=title)
        )

        print('imgDelResponse', imgDelResponse, title)

        data = imgDelResponse.get('data', dict()) 
        if not hasattr(data, 'get'):
            print('Probably image was not saved to the db')
            return
        else:
            successfulDels = data.get('successful', [])
            # TODO: Figure out what to do with the failed deletes
            # failed = data.get('failed', [])
       
            for sId in successfulDels: 
                # Clear out all the associated markers
                mDelResponse = utils.produceAndParse(
                    self.__markerHandler.deleteConn, dict(associatedImage_id=sId)
                )

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

    def openImage(self, fPath, markerSet=[], pixMap=None):
        if self._childMap is not None:
            # print('\033[44mself._childMap', self._childMap, '\033[00m')
            for k, v in self._childMap.items():
                v.hide()

        filename = fPath if fPath else utils._PLACE_HOLDER_PATH

        # print('self.imgPixMap', pixMap)
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
                    # print('filePath', filename, v)
                    v.show()
            
            self.setPixmap(self.imgPixMap)

            # Expand to the image's full size
            # self.setGeometry(self.x(), self.y(), self.imgPixMap.width(), self.imgPixMap.height())

            # Check again with the synchronizer
            self.checkSyncOfEditTimes()

    def loadContentFromDb(self, syncForCurrentImageOnly=False):
        connArgs = dict(sort='lastTimeEdit_r') # Getting the most recently edited first
        if syncForCurrentImageOnly:
            connArgs['title'] =  self.__fileOnDisplay

        parsedResponse = utils.produceAndParse(
            self.__imageHandler.getConn, connArgs
        )
    
        data = parsedResponse.get('data', None)
        if data:
            inOrderItems = [] 
        
            if self.lastEditTimeMap: 
                self.lastEditTimeMap.clear()

            for v in data:
                title, uri = v.get('title', None), v.get('uri', None) 
                markerSet = v.get('marker_set', [])

                # Saving titles here since comparisons are to made with
                # data local to your ground station
                self.lastEditTimeMap[title] = (v['id'], float(v['lastTimeEdit']))

                pathSelector = uri if uri else title
                inOrderItems.append(
                    utils.DynaItem(dict(path=pathSelector, markerSet=markerSet))
                )

                if self.__fileOnDisplay == title:
                    childMap = self.__childrenMap.get(title, dict()) 
                    # We need to create a copy of keys of a dict
                    # that we shall be popping from to avoid data
                    # contention issues
                    markerCopy = list(childMap.keys())[:] 
                    for mKey in markerCopy:
                        mk = childMap[mKey]
                        if mk:
                            mk.erase(mk.x, mk.y, needsFlush=False)
       
                    # Now create the markers that are recognized by the DB 
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
            parent=self, x=curPos.x(), y=curPos.y(), tree=self.childMap,
            mComments=curPos.mComments, onDeleteCallback=self.deleteMarkerFromDb, **kwargs
        )

        return marker
     
    def checkSyncOfEditTimes(self): 
        return self.__jobRunner.run(self.__checkSyncOfEditTimes, None, None)

    def __checkSyncOfEditTimes(self, *args):
        parsedResponse = utils.produceAndParse(
          func=self.__imageHandler.getConn,
          dataIn=dict(title=self.__fileOnDisplay,select='lastTimeEdit')
        )

        data = parsedResponse.get('data', None) if hasattr(parsedResponse, 'get') else None

        if data:
            savedValueTuple = self.lastEditTimeMap[self.__fileOnDisplay]
            iId, savedLastEditTime = savedValueTuple

            itemInfo = data[0]
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

    def syncCurrentItem(self, isSynchronous=False):
        if isSynchronous:
            print('\033[46mSaving synchronously\033[00m')
            return self.__jobRunner.run(self.__syncCurrentItem, None, None)
        else:
            print('\033[47mSaving using created thread\033[00m')
            return self.__jobRunner.run(self.__syncCurrentItem, None, print)

    def __syncCurrentItem(self, *args):
        if self.checkSyncOfEditTimes():
            print('No edit was recently performed for', self.__fileOnDisplay)
        else: # First time image is being registered
            parsedResponse = utils.produceAndParse(
              func=self.__imageHandler.postConn,
              dataIn= dict(
                uri=self.__fileOnDisplay, title=self.__fileOnDisplay,
                author=utils.getDefaultUserName()
              )
            )

            syncResponse = parsedResponse.get('data', None)
            # print(postData)
            if syncResponse:
                print(syncResponse)
                dbItem = syncResponse
                print('Memoizing a lastTimeEdit for ', self.__fileOnDisplay)
                self.lastEditTimeMap[self.__fileOnDisplay] =\
                     (dbItem.get('id', -1), dbItem.get('lastTimeEdit', -1),)

                # print('postResponse', postData)
                self.checkSyncOfEditTimes()
            else:
                print("Could not post the data to the DB.Try again later")

        # Markers may have changed
        childMap = self.__childrenMap.get(self.__fileOnDisplay, None)

        if childMap:
            targetId = self.lastEditTimeMap[self.__fileOnDisplay][0]
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

                # print('currentComments', currentComments, data)
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
                        if not currentComments == commentsFromDb: # Time for a put here
                            putResponse = utils.produceAndParse(
                                self.__markerHandler.putConn,
                                dict(id=retr['id'], comments=currentComments)
                            )
                            print('\033[45mPutResponse', putResponse, '\033[00m')
                            m.toggleSaved()

def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    imViewer = ImageViewer()
    imViewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
  main()
