#!/usr/bin/python3

# Author: Cindy Xiao <dixin@ualberta.ca>
#         Emmanuel Odeke <odeke@ualberta.ca>

"""
Main interface for ground station.
"""

import os
import sys
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QCursor, QPixmap

# Import all from QtWidgets for development for now.
# So for classes that are part of QtWidgets, I've specifically stated QtWidget.Class() for now.
from PyQt5.QtWidgets import *

import Tag # Local module
import utils # Local module
import PanedWindow # Local module
import ImageViewer # Local module

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
        imgViewId = self.addChild(ImageViewer.ImageViewer)

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

        # Now load up all content saved in the DB
        self.addFilesToStack(self.imageView.loadAllLastEditTimes())

    def showNext(self):
        self.__stackToPhoto(self.stack.next)

    def showPrev(self):
        self.__stackToPhoto(self.stack.prev)

    def getCurrentItem(self):
        return self.currentItem

    def __stackToPhoto(self, method):
        self.currentItem = method()
        print('currentItem', self.stack) # currentItem, self.imageMap)
        if isinstance(self.currentItem, utils.DynaItem):
           self.imageView.openImage(
             fPath=self.currentItem.path, markerSet=self.currentItem.markerSet
           )
        else:
           self.imageView.openImage(self.currentItem)

    def handleItemPop(self):
        popd = self.stack.pop()
        print('poppd', popd)
        if isinstance(popd, utils.DynaItem):
          popd = popd.path

        if popd: self.imageView.deleteImageFromDb(popd)

        # We won't be shielding the GUI from harsh realities of life
        # ie if there is no more content left

        itemToShow = None
        if self.stack.canGetPrev():
            itemToShow = self.stack.prev()
        else:
            itemToShow = self.stack.next()

        if isinstance(itemToShow, utils.DynaItem):
          self.imageView.openImage(
            fPath=itemToShow.path, markerSet=itemToShow.markerSet
          )
        else:
          self.imageView.openImage(itemToShow)

    def initMenus(self):
        self.fileMenu = QtWidgets.QMenu("&File", self)
        self.editMenu = QtWidgets.QMenu("&Edit", self)
        self.syncMenu = QtWidgets.QMenu("&Sync", self)

        self.fileMenu.addAction(self.exitAction)
        self.fileMenu.addAction(self.findImagesAction)

        self.editMenu.addAction(self.saveCoordsAction)
        self.editMenu.addAction(self.popCurrentImageAction)

        self.syncMenu.addAction(self.dbSyncAction)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.editMenu)
        self.menuBar().addMenu(self.syncMenu)

    def initActions(self):
        self.popCurrentImageAction = QtWidgets.QAction("&Remove currentImage", self)
        self.popCurrentImageAction.triggered.connect(self.handleItemPop)

        # Save coordinates
        self.saveCoordsAction = QtWidgets.QAction("&Save Coordinates", self)
        self.saveCoordsAction.setShortcut('Ctrl+S')
        self.saveCoordsAction.triggered.connect(self.saveCoords)

        # Synchronization with DB
        self.dbSyncAction = QtWidgets.QAction("&Sync with DB", self)
        self.dbSyncAction.triggered.connect(self.dbSync)
        self.dbSyncAction.setShortcut('Ctrl+R')

        # Exit
        self.exitAction = QtWidgets.QAction("&Exit", self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(self.close)

        # Finding and adding images
        self.findImagesAction = QtWidgets.QAction("&Add Images", self)
        self.findImagesAction.setShortcut('Ctrl+O')
        self.findImagesAction.triggered.connect(self.findImages)

    def addFilesToStack(self, dynaDictList):
        # print('paths', paths)
        self.stack.push(dynaDictList)
        self.showNext()

    def __normalizeFileAdding(self, paths):
        self.addFilesToStack(list(
          map(lambda p : utils.DynaItem(dict(path=p, markerSet=[])), paths)
        ))

    # Our file explorer
    def __setUpFileExplorer(self):
        self.fileDialog = QFileDialog()
        self.fileDialog.setFileMode(3) # Multiple files can be selected
        self.fileDialog.filesSelected.connect(self.__normalizeFileAdding)

    def findImages(self):
        if isinstance(self.fileDialog, QFileDialog):
            self.fileDialog.show()
        else:
            qBox = QMessageBox(parent=self)
            qBox.setText('FileDialog was not initialized')
            qBox.show()

    def saveCoords(self):
        self.imageView.saveCoords()

    def dbSync(self):
        self.imageView.loadAllLastEditTimes(syncForCurrentImageOnly=False)

def main():
    print("Ground station running.")
    app = QtWidgets.QApplication(sys.argv)
    mainwin = MainWindow(sys.argv[1:])
    mainwin.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
