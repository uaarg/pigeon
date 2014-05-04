#!/usr/bin/env python3
# Author: Cindy Xiao <dixin@ualberta.ca>, Emmanuel Odeke <odeke@ualberta.ca>

import os
import re
import sys
import threading
from PyQt5 import QtWidgets, QtGui, QtMultimedia

import gcs # Generated module by running: pyuic5 gcs.ui > gcs.py

import utils # Local module
import Tag # Local module
import iconStrip # Local module
import imageViewer # Local module
import mpUtils.JobRunner # Local module


curDirPath = os.path.abspath('.')
ATTR_VALUE_REGEX_COMPILE = re.compile('([^\s]+)\s*=\s*([^\s]+)\s*', re.UNICODE)

DEFAULT_IMAGE_FORM_DICT = dict(
    phi=0.0, psi=0, theta=0, alt=0, author=utils.getDefaultUserName(), utm_east=0.0, time=0,
    utm_north=0, speed=0, image_width=1294.0, image_height=964.0, viewangle_horiz=21.733333,
    viewangle_vert=16.833333, pixel_per_meter=0, ppm_difference=0, course=0
)

class GroundStation(QtWidgets.QMainWindow):
    __jobRunner     = mpUtils.JobRunner.JobRunner()
    def __init__(self, parent=None):
        super(GroundStation, self).__init__(parent)

        self.ui_window = gcs.Ui_MainWindow()
        self.ui_window.setupUi(self)

        self.__resourcePool = dict()

        self.initUI()
        self.initSaveSound()
        self.preparePathsForDisplay(self.imageViewer.loadContentFromDb())

    def initSaveSound(self):
        self.__saveSound = QtMultimedia.QSound('sounds/bubblePop.wav')

    def initUI(self):
        # Set up actions
        self.initActions()

        # Set up menus
        self.initToolBar()

        self.initFileDialogs()
        self.initImageViewer()
        self.initStrip()
        self.ui_window.countDisplayLabel.show()

    def initImageViewer(self):
        self.imageViewer = imageViewer.ImageViewer(
            self.ui_window.fullSizeImageScrollArea
        )
        self.ui_window.fullSizeImageScrollArea.setWidget(self.imageViewer)

    def initStrip(self):
        self.iconStrip = iconStrip.IconStrip(self)
        self.ui_window.thumbnailScrollArea.setWidget(self.iconStrip)
        self.iconStrip.setOnItemClick(self.displayThisImage)

    def initFileDialogs(self):
        self.fileDialog = QtWidgets.QFileDialog(caption='Add captured Images')
        self.fileDialog.setFileMode(3) # Multiple files can be selected
        self.fileDialog.filesSelected.connect(self.pictureDropped)

        self.locationDataDialog = QtWidgets.QFileDialog(caption='Add telemetry files')
        self.locationDataDialog.setFileMode(3) # Multiple files can be selected
        self.locationDataDialog.filesSelected.connect(self.processAssociatedDataFiles)

    def __normalizeFileAdding(self, paths):
        # Ensuring that paths added are relative to a common source eg
        # Files from folder ./data will be present on all GCS stations
        # so only the relative path not absolute path should be added
        normalizedPaths = []
        for path in paths:
            if path.find(curDirPath) >= 0:
                path = '.' + path.split(curDirPath)[1]

            normalizedPaths.append(dict(uri=path))

        self.preparePathsForDisplay(normalizedPaths)

    def __preparePathsForDisplay(self, pathDictList):
        lastItem = None
        for index, pathDict in enumerate(pathDictList):
        
            path = pathDict.get('uri', None)
            key = utils.getLocalName(path) or path
   
            if key not in self.__resourcePool:
                self.iconStrip.addIconItem(path, self.displayThisImage)

            self.__resourcePool[key] = pathDict

            if lastItem is None:
                lastItem = path

        # Display the last added item
        self.displayThisImage(lastItem)

        if lastItem: # Sound only if there is an item to be displayed
            self.__saveSound.play()

    def preparePathsForDisplay(self, dynaDictList, **kwargs):
        return self.__jobRunner.run(
            self.__preparePathsForDisplay, None, None, dynaDictList, **kwargs
        )
        
    def initToolBar(self):
        self.toolbar  = self.ui_window.toolBar;

        self.toolbar.addAction(self.editCurrentImageAction)
        self.toolbar.addAction(self.addLocationDataAction)
        self.toolbar.addAction(self.popCurrentImageAction)
        self.toolbar.addAction(self.findImagesAction)
        self.toolbar.addAction(self.syncCurrentItemAction)
        self.toolbar.addAction(self.dbSyncAction)
        self.toolbar.addAction(self.printCurrentImageDataAction)
        self.toolbar.addAction(self.exitAction)

    def editCurrentImage(self):
        print('Editing Current Image', self.ui_window.countDisplayLabel.text())

        srcPath = self.ui_window.countDisplayLabel.text()

        key = utils.getLocalName(srcPath) or srcPath
        stateDict = self.__resourcePool.get(key, None) or self.imageViewer.getFromResourcePool(key, None)

        entryList = []

        for index, entry in enumerate(DEFAULT_IMAGE_FORM_DICT.keys()):
            textExtracted = stateDict.get(entry, None)
            if textExtracted is None:
                textExtracted = DEFAULT_IMAGE_FORM_DICT[entry]

            entryList.append(
                utils.DynaItem(dict(
                    title=entry, isMultiLine=False, labelLocation=(index, 0,),
                    isEditable=True, entryLocation=(index, 1,), entryText=str(textExtracted)
                )
            ))

        imgAttrFrame = self.ui_window.imageAttributesFrame

        imageTag = Tag.Tag(
            size=utils.DynaItem(dict(x=imgAttrFrame.width(), y=imgAttrFrame.height())),
            location=utils.DynaItem(dict(x=imgAttrFrame.x(), y=imgAttrFrame.y())),
            title='Location data for: ' + utils.getLocalName(self.ui_window.countDisplayLabel.text()),
            onSubmit=self.saveCurrentImageContent,
            entryList=entryList
        )
        imageTag.show()

    def saveCurrentImageContent(self, content):
       
        curPath = self.ui_window.countDisplayLabel.text()
        key = utils.getLocalName(curPath) or curPath
        
        currentMap = self.__resourcePool.get(key, {})
        outDict = dict(id=currentMap.get('id', -1), uri=currentMap.get('uri', ''))

        for key in content:
            attrDict = content[key]
            outDict[key] = attrDict.get('entryText', '')

        # Getting the original ids in
        isFirstEntry, saveData = self.imageViewer.saveImageAttributes(curPath, outDict)

        if isFirstEntry:
            self.__resourcePool[key] = outDict

            # Give back the latest data
            self.imageViewer.setIntoResourcePool(key, outDict)

        self.imageViewer.checkSyncOfEditTimes(path=curPath, onlyRequiresLastTimeCheck=True)

    def initActions(self):
        self.popCurrentImageAction = QtWidgets.QAction(QtGui.QIcon('icons/recyclebin_close.png'),
            "&Remove currentImage", self
        )
        self.popCurrentImageAction.triggered.connect(self.handleItemPop)

        # Synchronization with DB
        self.syncCurrentItemAction = QtWidgets.QAction(
            QtGui.QIcon('icons/iconmonstr-upload.png'),"&Save to Cloud", self
        )
        self.syncCurrentItemAction.setShortcut('Ctrl+S')
        self.syncCurrentItemAction.triggered.connect(self.syncCurrentItem)

        self.dbSyncAction = QtWidgets.QAction(QtGui.QIcon('icons/iconmonstr-save.png'), "&Sync from Cloud", self)
        self.dbSyncAction.triggered.connect(self.dbSync)
        self.dbSyncAction.setShortcut('Ctrl+R')

        # Exit
        self.exitAction = QtWidgets.QAction(QtGui.QIcon('icons/exit.png'), "&Exit", self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(self.cleanUpAndExit)

        # Finding and adding images
        self.findImagesAction = QtWidgets.QAction(
            QtGui.QIcon('icons/iconmonstr-folder.png'), "&Add Images", self
        )
        self.findImagesAction.setShortcut('Ctrl+O')
        self.findImagesAction.triggered.connect(self.findImages)
        self.editCurrentImageAction = QtWidgets.QAction(
            QtGui.QIcon('icons/iconmonstr-picture-edit.png'), "&Edit Current Image", self
        )
        self.editCurrentImageAction.triggered.connect(self.editCurrentImage)
        self.editCurrentImageAction.setShortcut('Ctrl+E')

        self.addLocationDataAction = QtWidgets.QAction(
            QtGui.QIcon('icons/iconmonstr-note.png'), "&Add Telemetry Info", self
        )
        self.addLocationDataAction.triggered.connect(self.addLocationData)

        self.printCurrentImageDataAction = QtWidgets.QAction(
            QtGui.QIcon('icons/iconmonstr-printer.png'), "&Print Current Image Info", self
        )
        self.printCurrentImageDataAction.triggered.connect(self.printCurrentImageData)

    def displayThisImage(self, path):
        localName = utils.getLocalName(path) or path
        curItem = self.__resourcePool.get(localName, {})
        markerSet = []

        if curItem:
            markerSet = curItem.get('marker_set', [])

        memPixMap = self.iconStrip.getPixMap(path)
        valueFromResourcePool = self.imageViewer.openImage(fPath=path, markerSet=markerSet, pixMap=memPixMap)
       
        if valueFromResourcePool: 
            key = utils.getLocalName(path) or path
            self.__resourcePool[key] = valueFromResourcePool

        associatedTextFile = self.imageViewer.openImageInfo(fPath=path)
        self.processAssociatedDataFiles([associatedTextFile])

        self.ui_window.countDisplayLabel.setText(path)

    def handleItemPop(self):
        currentItem = self.ui_window.countDisplayLabel.text()

        nextItemOnDisplay = None

        if currentItem:
            self.imageViewer.deleteImageFromDb(currentItem)
            nextItemOnDisplay = self.iconStrip.popIconItem(currentItem, None)

        self.displayThisImage(nextItemOnDisplay)

    def syncCurrentItem(self):
        savText = self.ui_window.countDisplayLabel.text()
        
        self.imageViewer.syncCurrentItem(path=savText)

    def dbSync(self):
        self.preparePathsForDisplay(self.imageViewer.loadContentFromDb())

    def cleanUpAndExit(self):
        self.iconStrip.close()

        self.fileDialog.close()
        self.locationDataDialog.close()

        self.imageViewer.close()

        print(self, 'closing')

        print('close', self.__jobRunner.close())

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

    def printCurrentImageData(self):
        print('printCurrentImageData')
        

    def addLocationData(self):
        if isinstance(self.locationDataDialog, QtWidgets.QFileDialog):
            self.locationDataDialog.show()
        else:
            qBox = QMessageBox(parent=self)
            qBox.setText('FileDialog was not initialized')
            qBox.show()

    def processAssociatedDataFiles(self, pathList, **kwargs):
        return self.__jobRunner.run(self.__processAssociatedDataFiles, None, None, pathList, **kwargs)

    def __processAssociatedDataFiles(self, pathList, **kwargs):
        outMap = dict()
        for path in pathList:
            with open(path, 'r') as f:
                dataIn=f.readlines()
                outDict = dict()
                for line in dataIn:
                    line = line.strip('\n')
                    regexMatch = ATTR_VALUE_REGEX_COMPILE.match(line)
                    if regexMatch:
                        attr, value = regexMatch.groups(1)
                        
                        outDict[attr] = value
                
                key = utils.getLocalName(path) or path
                outMap[key] = outDict

        # Time to swap out the fields and replace
        for k in outMap:
            resourceMapped = self.__resourcePool.get(k, None)
            if resourceMapped is not None:
                freshValue = outMap[k]
                for key, value in freshValue.items():
                    resourceMapped[key] = value

                self.__resourcePool[k] = resourceMapped
                self.imageViewer.setIntoResourcePool(k, resourceMapped)

        return outMap

def main():
    argc = len(sys.argv)
    app = QtWidgets.QApplication(sys.argv)

    gStation = GroundStation()
    gStation.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
