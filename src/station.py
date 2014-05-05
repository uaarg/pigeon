#!/usr/bin/env python3
# Author: Cindy Xiao <dixin@ualberta.ca>, Emmanuel Odeke <odeke@ualberta.ca>

import os
import re
import sys
import time
import threading
import inspect
from PyQt5 import QtCore, QtWidgets, QtGui, QtMultimedia

import gcs # Generated module by running: pyuic5 gcs.ui > gcs.py

import utils # Local module
import Tag # Local module
import iconStrip # Local module
import DbLiason # Local module
import imageViewer # Local module
import mpUtils.JobRunner # Local module


curDirPath = os.path.abspath('.')
REPORTS_DIR = './reports'
ATTR_VALUE_REGEX_COMPILE = re.compile('([^\s]+)\s*=\s*([^\s]+)\s*', re.UNICODE)

DEFAULT_IMAGE_FORM_DICT = dict(
    phi=0.0, psi=0, theta=0, alt=0, author=utils.getDefaultUserName(), utm_east=0.0, time=0,
    utm_north=0, speed=0, image_width=1294.0, image_height=964.0, viewangle_horiz=21.733333,
    viewangle_vert=16.833333, pixel_per_meter=0, ppm_difference=0, course=0
)

class GroundStation(QtWidgets.QMainWindow):
    __jobRunner     = mpUtils.JobRunner.JobRunner()
    def __init__(self, dbHandler, parent=None):
        super(GroundStation, self).__init__(parent)

        self.ui_window = gcs.Ui_MainWindow()
        self.ui_window.setupUi(self)

        self.__resourcePool = dict()
        self.setDbHandler(dbHandler)

        self.initSyncCounters()
        self.initUI()

        self.initSaveSound()

        self.initLCDDisplays()
        self.initTimers()

        # Now load all content from the DB
        self.dbSync()

    def setDbHandler(self, dbHandler):
        self.__dbHandler = dbHandler

    def getDbHandler(self):
        return self.__dbHandler

    def initTimers(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.showCurrentTime)

        self.syncTimer = QtCore.QTimer(self)
        self.syncTimer.timeout.connect(self.querySyncStatus)
        self.syncTimer.start(5000)

        self.timer.start(1000)

    def initSyncCounters(self):
        self.__lastImageCount = 0
        self.__lastMarkerCount = 0

    def initLCDDisplays(self):
        self.__nowLCD = self.ui_window.nowLCDNumber
        self.__nowLCD.setDigitCount(8)

        self.__lastSyncLCD = self.ui_window.lastSyncLCDNumber
        self.__lastSyncLCD.setDigitCount(8)

        self.showCurrentTime()

    def getCurrentIcon(self, t):
        return 'icons/iconmonstr-xbox.png' if t & 1 else 'icons/iconmonstr-checkbox.png'

    def querySyncStatus(self):
        queryData = utils.produceAndParse(self.__dbHandler.imageHandler.getConn,
            dict(select='id,lastEditTime', limit=0, sort='lastEditTime_r')
        )
        if isinstance(queryData, dict):
            if hasattr(queryData, 'reason'):
                self.syncUpdateAction.setText(queryData['reason'])
            else:
                metaDict = queryData.get('meta', {})
                curImageCount = metaDict.get('count', 0)
                updateMsg = 'No new changes'
                self.__lastImageCount = len(self.__resourcePool)
                if curImageCount != self.__lastImageCount:
                    updateMsg = utils.itemComparisonInWords(curImageCount, self.__lastImageCount)

                self.syncUpdateAction.setText(updateMsg)
        print('querying about syncStatus')

    def showCurrentTime(self):
        time = QtCore.QTime.currentTime()
        text = time.toString('hh:mm:ss')
        self.__nowLCD.display(text)

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
            dbHandler=self.__dbHandler, parent=self.ui_window.fullSizeImageScrollArea
        )
        self.ui_window.fullSizeImageScrollArea.setWidget(self.imageViewer)

        self.imgAttrFrame = self.ui_window.imageAttributesFrame

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

        self.msgQBox = QtWidgets.QMessageBox(parent=self)

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

    def __preparePathsForDisplay(self, pathDictListTuple, onFinish=None):
        lastItem = None
        pathDictList = pathDictListTuple[0] if isinstance(pathDictListTuple, tuple) else pathDictListTuple
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

        if hasattr(onFinish, '__call__'):
            onFinish()

    def preparePathsForDisplay(self, dynaDictList, callback=None):
        return self.__preparePathsForDisplay(dynaDictList, callback)
        
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

        self.syncToolbar = self.ui_window.syncInfoToolbar
        self.syncToolbar.addAction(self.syncUpdateAction)

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


        imageTag = Tag.Tag(
            size=utils.DynaItem(dict(x=self.imgAttrFrame.width(), y=self.imgAttrFrame.height())),
            location=utils.DynaItem(dict(x=self.imgAttrFrame.x(), y=self.imgAttrFrame.y())),
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

        self.__iconB = 0
        self.syncUpdateAction = QtWidgets.QAction("&No new updates", self)

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
        if associatedTextFile != -1:
            print('associatedTextFile', associatedTextFile)
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

    def setSyncTime(self, *args):
        time = QtCore.QTime.currentTime()
        text = time.toString('hh:mm:ss')
        self.__lastSyncLCD.display(text)

    def dbSync(self):
        metaSaveDict = dict()
        result = self.preparePathsForDisplay(
            self.imageViewer.loadContentFromDb(metaSaveDict=metaSaveDict),
            callback=self.setSyncTime
        )
        print('After syncing', result)

        print('metaSaveDict', metaSaveDict)
        if isinstance(metaSaveDict, dict):
            # TODO: Memoize the time on the server to aid in versioning
            timeOnServer = metaSaveDict.get('currentTime', None)
            '''
            if timeOnServer is not None:
                strTime = time.ctime(timeOnServer)
                structOfTime = time.strptime(strTime)
                outStr = '{h}:{m}:{s}'.format(  
                    h=structOfTime.tm_hour, m=structOfTime.tm_min, s=structOfTime.tm_sec
                )
                self.__lastSyncLCD.display(outStr)
            '''

    def cleanUpAndExit(self):
        self.iconStrip.close()

        self.timer.close()
        self.lcd.close()

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
            qBox = QtWidgets.QMessageBox(parent=self)
            qBox.setText('FileDialog was not initialized')
            qBox.show()

    def pictureDropped(self, itemList):
        self.__normalizeFileAdding(itemList)

    def printCurrentImageData(self):
        print('printCurrentImageData')
        srcPath = self.ui_window.countDisplayLabel.text()
        key = utils.getLocalName(srcPath) or srcPath
        
        storedMap = self.__resourcePool.get(key, None)
        if storedMap:
            if not os.path.exists(REPORTS_DIR):
                try:
                    os.mkdir(REPORTS_DIR)
                except Exception as e:
                    print('\033[91m', e, '\033[00m')
                    return

            print('for', key, 'storedMap', storedMap)
            imageInfoPath = os.path.join(REPORTS_DIR, key + '-image.csv')
            imagesIn = markersIn = False
            with open(imageInfoPath, 'w') as f:
                keysCurrently = [k for k in storedMap.keys() if k != 'marker_set']
                f.write(','.join(keysCurrently))
                f.write('\n')
                f.write(','.join(str(storedMap[k]) for k in keysCurrently))
                f.write('\n')
                imagesIn = True

            markerSet = storedMap.get('marker_set', [])
            markerInfoPath = None

            if markerSet:
                markerInfoPath = os.path.join(REPORTS_DIR, key + '-markers.csv')
                with open(markerInfoPath, 'w') as g:
                    sampleElement = markerSet[0]
                    representativeKeys = sampleElement.keys()
                    g.write(','.join(representativeKeys))
                    g.write('\n')
                    for elem in markerSet:
                        g.write(','.join([str(elem[k]) for k in representativeKeys]))
                        g.write('\n')
                    markersIn = True
                    print('\033[94mWrote marker attributes to', markerInfoPath, '\033[00m')
       
            if (imagesIn or markersIn): 
                msg = 'Wrote: '
                if imagesIn:
                    msg += '\nimage information to: %s'%(imageInfoPath)
                if markersIn:
                    msg += '\nmarker information to: %s'%(markerInfoPath)

                print('\033[92m', msg, '\033[00m')
                if not hasattr(self.msgQBox, 'setText'):
                    self.msgQBox = QtWidgets.QMessageBox(parent=self)

                self.msgQBox.setText(msg)
                self.msgQBox.show()

    def addLocationData(self):
        if isinstance(self.locationDataDialog, QtWidgets.QFileDialog):
            self.locationDataDialog.show()
        else:
            qBox = QtWidgets.QMessageBox(parent=self)
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

    dbConnector = DbLiason.GCSHandler('http://127.0.0.1:8000/gcs')
    gStation = GroundStation(dbConnector)
    gStation.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
