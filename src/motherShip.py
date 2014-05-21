#!/usr/bin/env python3
# Author: Cindy Xiao <dixin@ualberta.ca>, Emmanuel Odeke <odeke@ualberta.ca>

import os
import re
import sys
import random
from PyQt5 import QtCore, QtWidgets, QtGui, QtMultimedia

import gcs # Generated module by running: pyuic5 gcs.ui > gcs.py

import Tag # Local module
import utils # Local module
import kmlUtil # Local module
import GPSCoord # Local module
import DbLiason # Local module
import iconStrip # Local module
import constants # Local module
import ImageDisplayer # Local module
import DirWatchManager # Local module
from fileOnCloudHandler import FileOnCloudHandler
import mpUtils.JobRunner # Local module

REPORTS_DIR = './reports'
ATTR_VALUE_REGEX_COMPILE = re.compile('([^\s]+)\s*=\s*([^\s]+)\s*', re.UNICODE)

defaultImageFormDict = dict(
    time=0, utm_north=0, speed=0, image_width=1294.0, image_height=964.0, course=0,
    phi=0.0, psi=0, theta=0, alt=0, author=utils.getDefaultUserName(), utm_east=0.0,
    viewangle_horiz=21.733333, viewangle_vert=16.833333, pixel_per_meter=0, ppm_difference=0
)

