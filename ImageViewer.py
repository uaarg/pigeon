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

class ImageViewer(QtWidgets.QLabel):
    __gcsH = DbLiason.GCSHandler('http://192.168.1.64:8000/gcs') 
    __imageHandler  = __gcsH.imageHandler
    __markerHandler = __gcsH.markerHandler

    def __init__(self, parent=None, treeMap=None):
        super(ImageViewer, self).__init__(parent)

        # Set up cursor
        self.cursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.cursor)

        self.__fileOnDisplay = None

        # Set up for storing tagged info
        self.setFrameShape(QFrame.Shape(10))
        self.imgPixMap = None
        self._childMap = None
        self.__childrenMap = collections.defaultdict(lambda : None)
        self.initLastEditTimeMap()

    def initLastEditTimeMap(self):
        self.lastEditTimeMap = collections.defaultdict(lambda : (-1, -1))

    @property
    def childMap(self):
        return self._childMap

    def deleteImageFromDb(self, title, isSynchronous=False):
      if isSynchronous:
        self.__deleteImageFromDb(title)
      else:
        th = Thread(target=self.__deleteImageFromDb, args=(title,))
        th.start()

    def __deleteImageFromDb(self, title):
        imgDelResponse = utils.produceAndParse(
            self.__imageHandler.deleteConn, dict(title=title)
        )

        # print('imgDelResponse', imgDelResponse)

        data = imgDelResponse.get('data', dict()) 
        successfulDels = data.get('successful', [])
        # TODO: Figure out what to do with the failed deletes
        # failed = data.get('failed', [])
       
        for sId in successfulDels: 
          # Clear out all the associated markers
          mDelResponse = utils.produceAndParse(
            self.__markerHandler.deleteConn, dict(associatedImage_id=sId)
          )
          # print('mDelResponse', mDelResponse)
        

        self.lastEditTimeMap.pop(title, None)

    def deleteMarkerFromDb(self, x, y):
        savValue = self.lastEditTimeMap[self.currentFilePath]

        iId, savedLastEditTime = savValue
        if iId > 0:
          mDelResponse = utils.produceAndParse(
            self.__markerHandler.deleteConn,
            dict(x=x, y=y, associatedImage_id=iId)
          )

          # print('After markerDeletion', mDelResponse)
          return mDelResponse

    def setCurrentFilePath(self, path):
        self.__fileOnDisplay = path

    def getCurrentFilePath(self):
        return self.__fileOnDisplay

    def openImage(self, fPath, markerSet=[]):
        if self._childMap is not None:
            # print('\033[44mself._childMap', self._childMap, '\033[00m')
            for k, v in self._childMap.items():
                v.hide()

        filename = fPath if fPath else utils._PLACE_HOLDER_PATH

        image = QImage(filename)
        print(filename)
        if image.isNull():
            QtWidgets.QMessageBox.information(self, "Error", "Can't load image %s." %(filename))
        else:
            # Convert from QImage to QPixmap, and display
            self.setCurrentFilePath(filename)
            self._childMap = self.__childrenMap[self.currentFilePath]

            if self._childMap is None:
                self._childMap = dict()
                self.__childrenMap[self.currentFilePath] = self._childMap

                for mData in markerSet:
                    if mData:
                        dictatedPosition =utils.DynaItem(
                          dict(x= lambda : int(mData['x']), y= lambda : int(mData['y']))
                        )
                           
                        m = self.createMarker(
                            dictatedPosition, author=mData['author'], mComments=mData['comments']
                        )
                        m.show()

            else:
                for k, v in self._childMap.items():
                    v.show()

            
            self.imgPixMap = QPixmap.fromImage(image)
            self.setPixmap(self.imgPixMap)

            # Expand to the image's full size
            self.setGeometry(self.x(), self.y(), image.width(), image.height())

            # Check again with the synchronizer
            self.checkSyncOfEditTimes()

    def loadContentFromDb(self, syncForCurrentImageOnly=False):
      connArgs = dict(sort='lastTimeEdit_r') # Getting the most recently edited first
      if syncForCurrentImageOnly:
        connArgs['title'] =  self.currentFilePath

      parsedResponse = utils.produceAndParse(self.__imageHandler.getConn, connArgs)

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

            if self.currentFilePath.__eq__(title):
                childMap = self.__childrenMap.get(self.currentFilePath, dict()) 
                markerCopy = list(childMap.keys())[:] # We need to create a copy of keys of a dict
                                                      # that we shall be popping from to avoid data
                                                      # contention issues
                for mKey in markerCopy:
                    mk = childMap[mKey]
                    if mk:
                      mk.erase(needsFlush=False)
       
                # Now create the markers that are recognized by the DB 
                for mData in markerSet:
                    if mData:
                        m = self.createMarker(
                            utils.DynaItem(
                                dict(x=lambda : int(mData['x']), y=lambda : int(mData['y']))
                            ), author=mData['author'], mComments=mData['comments']
                        )
                        m.show()

          return inOrderItems
      else: return []
        

    @property
    def currentFilePath(self): return self.__fileOnDisplay

    def mousePressEvent(self, e):
        # Event handler for mouse clicks on image area.
        if e.button() == 2: # Right click
            m = self.createMarker(self.mapFromGlobal(self.cursor.pos()))
            m.show()

    def createMarker(self, curPos, **kwargs):
        marker = Marker.Marker(
          parent=self, x=curPos.x(), y=curPos.y(), tree=self.childMap,
          onDeleteCallback=self.deleteMarkerFromDb, **kwargs
        )

        return marker
      
    def checkSyncOfEditTimes(self):
        parsedResponse = utils.produceAndParse(
          func=self.__imageHandler.getConn,
          dataIn=dict(title=self.currentFilePath,select='lastTimeEdit')
        )

        data = parsedResponse.get('data', None) if hasattr(parsedResponse, 'get') else None

        if data:
            savedValueTuple = self.lastEditTimeMap[self.currentFilePath]
            iId, savedLastEditTime = savedValueTuple

            itemInfo = data[0]
            lastEditTimeFromDb = float(itemInfo['lastTimeEdit'])

            if (lastEditTimeFromDb > savedLastEditTime):
                print('\033[47mDetected a need for saving here since')
                print('your last memoized local editTime was', savedLastEditTime)
                print('Most recent db editTime is\033[00m', lastEditTimeFromDb)
                self.lastEditTimeMap[self.getCurrentFilePath()] = (itemInfo['id'], lastEditTimeFromDb)
                return False
            else:
                print('\033[42mAll good! No need for an extra save for', self.getCurrentFilePath(), '\033[00m')
                return True
        else:
            print("\033[41mNo data back from querying about lastTimeEdit\033[00m")

    def saveCoords(self, isSynchronous=False):
      if isSynchronous:
        return self.__saveCoords()
      else:
        th = Thread(target=self.__saveCoords)
        print('\033[47mSaving using created thread\033[00m')
        th.start()

    def __saveCoords(self):
        # TODO: Add guards for thread safety
        # This function needs data protection

        if self.checkSyncOfEditTimes():
            print('No edit was recently performed for', self.currentFilePath)
        else: # First time image is being registered
            parsedResponse = utils.produceAndParse(
              func=self.__imageHandler.postConn,
              dataIn= dict(
                uri=self.currentFilePath, title=self.currentFilePath,
                author=utils.getDefaultUserName()
              )
            )

            postData = parsedResponse.get('data', None)
            print(postData)
            if parsedResponse:
                dbItem = postData
                print('Memoizing a lastTimeEdit for ', self.currentFilePath)
                self.lastEditTimeMap[self.currentFilePath] = dbItem.get('lastTimeEdit', (-1, -1))

                print('postResponse', postData)
                self.checkSyncOfEditTimes()
            else:
                print("Could not post the data to the DB.Try again later")


        # Markers may have changed
        childMap = self.__childrenMap.get(self.currentFilePath, None)

        if childMap:
            targetId = self.lastEditTimeMap[self.currentFilePath][0]
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
                    print('After creating marker', postResponse)
                else:
                    for retr in data:
                        commentsFromDb = retr['comments']
                        if not currentComments.__eq__(commentsFromDb): # Time for a put here
                            putResponse = utils.produceAndParse(
                                self.__markerHandler.putConn,
                                dict(id=retr['id'], comments=currentComments)
                            )
                            print('\033[45mPutResponse', putResponse, '\033[00m')

def main():
  import sys
  app = QtWidgets.QApplication(sys.argv)
  imViewer = ImageViewer()
  imViewer.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
