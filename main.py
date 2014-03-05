
"""
Main interface for ground station.
"""

import sys
import time
import json, pickle
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QCursor, QPixmap
# Import all from QtWidgets for development for now.
# So for classes that are part of QtWidgets, I've specifically stated QtWidget.Class() for now.
from PyQt5.QtWidgets import *

class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window for the ground station.
    """
    def __init__(self, sysargs):
        super(MainWindow, self).__init__()

        self.sysargs = sysargs

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

    def initMenus(self):
        self.fileMenu = QtWidgets.QMenu("&File", self)
        self.fileMenu.addAction(self.saveCoordsAction)
        self.fileMenu.addAction(self.exitAction)
        self.menuBar().addMenu(self.fileMenu)


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
        self.serializedMarkersFile = 'serializedCoords.pk'
        self.coordsFilename = "coords.txt"

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
                self.setPixmap(QPixmap.fromImage(image))

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
        print(self.getCursorPosition());
        self.coords.append(dict(position=self.getCursorPosition(), time=time.time()))

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