class GroundStation(QtWidgets.QMainWindow):
    __jobRunner     = mpUtils.JobRunner.JobRunner()
    def __init__(self, dbHandler, parent=None, eavsDroppingMode=False):
        super(GroundStation, self).__init__(parent)

        self.ui_window = gcs.Ui_MainWindow()
        self.ui_window.setupUi(self)

        self.__resourcePool = dict()
        self.__keyToMarker = dict()
        self.__dirWatcher = DirWatchManager.DirWatchManager(
            onFreshPaths=lambda p: self.pictureDropped([p]), onStalePaths=lambda a: a
        )
        self.__iconMemMap = dict()
        self.initStrip()

        self.inEavsDroppingMode = eavsDroppingMode
        self.setDbHandler(dbHandler)

        self.initUI()
        self.initSaveSound()
        self.initLCDDisplays()
        self.initTimers()

        # Now load all content from the DB
        self.dbSync()

    def setDbHandler(self, dbHandler):
        self.__dbHandler = dbHandler

        self.__uploadHandler = FileOnCloudHandler(os.path.dirname(self.__dbHandler.baseUrl))

    def getDbHandler(self):
        return self.__dbHandler

    def initTimers(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.showCurrentTime)

        self.syncTimer = QtCore.QTimer(self)
        func = self.querySyncStatus
        timeout = 5000
        if self.inEavsDroppingMode:
            func = self.fullDBSync
            timeout = 10000

        print('func', func, 'timeout', timeout)

        self.syncTimer.timeout.connect(func)
        self.syncTimer.start(timeout)

        self.timer.start(1000)

    def initLCDDisplays(self):
        self.__nowLCD = self.ui_window.nowLCDNumber
        self.__nowLCD.setDigitCount(8)

        self.__lastSyncLCD = self.ui_window.lastSyncLCDNumber
        self.__lastSyncLCD.setDigitCount(8)

        self.showCurrentTime()

    def fullDBSync(self):
        print('FullDBSync')

    def getIcon(self, key):
        memIcon = self.__iconMemMap.get(key, None)
        if memIcon is None:
            memIcon = QtGui.QIcon(self.iconStrip.addPixMap(key))
            self.__iconMemMap[key] = memIcon
        return memIcon

    def querySyncStatus(self):
        syncStatus, dbImageCount = self.findSyncStatus(self.ui_window.pathDisplayLabel.text())
        if syncStatus == constants.NO_CONNECTION:
            self.connectionStatusAction.setIcon(self.getIcon('icons/iconmonstr-connection-bad.png'))
            self.connectionStatusAction.setText('&Not connected')

            self.syncUpdateAction.setText('Failed to connect')

            self.syncIconAction.setIcon(self.getIcon('icons/iconmonstr-cloud-unsyncd.png'))
            self.syncIconAction.setText('&Current item not in sync\nHit Ctrl+R for sync')
        elif dbImageCount < 0:
            print('Failed to get imageCount', dbImageCount, syncStatus)
        else:
            updateMsg = 'No new changes'
            localImageCount = len(self.__resourcePool)
            diff = dbImageCount - localImageCount
            if diff:
                absDiff = abs(diff)
                plurality = 'image' if absDiff == 1 else 'images' 
                if diff > 0:
                    updateMsg = '%d %s available for downloading'%(absDiff, plurality)
                else:
                    updateMsg = '%d unsaved %s'%(absDiff, plurality)

            self.syncUpdateAction.setText(updateMsg)
            if syncStatus == constants.IS_IN_SYNC:
                self.syncIconAction.setIcon(self.getIcon('icons/iconmonstr-cloud-syncd.png'))
                self.syncIconAction.setText('&Current item in sync')
            else:
                self.syncIconAction.setIcon(self.getIcon('icons/iconmonstr-cloud-unsyncd.png'))
                self.syncIconAction.setText('&Current item not in sync')

            self.connectionStatusAction.setIcon(
                self.getIcon('icons/iconmonstr-connection-good.png')
            )
            self.connectionStatusAction.setText('&Connected')

    def findSyncStatus(self, path=None): 
        queryDict = dict(format='short', uri=path, select='lastTimeEdit')

        parsedResponse = utils.produceAndParse(
          func=self.__dbHandler.imageHandler.getConn, dataIn=queryDict
        )

        data = None
        status_code = 400
        countOnCloud = -1

        if hasattr(parsedResponse, 'get'):
            status_code = parsedResponse.get('status_code', 400)
            data = parsedResponse.get('data', None)
            meta = parsedResponse.get('meta', None)
            if hasattr(meta, 'keys'): 
                countOnCloud = meta.get('count', -1)

        if status_code != 200:
            return constants.NO_CONNECTION, countOnCloud

        elif data:
            memAttrMap = self.getImageAttrsByKey(path)

            memId = int(memAttrMap.get('id', -1))
            memlastTimeEdit = float(memAttrMap.get('lastTimeEdit', -1))

            itemInfo = data[0]
            idOnCloud = int(itemInfo.get('id', -1))
            imageOnCloudlastTimeEdit = float(itemInfo['lastTimeEdit'])

            if idOnCloud < 1:
                print('\033[48mThis data is not present on cloud, path:', path, '\033[00m')
                return constants.IS_FIRST_TIME_SAVE, countOnCloud

            elif imageOnCloudlastTimeEdit > memlastTimeEdit:
                print('\033[47mDetected a need for saving here since')
                print('your last memoized local editTime was', memlastTimeEdit)
                print('Most recent db editTime is\033[00m', imageOnCloudlastTimeEdit)
                return constants.IS_OUT_OF_SYNC, countOnCloud
            else:
                print('\033[42mAll good! No need for an extra save for',\
                     path, '\033[00m'
                )
                return constants.IS_IN_SYNC, countOnCloud
        else:
            print("\033[41mNo data back from querying about lastTimeEdit\033[00m")
            #TODO: Handle this special case
            return constants.NO_DATA_BACK, countOnCloud

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
        self.initImageDisplayer()

        self.ui_window.pathDisplayLabel.show()

    def initImageDisplayer(self):
        self.ImageDisplayer = ImageDisplayer.ImageDisplayer(
            parent=self.ui_window.fullSizeImageScrollArea,
            onDeleteMarkerFromDB=self.deleteMarkerFromDB
        )
        self.ui_window.fullSizeImageScrollArea.setWidget(self.ImageDisplayer)

        self.imgAttrFrame = self.ui_window.imageAttributesFrame

    def initStrip(self):
        self.iconStrip = iconStrip.IconStrip(self)
        self.ui_window.thumbnailScrollArea.setWidget(self.iconStrip)
        self.iconStrip.setOnItemClick(self.renderImage)

    def createFileDialog(self, caption, connectFunc, fileMode, baseDir=None, nameFilter=None):
        __fDialog = QtWidgets.QFileDialog(caption=caption)
        __fDialog.setFileMode(fileMode) # Multiple files can be selected
        __fDialog.filesSelected.connect(connectFunc)
        if os.path.exists(baseDir):
            __fDialog.setDirectory(baseDir)

        if nameFilter and isinstance(nameFilter, str):
            __fDialog.setNameFilter(nameFilter)

        return __fDialog

    def initFileDialogs(self):
        self.fileDialog = self.createFileDialog(
            'Add captured Images', self.pictureDropped, QtWidgets.QFileDialog.ExistingFiles,
            './data/processed', 'All image files (*.png *.jpg *.jpeg *.gif)'
        )

        self.dirWatchFileDialog = self.createFileDialog(    
            'Select directories to watch', self.watchDirs,
            QtWidgets.QFileDialog.Directory, '../'
        )
        self.dirWatchFileDialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly)

        self.locationDataDialog = self.createFileDialog(
            'Add telemetry files', self.processAssociatedDataFiles,
            QtWidgets.QFileDialog.ExistingFiles, './data/info', 'All text files (*.txt)'
        )

        self.msgQBox = QtWidgets.QMessageBox(parent=self)

    def __normalizeFileAdding(self, paths):
        # Ensuring that paths added are relative to a common source eg
        # Files from folder ./data will be present on all GCS stations
        # so only the relative path not absolute path should be added
        normalizedPaths = []
        for path in paths:
            normalizedPaths.append(dict(uri=path, title=path))

        self.preparePathsForDisplay(normalizedPaths)

    def __preparePathsForDisplay(self, pathDictList, onFinish=None):
        lastItem = None

        for index, pathDict in enumerate(pathDictList):
            path = pathDict.get('uri', None)

            if path not in self.__resourcePool:
                self.iconStrip.addIconItem(path, self.renderImage)
                self.__resourcePool[path] = True

            self.__resourcePool[path] = pathDict

            lastItem = path
            print('path', path)

        # Display the last added item
        self.renderImage(lastItem)

        if lastItem: # Sound only if there is an item to be displayed
            self.__saveSound.play()
        else:
            self.querySyncStatus()

        if hasattr(onFinish, '__call__'):
            onFinish()

    def preparePathsForDisplay(self, dynaDictList, onFinish=None):
        if dynaDictList:
            return self.__preparePathsForDisplay(dynaDictList, onFinish=onFinish)
        
    def initToolBar(self):
        self.toolbar  = self.ui_window.toolBar;

        self.toolbar.addAction(self.editCurrentImageAction)
        self.toolbar.addAction(self.addLocationDataAction)
        self.toolbar.addAction(self.popCurrentImageAction)
        self.toolbar.addAction(self.findImagesAction)
        self.toolbar.addAction(self.dirWatchAction)
        self.toolbar.addAction(self.syncCurrentItemAction)
        self.toolbar.addAction(self.dbSyncAction)
        self.toolbar.addAction(self.printCurrentImageDataAction)
        self.toolbar.addAction(self.exitAction)

        self.syncToolbar = self.ui_window.syncInfoToolbar
        self.syncToolbar.addAction(self.syncIconAction)
        self.syncToolbar.addAction(self.syncUpdateAction)
        self.syncToolbar.addAction(self.connectionStatusAction)

    def getImageAttrsByKey(self, key):
        print('key', key)
        memDict = self.__resourcePool.get(key, None)
        if memDict is None:
            memDict = dict(title=key)
            self.__resourcePool[key] = memDict

        return memDict

    def editCurrentImage(self):
        print('Editing Current Image', self.ui_window.pathDisplayLabel.text())

        srcPath = self.ui_window.pathDisplayLabel.text()

        stateDict = self.getImageAttrsByKey(srcPath)

        entryList = []

        for index, entry in enumerate(defaultImageFormDict.keys()):
            textExtracted = stateDict.get(entry, None)
            if textExtracted is None:
                textExtracted = defaultImageFormDict[entry]

            entryList.append(
                utils.DynaItem(dict(
                    title=entry, isMultiLine=False, labelLocation=(index, 0,),
                    isEditable=True, entryLocation=(index, 1,), entryText=str(textExtracted)
                )
            ))


        imageTag = Tag.Tag(
            size=utils.DynaItem(dict(x=self.imgAttrFrame.width(), y=self.imgAttrFrame.height())),
            location=utils.DynaItem(dict(x=self.imgAttrFrame.x(), y=self.imgAttrFrame.y())),
            title='Location data for: ' + utils.getLocalName(self.ui_window.pathDisplayLabel.text()),
            onSubmit=self.saveCurrentImageContent,
            entryList=entryList
        )
        imageTag.show()

    def saveCurrentImageContent(self, content):
        print('Saving currentImage content', content)
        curPath = self.ui_window.pathDisplayLabel.text()
        
        currentMap = self.__resourcePool.get(curPath, {})

        if isinstance(content, dict):
            for k, v in content.items():
                currentMap[k] = v

        currentMap.setdefault('uri', curPath)
        currentMap.setdefault('title', curPath)

        # Getting the original ids in
        saveResponse = self.saveImageToDB(key, currentMap)

    def saveImageToDB(self, key, attrDict):
        print('Saving image to DB', key, attrDict)

    def initActions(self):
        self.popCurrentImageAction = QtWidgets.QAction(self.getIcon('icons/recyclebin_close.png'),
            '&Remove currentImage', self
        )
        self.popCurrentImageAction.triggered.connect(self.handleItemPop)

        # Synchronization with DB
        self.syncCurrentItemAction = QtWidgets.QAction(
            self.getIcon('icons/iconmonstr-upload.png'),'&Save to Cloud', self
        )
        self.syncCurrentItemAction.setShortcut('Ctrl+S')
        self.syncCurrentItemAction.triggered.connect(self.syncCurrentItem)

        self.dbSyncAction = QtWidgets.QAction(self.getIcon('icons/iconmonstr-save.png'), '&Sync from Cloud', self)
        self.dbSyncAction.triggered.connect(self.dbSync)
        self.dbSyncAction.setShortcut('Ctrl+R')

        self.dirWatchAction = QtWidgets.QAction(self.getIcon('icons/iconmonstr-eye.png'), '&Select directories to watch', self)
        self.dirWatchAction.triggered.connect(self.dirWatchTrigger)

        self.connectionStatusAction = QtWidgets.QAction('&Connection Status', self)

        self.syncUpdateAction = QtWidgets.QAction('&Updates Info', self)
        self.syncIconAction = QtWidgets.QAction('&SyncStatus', self)

        # Exit
        self.exitAction = QtWidgets.QAction(self.getIcon('icons/exit.png'), '&Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(self.cleanUpAndExit)

        # Finding and adding images
        self.findImagesAction = QtWidgets.QAction(
            self.getIcon('icons/iconmonstr-folder.png'), '&Add Images', self
        )
        self.findImagesAction.setShortcut('Ctrl+O')
        self.findImagesAction.triggered.connect(self.findImages)
        self.editCurrentImageAction = QtWidgets.QAction(
            self.getIcon('icons/iconmonstr-picture-edit.png'), '&Edit Current Image', self
        )
        self.editCurrentImageAction.triggered.connect(self.editCurrentImage)
        self.editCurrentImageAction.setShortcut('Ctrl+E')

        self.addLocationDataAction = QtWidgets.QAction(
            self.getIcon('icons/iconmonstr-note.png'), '&Add Telemetry Info', self
        )
        self.addLocationDataAction.triggered.connect(self.addLocationData)

        self.printCurrentImageDataAction = QtWidgets.QAction(
            self.getIcon('icons/iconmonstr-printer.png'), '&Print Current Image Info', self
        )
        self.printCurrentImageDataAction.triggered.connect(self.printCurrentImageData)

    def handleItemPop(self, currentItem=None):
        pathOnDisplay = self.ui_window.pathDisplayLabel.text()
        popd = self.__resourcePool.pop(pathOnDisplay, None)
        mpopd = self.__keyToMarker.pop(pathOnDisplay, None)
        nextPath = self.iconStrip.popIconItem(currentItem)

        self.renderImage(nextPath)

    def deleteMarkerFromDB(self, x, y):
        print('deleting ', x, y, 'from DB')

    def handleSync(self, path):
        elemData = self.getImageAttrsByKey(path)
        elemAttrDict = dict((k, v) for k, v in elemData.items() if k != 'marker_set')
        pathSelector = elemData.get('uri', '') or elemData.get('title', '')

        basename = os.path.basename(pathSelector)
        localizedDataPath = os.sep.join(('.', 'data', 'processed', basename,))

        queryDict = dict(uri=localizedDataPath)
        print('queryDict', queryDict)
        dQuery = self.__uploadHandler.jsonParseResponse(
            self.__uploadHandler.getManifest(queryDict)
        )
        print('dQuery', dQuery)

        statusCode = dQuery['status_code']
        if statusCode == 200:
            needsUpload = True
            data = dQuery.get('data', None)
            if data:
                # Now time for a size inquiry
                print('data', data)
                if utils.pathExists(pathSelector):
                    statDict = os.stat(pathSelector)
                    randSample = random.sample(data, 1)[0]
                    queriedSize = randSample.get('size', -1)
                    if int(statDict.st_size) == int(queriedSize):
                        # Simple litmus test. In the future will add checksum checks
                        needsUpload = False

            if needsUpload:
                queryDict['author'] = utils.getDefaultUserName()
                print('\033[92mOn Upload',
                    self.__uploadHandler.uploadFileByPath(pathSelector, **queryDict),
                '\033[00m')


        if not utils.pathExists(localizedDataPath):
            dlPath = self.downloadFile(pathSelector)
            if dlPath:
                localizedDataPath = dlPath

        if pathSelector != localizedDataPath:
            self.__jobRunner.run(   
                self.__swapOutResourcePaths, None, None, pathSelector, localizedPath
            )

        elemAttrDict['uri'] = localizedDataPath
        print('\033[91mpathSelector', pathSelector, localizedDataPath, elemAttrDict, '\033[00m')

        memId = int(elemData.get('id', -1))
        methodName = 'putConn'

        if memId <= 0:
            methodName = 'postConn'
            elemAttrDict.pop('id', None) # Let the DB decide what Id to assign to you

        # print('elemAttrDict', elemAttrDict)
        func = getattr(self.__dbHandler.imageHandler, methodName)
        parsedResponse = utils.produceAndParse(func, elemAttrDict)
        idFromDB = parsedResponse.get('id', -1)
       
        pathDict = self.__resourcePool.get(path, None) 
        if pathDict is None:
            pathDict = dict(uri=localizedDataPath)

        pathDict['id'] = idFromDB
        print('idFromDB', path, parsedResponse)
        self.__resourcePool[path] = pathDict
            
        return localizedDataPath

    def __swapOutResourcesPaths(self, *args):
        oldPath, newPath = args
        popd = self.__resourcePool.pop(oldPath, None)
        if popd is not None:
            self.__resourcePool[newPath] = popd
        mPop = self.__keyToMarker.pop(oldPath, None)
        if mPop is not None: 
            self.__keyToMarker[newPath] = mPop 

    def bulkSaveMarkers(self, associatedKey, markerDictList):
        print('associatedKey', associatedKey, markerDictList)
    
    def syncCurrentItem(self):
        pathOnDisplay = self.ui_window.pathDisplayLabel.text()
        print('Syncing current item', pathOnDisplay)

        localizedPath = self.handleSync(pathOnDisplay)
        if localizedPath:
            self.iconStrip.editStatusTipByKey(pathOnDisplay, localizedPath)

            # Swap out this path
            self.__jobRunner.run(
                self.__swapOutResourcesPaths, None, None, pathOnDisplay, localizedPath
            )
            pathOnDisplay = localizedPath

        dbConfirmation = self.syncFromDB(uri=pathOnDisplay)
        associatedMarkerMap = self.__keyToMarker.get(localizedPath, {})

        markerDictList = []
        for m in associatedMarkerMap.values():
            markerDictList.append(dict(
                getter=m.induceSave, onSuccess=m.refreshAndToggleSave,
                onFailure=m.toggleUnsaved
            ))
            
        # Now the associated markers
        bulkSaveResults = self.bulkSaveMarkers(pathOnDisplay, markerDictList)

        if bulkSaveResults:
            associatedImageId = int(bulkSaveResults.get('associatedImageId', -1))
            print('associatedImageId', associatedImageId)

    def syncFromDB(self, **attrs):
        print('attrs', attrs)

    def setSyncTime(self, *args):
        curTime = QtCore.QTime.currentTime()
        text = curTime.toString('hh:mm:ss')
        self.__lastSyncLCD.display(text)

    def renderImage(self, path):
        memPixMap = self.iconStrip.addPixMap(path)
        markerSet = self.__resourcePool.get(path, {}).get('marker_set', [])
        markerMap = self.__keyToMarker.setdefault(path, {})
        if self.ImageDisplayer.renderImage(path, markerSet, markerMap, memPixMap):
            self.ui_window.pathDisplayLabel.setText(path)
            associatedTextFile = self.getInfoFileNameFromImagePath(path)
            if associatedTextFile != -1:
                print('associatedTextFile', associatedTextFile)
                # ,iself.processAssociatedDataFiles([associatedTextFile])
                geoDataDict = GPSCoord.getInfoDict(associatedTextFile)
                self.ImageDisplayer.extractSetGeoData(geoDataDict)

        print('RenderImage', path)

    def dbSync(self):
        print('DBSync')

    def cleanUpAndExit(self):
        self.__dirWatcher.close()
        self.iconStrip.close()

        self.fileDialog.close()
        self.locationDataDialog.close()

        self.__nowLCD.close()
        self.__lastSyncLCD.close()

        self.ImageDisplayer.close()

        print('close', self.__jobRunner.close())
        print(self, 'closing')

        self.close()

    def dirWatchTrigger(self):
        if isinstance(self.dirWatchFileDialog, QtWidgets.QFileDialog):
            self.dirWatchFileDialog.show()
        else:
            self.msgQBox.setText('DirWatch FileDialog was not initialized')
            self.msgQBox.show()

    def watchDirs(self, selectedDirPaths):
        print('Selected directories', selectedDirPaths)
        for dPath in selectedDirPaths:
            dWatcher = self.__dirWatcher.watchDir(dPath)

    def findImages(self):
        if isinstance(self.fileDialog, QtWidgets.QFileDialog):
            self.fileDialog.show()
        else:
            self.msgQBox.setText('FileDialog was not initialized')
            self.msgQBox.show()

    def pictureDropped(self, itemList):
        self.__normalizeFileAdding(itemList)

    def printCurrentImageData(self):
        print('printCurrentImageData')
        srcPath = self.ui_window.pathDisplayLabel.text()
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
            exclusiveOfMarkerSetKeys = [k for k in storedMap.keys() if k != 'marker_set']
            with open(imageInfoPath, 'w') as f:
                f.write(','.join(exclusiveOfMarkerSetKeys))
                f.write('\n')
                f.write(','.join(str(storedMap[k]) for k in exclusiveOfMarkerSetKeys))
                f.write('\n')
                
                imagesIn = True
                
            markerSet = storedMap.get('marker_set', [])
            kmlPath = os.path.join(REPORTS_DIR, key + '.kml')
            with open(kmlPath, 'w') as h:
                fmtdTree = dict((k, storedMap[k]) for k in exclusiveOfMarkerSetKeys)
                fmtdTree['marker_set'] = [dict(Marker=m) for m in markerSet]
                h.write(kmlUtil.kmlDoc(fmtdTree)) and print('\033[95mWrote KML info to', kmlPath)

            markerInfoPath =  None
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
                    msg += '\nCSV image information to: %s'%(imageInfoPath)
                if markersIn:
                    msg += '\nCSV marker information to: %s'%(markerInfoPath)
                    msg += '\nKML marker information to: %s'%(kmlPath)

                print('\033[92m', msg, '\033[00m')
                if not hasattr(self.msgQBox, 'setText'):
                    self.msgQBox = QtWidgets.QMessageBox(parent=self)

                self.msgQBox.setText(msg)
                self.msgQBox.show()

    def addLocationData(self):
        if isinstance(self.locationDataDialog, QtWidgets.QFileDialog):
            self.locationDataDialog.show()
        else:
            self.msgQBox.setText('LocationData fileDialog was not initialized')
            self.msgQBox.show()

    def processAssociatedDataFiles(self, pathList, **kwargs):
        return self.__jobRunner.run(
            self.__processAssociatedDataFiles, None, print, pathList, **kwargs
        )

    def __processAssociatedDataFiles(self, pathList, **kwargs):
        print('args', kwargs, 'pathList', pathList)
        outMap = dict()
        for path in pathList:
            key = utils.getLocalName(path) or path
            outMap[key] = GPSCoord.getInfoDict(path)
            memResource = self.__resourcePool.get(key, {})
            outMap[key]['author'] = utils.getDefaultUserName()

        # Time to swap out the fields and replace
        for k in outMap:
            self.editLocalContent(k, outMap[k])

        return outMap

    def editLocalContent(self, key, outMap):
        memMap = self.__resourcePool.get(key, dict())
        for k, v in outMap.items():
            memMap[k] = v

        return memMap

    def getInfoFileNameFromImagePath(self, fPath):
        if not fPath:
            return -1

        splitPath = os.path.split(fPath)
        parentDir, axiom = os.path.split(fPath)
        seqIDExtSplit = axiom.split('.')

        if not (seqIDExtSplit and len(seqIDExtSplit) == 2):
            print('Erraneous format, expecting pathId and extension eg from 12.jpg')
            return -1

        seqID, ext = seqIDExtSplit
        if ext != 'jpg':
            print('Could not find an info file associated with the image', fPath)
            return -1

        # Scheme assumed is that directories [info, data] have the same parent
        grandParentDir, endAxiom = os.path.split(parentDir)

        infoFilename = os.sep.join([grandParentDir, 'info', seqID + '.txt'])
        return infoFilename

def main():
    app = QtWidgets.QApplication(sys.argv)
    args, options = utils.cliParser()

    # Time to get address that the DB can be connected to via
    dbAddress = '{ip}:{port}/gcs'.format(ip=args.ip.strip('/'), port=args.port.strip('/'))
    eavsDroppingMode = args.eavsDroppingMode
    print('Connecting via: \033[92m dbAddress', dbAddress, eavsDroppingMode, '\033[00m')
       
    dbConnector = DbLiason.GCSHandler(dbAddress)
    gStation = GroundStation(dbHandler=dbConnector, eavsDroppingMode=eavsDroppingMode)

    gStation.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
