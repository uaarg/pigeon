#!/usr/bin/env python3
# Author: Cindy Xiao <dixin@ualberta.ca>, Emmanuel Odeke <odeke@ualberta.ca>

import os
import sys
from PyQt5 import QtWidgets, QtGui

import gcs # Generated module by running: pyuic5 gcs.ui > gcs.py

import utils # Local module
import stack # Local module
import imageViewer # Local module
import mpUtils.JobRunner
from thumbnailStrip import IconStrip

curDirPath = os.path.abspath('.')

class GroundStation(QtWidgets.QMainWindow):
    __jobRunner     = mpUtils.JobRunner.JobRunner()
    def __init__(self, parent=None):
        super(GroundStation, self).__init__(parent)

        self.ui_window = gcs.Ui_MainWindow()
        self.ui_window.setupUi(self)

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
        self.initStrip()

    def initImageViewer(self):
        self.imageViewer = imageViewer.ImageViewer(
            self.ui_window.fullSizeImageScrollArea
        )
        self.ui_window.fullSizeImageScrollArea.setWidget(self.imageViewer)

    def initStrip(self):
        self.iconStrip = IconStrip.IconStrip(self)
        self.ui_window.thumbnailScrollArea.setWidget(self.iconStrip)
        self.iconStrip.setOnItemClick(self.selectImageToDisplay)

    def initFileDialog(self):
        self.fileDialog = QtWidgets.QFileDialog()
        self.fileDialog.setFileMode(3) # Multiple files can be selected
        self.fileDialog.filesSelected.connect(self.pictureDropped)

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

    def __addFilesToStack(self, dynaDictList):
        for dynaDict in dynaDictList:
            self.stack.push(dynaDict.path, dynaDict)
            self.iconStrip.addIconItem(dynaDict.path, self.selectImageToDisplay)

    def addFilesToStack(self, dynaDictList, **kwargs):
        return self.__jobRunner.run(self.__addFilesToStack, None, None, dynaDictList, **kwargs)
        
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

    def __invokeOpenImage(self, displayArgs):
        if displayArgs is not None:
            self.key, self.currentItem = displayArgs 
            path, markerSet = self.key, []
            if isinstance(self.currentItem, utils.DynaItem):
                path = self.currentItem.path
                markerSet = self.currentItem.markerSet

            memPixMap = self.iconStrip.getPixMap(path)
            self.imageViewer.openImage(fPath=path, markerSet=markerSet, pixMap=memPixMap)
            self.ui_window.countDisplayLabel.setText(path)
            self.stack.setPtrToKeyIndex(path)

    def selectImageToDisplay(self, path):
        argTuple = (path, self.stack.accessByKey(path, []),)
        self.__invokeOpenImage(argTuple)

    def __stackToPhoto(self, method):
        self.__invokeOpenImage(method())

    def handleItemPop(self):
        popd = self.stack.pop()

        if isinstance(popd, utils.DynaItem):
          popd = popd.path

        if popd:
            self.imageViewer.deleteImageFromDb(popd)
            self.iconStrip.popIconItem(popd, None)

        method = None
        if self.stack.canGetPrev():
            method = self.stack.prev
        else:
            method = self.stack.next

        self.__stackToPhoto(method)

    def syncCurrentItem(self):
        self.imageViewer.syncCurrentItem()

    def dbSync(self):
        self.imageViewer.loadContentFromDb(syncForCurrentImageOnly=True)

    def cleanUpAndExit(self):
        self.iconStrip.close()
        self.fileDialog.close()
        self.imageViewer.close()

        print(self, 'closing')
        self.close()

    def findImages(self):
        if isinstance(self.fileDialog, QtWidgets.QFileDialog):
            self.fileDialog.show()
        else:
            qBox = QMessageBox(parent=self)
            qBox.setText('FileDialog was not initialized')
            qBox.show()

    def pictureDropped(self, itemList):
        for itemUri in itemList:
            if os.path.exists(itemUri):
                self.iconStrip.addIconItem(itemUri, self.selectImageToDisplay)

def main():
    argc = len(sys.argv)
    app = QtWidgets.QApplication(sys.argv)

    gStation = GroundStation()
    gStation.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
