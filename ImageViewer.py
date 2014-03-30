#!/usr/bin/python3

# Author: Cindy Xiao <dixin@ualberta.ca>
#         Emmanuel Odeke <odeke@ualberta.ca>


import time
import json
import collections

from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QImage, QCursor, QPixmap

import utils # Local module
import Marker # Local module
import DbLiason # Local module

class ImageViewer(QtWidgets.QLabel):
    __gcsH = DbLiason.GCSHandler('http://192.168.1.102:8000/gcs') 
    __imageHandler  = __gcsH.imageHandler
    __markerHandler = __gcsH.markerHandler

    def __init__(self, parent=None, treeMap=None):
        super(ImageViewer, self).__init__(parent)

        # Set up cursor
        self.cursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.cursor)

        self.__fileOnDisplay = None

        # Set up storing coordinates
        self.coords = []

        # Set up for storing tagged info
        self.tags   = []
        self.markers = []
        self.serializedMarkersFile = 'serializedCoords.pk'
        self.setFrameShape(QFrame.Shape(10))
        self.coordsFilename = "coords.txt"
        self.imgPixMap = None
        self.__childrenMap = collections.defaultdict(lambda : None)
        self._childMap = None

    @property
    def childMap(self):
        return self._childMap

    def deleteFromDb(self, title):
        print(self.__imageHandler.deleteConn(dict(title=title)))

    def openImage(self, fPath):
        if self._childMap is not None:
            for k, v in self._childMap.items():
                v.hide()

        filename = fPath if fPath else utils._PLACE_HOLDER_PATH

        image = QImage(filename)
        if image.isNull():
            QMessageBox.information(self, "Error", "Can't load image %s." %(filename))
        else:
            # Convert from QImage to QPixmap, and display
            self.__fileOnDisplay = filename
            print('self.fileOnDisplay\033[47m%s'%(self.__fileOnDisplay))
            self._childMap = self.__childrenMap[self.__fileOnDisplay]
            if self._childMap is None:
                self._childMap = dict()
                self.__childrenMap[self.__fileOnDisplay] = self._childMap
            else:
                for k, v in self._childMap.items():
                    v.show()
                    print('\033[47mkey', k, v, '\033[00m')

            print('\033[43mChildMap', self._childMap, '\033[00m')
            self.imgPixMap = QPixmap.fromImage(image)
            self.setPixmap(self.imgPixMap)

            # Expand to the image's full size
            self.setGeometry(self.x(), self.y(), image.width(), image.height())

    @property
    def currentFilePath(self): return self.__fileOnDisplay

    def mousePressEvent(self, e):
        # Event handler for mouse clicks on image area.
        if e.button() == 2: # Right click
            self.createMarker(e)

    def createMarker(self, event):
        curPos = self.mapFromGlobal(self.cursor.pos())
        marker = Marker.Marker(
          parent=self, x=curPos.x(), y=curPos.y(), tree=self.childMap
        )
        marker.show()
      
    def loadMarkers(self):
        print('\033[47mDeprecated\033[00m')

    def saveCoords(self, attr='time'):
        print('\033[46m%s\033[00m'%(self.__fileOnDisplay))
        ownMapQuery = self.__imageHandler.getConn(
          dict(title=self.__fileOnDisplay)
        )

        if hasattr(ownMapQuery, 'reason'): # Error response
            print(ownMapQuery['reason'])
        else:
            serialzdResponse = ownMapQuery.get('value', None)
            if serialzdResponse:
                strResponse = serialzdResponse.decode()
                print('strResponse', strResponse)
                deSerialzd = json.loads(strResponse)
                data = deSerialzd.get('data', [])
                if data:
                    imgId = data[0].get('id', None)
                    print('data of image', data)
                    # Should resolve data changes
                else: # First time image is being registered
                    postResponse = self.__imageHandler.postConn(
                      dict(
                        uri=self.currentFilePath,
                        title=self.currentFilePath,
                        author=utils.getDefaultUserName()
                      )
                    )

                    for p, childMap in self.__childrenMap.items():
                        for k, m in childMap.items():
                            print(p, m.serialize())
                    print('postResponse', postResponse)

            else: # Format error here report it
                print("Error::Expecting the value attribute")
            
            # print(ownMapQuery)
        ''' 
        for path, childMap in self.__childrenMap.items():
            for key, marker in childMap.items():
              print(path, marker.serialize())
            # print('Saving', path, childMap)
        '''

def main():
  import sys
  app = QtWidgets.QApplication(sys.argv)
  imViewer = ImageViewer()
  imViewer.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
