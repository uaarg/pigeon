#!/usr/bin/env python3
# Author: Cindy Xiao <dixin@ualberta.ca>, Emmanuel Odeke <odeke@ualberta.ca>

import os
import sys
from PyQt5 import QtWidgets, QtGui

import gcs # Generated module by running: pyuic5 gcs.ui > gcs.py

import utils # Local module
import iconStrip # Local module
import imageViewer # Local module
import mpUtils.JobRunner # Local module

curDirPath = os.path.abspath('.')

class GroundStation(QtWidgets.QMainWindow):
    __jobRunner     = mpUtils.JobRunner.JobRunner()
    def __init__(self, parent=None):
        super(GroundStation, self).__init__(parent)

        self.ui_window = gcs.Ui_MainWindow()
        self.ui_window.setupUi(self)

        self.__resourcePool = dict()

        self.initUI()
        self.preparePathsForDisplay(self.imageViewer.loadContentFromDb())

    def initUI(self):
        # Set up actions
        self.initActions()

        # Set up menus
        self.initToolBar()

        self.initFileDialog()
        self.initImageViewer()
        self.initStrip()
        self.ui_window.countDisplayLabel.hide()

    def initImageViewer(self):
        self.imageViewer = imageViewer.ImageViewer(
            self.ui_window.fullSizeImageScrollArea
        )
        self.ui_window.fullSizeImageScrollArea.setWidget(self.imageViewer)

    def initStrip(self):
        self.iconStrip = iconStrip.IconStrip(self)
        self.ui_window.thumbnailScrollArea.setWidget(self.iconStrip)
        self.iconStrip.setOnItemClick(self.displayThisImage)

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
                path = '.' + path.split(curDirPath)[1]

            normalizedPaths.append(
                utils.DynaItem(dict(path=path, markerSet=[]))
            )

        self.preparePathsForDisplay(normalizedPaths)

    def __preparePathsForDisplay(self, dynaDictList):
        lastItem = None
        for dynaDict in dynaDictList:
            if dynaDict.path not in self.__resourcePool:
                self.iconStrip.addIconItem(dynaDict.path, self.displayThisImage)
                lastItem = dynaDict.path

            self.__resourcePool[dynaDict.path] = dynaDict

        # Display the last added item
        self.displayThisImage(lastItem)

    def preparePathsForDisplay(self, dynaDictList, **kwargs):
        return self.__jobRunner.run(
            self.__preparePathsForDisplay, None, None, dynaDictList, **kwargs
        )
        
    def initToolBar(self):
        self.toolbar  = self.ui_window.toolBar;

        self.toolbar.addAction(self.findImagesAction)

        self.toolbar.addAction(self.syncCurrentItemAction)
        self.toolbar.addAction(self.dbSyncAction)
        self.toolbar.addAction(self.popCurrentImageAction)
        self.toolbar.addAction(self.exitAction)

    def initActions(self):
        self.popCurrentImageAction = QtWidgets.QAction(QtGui.QIcon('icons/recyclebin_close.png'),
            "&Remove currentImage", self
        )
        self.popCurrentImageAction.triggered.connect(self.handleItemPop)

        # Synchronization with DB
        self.syncCurrentItemAction = QtWidgets.QAction(QtGui.QIcon('icons/iconmonstr-upload.png'),"&Save", self)
        self.syncCurrentItemAction.setShortcut('Ctrl+S')
        self.syncCurrentItemAction.triggered.connect(self.syncCurrentItem)

        self.dbSyncAction = QtWidgets.QAction(QtGui.QIcon('icons/iconmonstr-save.png'), "&Sync all", self)
        self.dbSyncAction.triggered.connect(self.dbSync)
        self.dbSyncAction.setShortcut('Ctrl+R')

        # Exit
        self.exitAction = QtWidgets.QAction(QtGui.QIcon('icons/exit.png'), "&Exit", self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(self.cleanUpAndExit)

        # Finding and adding images
        self.findImagesAction = QtWidgets.QAction(QtGui.QIcon('icons/iconmonstr-folder.png'), "&Add Images", self)
        self.findImagesAction.setShortcut('Ctrl+O')
        self.findImagesAction.triggered.connect(self.findImages)

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

    def displayThisImage(self, path):
        argTuple = (path, self.__resourcePool.get(path, []))
        self.__invokeOpenImage(argTuple)

    def handleItemPop(self):
        popd = self.__resourcePool.pop( 
            self.ui_window.countDisplayLabel.text(), None
        )

        if isinstance(popd, utils.DynaItem):
          popd = popd.path

        nextItemOnDisplay = None
        if popd:
            self.imageViewer.deleteImageFromDb(popd)
            nextItemOnDisplay = self.iconStrip.popIconItem(popd, None)

        self.displayThisImage(nextItemOnDisplay)

    def syncCurrentItem(self):
        self.imageViewer.syncCurrentItem()

    def dbSync(self):
        self.preparePathsForDisplay(self.imageViewer.loadContentFromDb())

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
        self.__normalizeFileAdding(itemList)

def main():
    argc = len(sys.argv)
    app = QtWidgets.QApplication(sys.argv)

    gStation = GroundStation()
    gStation.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
