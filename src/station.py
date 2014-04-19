#!/usr/bin/env python3
# Author: Cindy Xiao <dixin@ualberta.ca>, Emmanuel Odeke <odeke@ualberta.ca>

import os
import sys
from PyQt5 import QtWidgets, QtGui

import gcs # Generated module by running: pyuic5 gcs.ui > gcs.py

import utils # Local module
import stack # Local module
import imageViewer # Local module

curDirPath = os.path.abspath('.')

class GroundStation(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(GroundStation, self).__init__(parent)

        self.ui_window = gcs.Ui_MainWindow()
        self.ui_window.setupUi(self)

        self.__pixmapCache = dict()
        self.stack = stack.Stack(None)

        self.initUI()
        self.addFilesToStack(self.imageViewer.loadContentFromDb())

    def initUI(self):
        # Set up actions
        self.initActions()

        # Set up menus
        self.initMenus()

        self.initFileDialog()
        self.initImageViewer()
        self.initClicks()

    def initImageViewer(self):
        self.imageViewer = imageViewer.ImageViewer(
            self.ui_window.fullSizeImageScrollArea
        )
        self.ui_window.fullSizeImageScrollArea.setWidget(self.imageViewer)

    def initFileDialog(self):
        self.fileDialog = QtWidgets.QFileDialog()
        self.fileDialog.setFileMode(3) # Multiple files can be selected
        self.fileDialog.filesSelected.connect(self.__normalizeFileAdding)

    def initClicks(self):
        self.ui_window.nextButton.clicked.connect(self.showNext)
        self.ui_window.previousButton.clicked.connect(self.showPrev)

    def __normalizeFileAdding(self, paths):
        # Ensuring that paths added are relative to a common source eg
        # Files from folder ./data will be present on all GCS stations
        # so only the relative path not absolute path should be added
        normalizedPaths = []
        for path in paths:
            if path.find(curDirPath) >= 0:
                path = '.' + p.split(curDirPath)[1]

            normalizedPaths.append(
                utils.DynaItem(dict(path=path, markerSet=[]))
            )

        self.addFilesToStack(normalizedPaths)

    def addFilesToStack(self, dynaDictList):
        for dynaDict in dynaDictList:
            self.stack.push(dynaDict.path, dynaDict)

        self.showNext()

    def initMenus(self):
        self.fileMenu = QtWidgets.QMenu("&File", self)
        self.editMenu = QtWidgets.QMenu("&Edit", self)
        self.syncMenu = QtWidgets.QMenu("&Sync", self)

        self.fileMenu.addAction(self.exitAction)
        self.fileMenu.addAction(self.findImagesAction)

        self.editMenu.addAction(self.syncCurrentItemAction)
        self.editMenu.addAction(self.popCurrentImageAction)

        self.syncMenu.addAction(self.dbSyncAction)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.editMenu)
        self.menuBar().addMenu(self.syncMenu)

    def initActions(self):
        self.popCurrentImageAction = QtWidgets.QAction(
            "&Remove currentImage", self
        )
        self.popCurrentImageAction.triggered.connect(self.handleItemPop)

        # Save coordinates
        self.syncCurrentItemAction = QtWidgets.QAction("&Save Coordinates", self)
        self.syncCurrentItemAction.setShortcut('Ctrl+S')
        self.syncCurrentItemAction.triggered.connect(self.syncCurrentItem)

        # Synchronization with DB
        self.dbSyncAction = QtWidgets.QAction("&Sync with DB", self)
        self.dbSyncAction.triggered.connect(self.dbSync)
        self.dbSyncAction.setShortcut('Ctrl+R')

        # Exit
        self.exitAction = QtWidgets.QAction("&Exit", self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(self.cleanUpAndExit)

        # Finding and adding images
        self.findImagesAction = QtWidgets.QAction("&Add Images", self)
        self.findImagesAction.setShortcut('Ctrl+O')
        self.findImagesAction.triggered.connect(self.findImages)

        # Navigating
        self.nextItemAction = QtWidgets.QAction('&Next Item', self)
        self.nextItemAction.setShortcut('Ctrl+N')
        self.nextItemAction.triggered.connect(self.showNext)

        self.prevItemAction = QtWidgets.QAction('&Previous Item', self)
        self.prevItemAction.setShortcut('Ctrl+P')
        self.prevItemAction.triggered.connect(self.showPrev)

    def showNext(self):
        self.__stackToPhoto(self.stack.next)

    def showPrev(self):
        self.__stackToPhoto(self.stack.prev)

    def getPixMapByKey(self, path):
        memPixMap = self.__pixmapCache.get(path, None)
        if memPixMap is None:
            self.__pixmapCache[path] = QtGui.QPixmap(path)
            memPixMap = self.__pixmapCache[path]

        return memPixMap

    def __stackToPhoto(self, method):
        invokedResult = method()
        if invokedResult is not None:
            self.key, self.currentItem = invokedResult
            path, markerSet = self.key, []
            if isinstance(self.currentItem, utils.DynaItem):
                path = self.currentItem.path
                markerSet = self.currentItem.markerSet

            memPixMap = self.getPixMapByKey(path)
            self.imageViewer.openImage(
                fPath=path, markerSet=markerSet, pixMap=memPixMap
            )
            self.ui_window.countDisplayLabel.setText(path)

    def handleItemPop(self):
        print('handleItemPop')

    def syncCurrentItem(self):
        self.imageViewer.syncCurrentItem()

    def dbSync(self):
        self.imageViewer.loadContentFromDb(syncForCurrentImageOnly=True)

    def cleanUpAndExit(self):
        self.close()

    def findImages(self):
        if isinstance(self.fileDialog, QtWidgets.QFileDialog):
            self.fileDialog.show()
        else:
            qBox = QMessageBox(parent=self)
            qBox.setText('FileDialog was not initialized')
            qBox.show()

def main():
    argc = len(sys.argv)
    app = QtWidgets.QApplication(sys.argv)

    gStation = GroundStation()
    gStation.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
