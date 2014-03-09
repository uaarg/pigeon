#!/usr/bin/python3

# Author: Cindy Xiao <dixin@ualberta.ca>
#         Emmanuel Odeke <odeke@ualberta.ca>

"""
Main interface for ground station.
"""

import os
import sys
import time
import json, pickle
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QCursor, QPixmap

# Import all from QtWidgets for development for now.
# So for classes that are part of QtWidgets, I've specifically stated QtWidget.Class() for now.
from PyQt5.QtWidgets import *

import Tag # Local module
import utils # Local module
import Marker

class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window for the ground station.
    """
    def __init__(self, paths):
        super(MainWindow, self).__init__()

        self.fileDialog = None
        self.stack = utils.PseudoStack(paths)

        # Set up window
        self.setWindowTitle("pigeon")
        layout = QGridLayout()

        # Set up image viewer
        self.__imageDisplayFrame = QtWidgets.QFrame(self)
        self.__imageDisplayFrame.setFrameStyle(
            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken
        )

        self.__controlFrame = QtWidgets.QFrame(self)
        self.__controlFrame.setFrameStyle(QtWidgets.QFrame.Panel)
        self.setGeometry(0, 0, 800, 800)

        self.imageView = ImageViewer(self.__imageDisplayFrame)
        imageFrameWidth = 2 * self.width() / 3
        self.__imageDisplayFrame.setGeometry(
            0, 0, imageFrameWidth, self.height()
        )
        self.__controlFrame.setGeometry(
            self.__imageDisplayFrame.width(), 0, self.width() - self.imageView.width(), self.height())
        layout.addWidget(self.__controlFrame, 2, 0)

        halfFrameWidth = self.__imageDisplayFrame.width() / 2
        halfFrameHeight = self.__imageDisplayFrame.height() / 2

        prevButton = QtWidgets.QPushButton(self)
        prevButton.setText('&Previous')
        prevButton.move(0, halfFrameHeight)
        prevButton.clicked.connect(self.showPrev)
        prevButton.show()

        nextButton = QtWidgets.QPushButton(self)
        nextButton.setText('&Next')
        nextButton.move(
          imageFrameWidth - nextButton.width(), halfFrameHeight
        )
        nextButton.clicked.connect(self.showNext)
        nextButton.show()

        layout.addWidget(prevButton, 1, 0)
        self.showNext()
        self.__imageDisplayFrame.show()
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

    def __stackToPhoto(self, method):
        item = method()
        print(item)
        self.imageView.openImage(item)
        #  print('No more content')

    def handleItemPop(self):
        popd = self.stack.pop()
        print('poppd', popd)

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
    def __init__(self, parent=None):
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

    def openImage(self, fPath):
        print('openImage invoked')
        """
        Opens image from specified path.
        """
        filename = fPath if fPath else utils._404_IMAGE_PATH

        image = QImage(filename)
        if image.isNull():
            QMessageBox.information(self, "Error", "Can't load image %s." %(filename))
        else:
            # Convert from QImage to QPixmap, and display
           self.__fileOnDisplay = filename
           imgPixMap = QPixmap.fromImage(image)
           self.setPixmap(QPixmap.fromImage(image))
           # Expand to the image's full size
           self.setGeometry(self.x(), self.y(), image.width(), image.height())

    @property
    def currentFilePath(self): return self.__fileOnDisplay

    def getCursorPosition(self):
        """
        Gets the current position of the mouse cursor on the image.
        Returns a list containing mouse coordinates on the image.
        """
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
        marker = Marker.Marker(parent=self,  x=curPos[0], y=curPos[1])
        marker.show()
        print(marker.__dict__)
        self.markers.append(marker)
      
    def loadMarkers(self):
        with open(self.serializedMarkersFile, 'rb') as f:
            return pickle.load(f)
                

    def __writeToFile(self, filePath, isPickled, attr='time'):
        funcToUse = json.dump
        if isPickled:
            funcToUse = pickle.dump

        __outCoords = sorted(self.coords, key=lambda a : a.get(attr, None), reverse=True)
        __uniqPath = "%s-%s"%(time.ctime().replace(' ', '_'), filePath)
        with open(__uniqPath, 'w') as f:
            funcToUse(__outCoords, f)

    def saveCoords(self, attr='time'):
        self.__writeToFile(filePath=self.coordsFilename, isPickled=False, attr=attr)

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
