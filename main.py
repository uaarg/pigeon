#!/usr/bin/python3

# Author: Cindy Xiao <dixin@ualberta.ca>
#         Emmanuel Odeke <odeke@ualberta.ca>

"""
Main interface for ground station.
"""

import os
import sys
import time
import collections
import json, pickle
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QCursor, QPixmap

# Import all from QtWidgets for development for now.
# So for classes that are part of QtWidgets, I've specifically stated QtWidget.Class() for now.
from PyQt5.QtWidgets import *

import Tag # Local module
import utils # Local module
import Marker # Local module
import DbLiason # Local module
import PanedWindow # Local module

class MainWindow(PanedWindow.PanedWindow):
    """
    Main application window for the ground station.
    """
    def __init__(self, paths):
        super(MainWindow, self).__init__()

        self.fileDialog = None
        self.stack = utils.PseudoStack(paths)

        # Set up window
        self.setWindowTitle("GSC")
        layout = QGridLayout()
        print(self.children)

        self.imageMap = dict()
        self.__controlFrame = QtWidgets.QFrame(self)
        self.__controlFrame.setFrameStyle(QtWidgets.QFrame.Panel)
        self.setGeometry(0, 0, 800, 500)

        # Set up image viewer
        imgViewId = self.addChild(ImageViewer)

        self.imageView = self.children[imgViewId]['child']

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        self.scrollArea.setWidget(self.imageView)
        self.imageView.move(self.scrollArea.width()//4, self.scrollArea.height()//4)
        self.setCentralWidget(self.scrollArea)

        # Important step before you add the panes in
        self.onLeftPaneClick = self.showPrev
        self.onRightPaneClick = self.showNext

        self.addPanes()

        layout.addWidget(self.__controlFrame, 2, 0)
        self.showNext()
        self.__controlFrame.show()

        # Set up actions
        self.initActions()

        # Set up menus
        self.initMenus()
    
        self.__setUpFileExplorer()
        # self.setLayout(layout)

    def showNext(self):
        self.__stackToPhoto(self.stack.next)

    def showPrev(self):
        self.__stackToPhoto(self.stack.prev)

    def getCurrentItem(self):
        return self.currentItem

    def __stackToPhoto(self, method):
        self.currentItem = method()
        # print('currentItem', self.currentItem, self.imageMap)
        self.imageView.openImage(self.currentItem)

    def handleItemPop(self):
        popd = self.stack.pop()
        print('poppd', popd)
        self.imageView.deleteFromDb(popd)

        # We won't be shielding the GUI from harsh realities of life
        # ie if there is no more content left
        nextItem = self.stack.next()
        self.imageView.openImage(nextItem)

    def initMenus(self):
        self.fileMenu = QtWidgets.QMenu("&File", self)
        self.editMenu = QtWidgets.QMenu("&Edit", self)
        self.fileMenu.addAction(self.saveCoordsAction)
        self.fileMenu.addAction(self.exitAction)
        self.editMenu.addAction(self.findImagesAction)
        self.editMenu.addAction(self.popCurrentImageAction)
        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.editMenu)

    def initActions(self):
        # Save coordinates
        self.saveCoordsAction= QtWidgets.QAction("&Save Coordinates", self)
        self.saveCoordsAction.setShortcut('Ctrl+S')
        self.saveCoordsAction.triggered.connect(self.saveCoords)

        # Exit
        self.exitAction = QtWidgets.QAction("&Exit", self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(self.close)

        self.findImagesAction = QtWidgets.QAction("&Add Images", self)
        self.findImagesAction.triggered.connect(self.findImages)

        self.popCurrentImageAction = QtWidgets.QAction("&Remove currentImage", self)
        self.popCurrentImageAction.triggered.connect(self.handleItemPop)

    def addFilesToStack(self, paths):
        print('paths', paths)
        self.stack.push(paths)
        self.showNext()

    # Our file explorer
    def __setUpFileExplorer(self):
        self.fileDialog = QFileDialog()
        self.fileDialog.setFileMode(3) # Multiple files can be selected
        self.fileDialog.filesSelected.connect(self.addFilesToStack)

    def findImages(self):
        if isinstance(self.fileDialog, QFileDialog):
            self.fileDialog.show()
        else:
            qBox = QMessageBox(parent=self)
            qBox.setText('FileDialog was not initialized')
            qBox.show()

    def saveCoords(self):
        self.imageView.saveCoords()

    def serializeCoords(self):
        self.imageView.serializeCoords()

class ImageViewer(QtWidgets.QLabel):
    __gcsH = DbLiason.GCSHandler('http://192.168.1.102:8000/gcs') 
    __imageHandler  = __gcsH.imageHandler
    __markerHandler = __gcsH.markerHandler

    def __init__(self, parent=None, treeMap=None):
        super(ImageViewer, self).__init__(parent)

        # Set up main display area
        # self.imageLabel = QtWidgets.QLabel()
        # self.imageLabel.show()

        # Set up cursor
        self.cursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.cursor)
        self.getCursorPosition()

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

    def getCursorPosition(self):
        self.cursorPosition = QWidget.mapFromGlobal(self, self.cursor.pos())
        coords = [self.cursorPosition.x(), self.cursorPosition.y()]
        return coords
    
    def mousePressEvent(self, e):
        """
        Event handler for mouse clicks on image area.
        """
        __cursorPosition = self.getCursorPosition()
        self.coords.append(dict(position=__cursorPosition, time=time.time()))
        if e.button() == 2: # Right click
            self.createMarker(e)

    def createMarker(self, event):
        curPos = self.getCursorPosition()
        marker = Marker.Marker(parent=self,  x=curPos[0], y=curPos[1], tree=self.childMap)
        marker.show()
      
    def loadMarkers(self):
        with open(self.serializedMarkersFile, 'rb') as f:
            return pickle.load(f)
                

    def __writeToFile(self, filePath, isPickled, attr='time'):
        print('\033[47mDeprecated\033[00m')
        '''
        funcToUse = json.dump
        if isPickled:
            funcToUse = pickle.dump

        __outCoords = sorted(self.coords, key=lambda a : a.get(attr, None), reverse=True)
        print(__outCoords)
        __uniqPath = "%s-%s"%(time.ctime().replace(' ', '_'), filePath)
        with open(__uniqPath, 'w') as f:
            funcToUse(__outCoords, f)
        '''

    def saveCoords(self, attr='time'):
        print('\033[46m%s\033[00m'%(self.__fileOnDisplay))
        ownMapQuery = self.__imageHandler.getConn(dict(title=self.__fileOnDisplay))

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
                      dict(author=utils.getDefaultUserName(), title=self.currentFilePath, uri=self.currentFilePath)
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
        # self.__writeToFile(filePath=self.coordsFilename, isPickled=False, attr=attr)
        '''

    def serializeCoords(self, attr='time'):
        self.__writeToFile(filePath=self.serializedMarkersFile, isPickled=True, attr=attr)
        

def main():
    import time

    print("Ground station running.")
    app = QtWidgets.QApplication(sys.argv)
    mainwin = MainWindow(sys.argv[1:])
    mainwin.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
