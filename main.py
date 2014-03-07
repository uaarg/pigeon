#!/usr/bin/python3
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

getDefaultUserName = lambda : os.environ.get('USER', 'Anonymous')

class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window for the ground station.
    """
    def __init__(self, sysargs):
        super(MainWindow, self).__init__()

        self.sysargs = sysargs
        self.fileDialog = None

        # Set up window
        self.setWindowTitle("pigeon")
        self.setGeometry(300, 300, 250, 150)

        # Set up image viewer
        self.imageView = ImageViewer(sysargs)
        self.setCentralWidget(self.imageView)

        # Set up actions
        self.initActions()

        # Set up menus
        self.initMenus()
    
        self.__setUpFileExplorer()

    def initMenus(self):
        self.fileMenu = QtWidgets.QMenu("&File", self)
        self.editMenu = QtWidgets.QMenu("&Edit", self)
        self.fileMenu.addAction(self.saveCoordsAction)
        self.fileMenu.addAction(self.exitAction)
        self.editMenu.addAction(self.findImagesAction)
        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.editMenu)


    def initActions(self):
        # Save coordinates
        # self.saveCoordsAction = QtWidgets.QAction("&Save Coordinates", self, shortcut='Ctrl+S', triggered=self.saveCoords)
        self.saveCoordsAction= QtWidgets.QAction("&Save Coordinates", self)
        self.saveCoordsAction.setShortcut('Ctrl+S')
        self.saveCoordsAction.triggered.connect(self.saveCoords)

        # Exit
        # self.exitAction = QtWidgets.QAction("&Exit", self, shortcut='Ctrl+Q', triggered=self.close)
        self.exitAction = QtWidgets.QAction("&Exit", self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(self.close)
        self.findImagesAction = QtWidgets.QAction("&Find Images", self)
        self.findImagesAction.triggered.connect(self.findImages)

    def addFilesToQueue(self, paths):
        pass

    # Our file explorer
    def __setUpFileExplorer(self):
        self.fileDialog = QFileDialog()
        self.fileDialog.setFileMode(3) # Multiple files can be selected
        self.fileDialog.filesSelected.connect(lambda paths:print(paths))

    def findImages(self):
        if isinstance(self.fileDialog, QFileDialog):
            self.fileDialog.show()
        else:
            qBox = QMessageBox(parent=self) # parent=self, 'Improperly initialized fileDialog!')
            qBox.setText('FileDialog was not initialized')
            qBox.show()

    def saveCoords(self):
        self.imageView.saveCoords()

    def serializeCoords(self):
        self.imageView.serializeCoords()

class ImageViewer(QtWidgets.QLabel):
    def __init__(self, sysargs):
        super(ImageViewer, self).__init__()

        # Set up main display area
        # self.imageLabel = QtWidgets.QLabel()
        # self.imageLabel.show()

        # Set up cursor
        self.cursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.cursor)
        self.getCursorPosition()

        self.__fileOnDisplay = None

        # Open image
        try:
            self.imagePath = sysargs[1]
        except:
            print("Usage: python main.py [image_path]")
            sys.exit()
        else:
            self.openImage(self.imagePath)

        # Set up storing coordinates
        self.coords = []

        # Set up for storing tagged info
        self.tags   = []
        self.serializedMarkersFile = 'serializedCoords.pk'
        self.coordsFilename = "coords.txt"

    def addTaggedInfo(self, content):
        print(content)
        self.tags.append(content)

    def openImage(self, filename):
        """
        Opens image from specified path.
        """
        if filename:
            image = QImage(filename)
            if image.isNull():
                QMessageBox.information(self, "Error", "Can't load image %s." %(filename))
            else:
                # Convert from QImage to QPixmap, and display
                self.__fileOnDisplay = filename
                self.setPixmap(QPixmap.fromImage(image))

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
            self.createTag(e)

    def createTag(self, event):
        t = Tag.Tag(
            parent=None, title = '@%s'%(time.ctime()),
            location = Tag.DynaItem(dict(x=event.x(), y=event.y())),
            size = Tag.DynaItem(dict(x=200, y=200)),
            onSubmit = self.addTaggedInfo,
            metaData = dict(
              author = getDefaultUserName(),
              filePath = self.currentFilePath,
              captureTime = time.time(), x = event.x(), y = event.y()
            ),
            entryList = [
              Tag.DynaItem(dict(
                  title='Description', isMultiLine=False, eLocation=(1, 1,),
                  lLocation=(1, 0,), initContent=None
                )
              ),
              Tag.DynaItem(dict(
                  title='Location', isMultiLine=False,
                  eLocation=(3, 1,), lLocation=(3, 0,),
                  initContent='%s, %s'%(event.x(), event.y())
                )
              )
            ]
        )


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
    mainwin = MainWindow(sys.argv)
    mainwin.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
