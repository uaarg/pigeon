#!/usr/bin/env python3
# Author: Cindy Xiao <dixin@ualberta.ca>, Emmanuel Odeke <odeke@ualberta.ca>

import os
import re
import sys
from PyQt5 import QtCore, QtWidgets, QtGui, QtMultimedia

import gcs # Generated module by running: pyuic5 gcs.ui > gcs.py

import Tag # Local module
import utils # Local module
import kmlUtil # Local module
import GPSCoord # Local module
import DbLiason # Local module
import iconStrip # Local module
import constants # Local module
import SyncManager # Local module
import ImageDisplayer # Local module
import DirWatchManager # Local module
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
        self.syncManager = SyncManager.SyncManager(dbHandler)
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
        self.dbSync()

        # Cycle through each one of the images
        iconStripManifest = self.iconStrip.itemDictManifest()
        for path in iconStripManifest:
            curItemSyncStatus = self.syncManager.needsSync(path=path)
            if curItemSyncStatus != constants.IS_IN_SYNC:
                self.handleItemPop(path)

    def getIcon(self, key):
        memIcon = self.__iconMemMap.get(key, None)
        if memIcon is None:
            memIcon = QtGui.QIcon(key)
            self.__iconMemMap[key] = memIcon
        return memIcon

    def querySyncStatus(self):
        queryData = utils.produceAndParse(self.__dbHandler.imageHandler.getConn,
            dict(select='id,lastEditTime', limit=0, sort='lastEditTime_r')
        )
        if isinstance(queryData, dict):
            statusCode = queryData.get('status_code', 400)
            if statusCode != 200 or hasattr(queryData, 'reason'):
                self.connectionStatusAction.setIcon(self.getIcon('icons/iconmonstr-connection-bad.png'))
                self.connectionStatusAction.setText('&Not connected')

                self.syncUpdateAction.setText('Failed to connect')

                self.syncIconAction.setIcon(self.getIcon('icons/iconmonstr-cloud-unsyncd.png'))
                self.syncIconAction.setText('&Current item not in sync\nHit Ctrl+R for sync')
            else:
                metaDict = queryData.get('meta', {})
                dbImageCount = metaDict.get('count', 0)
                updateMsg = 'No new changes'
                localImageCount = len(self.__resourcePool)
                # print('dbImageCount', dbImageCount, 'lastImageCount', localImageCount)
                diff = dbImageCount - localImageCount
                if diff:
                    absDiff = abs(diff)
                    plurality = 'image' if absDiff == 1 else 'images' 
                    if diff > 0:
                        updateMsg = '%d %s available for downloading'%(absDiff, plurality)
                    else:
                        updateMsg = '%d unsaved %s'%(absDiff, plurality)

                curItemSyncStatus = self.syncManager.needsSync(path=self.ui_window.countDisplayLabel.text())
                if curItemSyncStatus == constants.IS_IN_SYNC:
                    self.syncIconAction.setIcon(self.getIcon('icons/iconmonstr-cloud-syncd.png'))
                    self.syncIconAction.setText('&Current item in sync')
                else:
                    self.syncIconAction.setIcon(self.getIcon('icons/iconmonstr-cloud-unsyncd.png'))
                    self.syncIconAction.setText('&Current item not in sync')

                self.syncUpdateAction.setText(updateMsg)
                self.connectionStatusAction.setIcon(self.getIcon('icons/iconmonstr-connection-good.png'))
                self.connectionStatusAction.setText('&Connected')

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
        self.initStrip()

        self.ui_window.countDisplayLabel.show()

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
            'Add captured Images', self.pictureDropped, QtWidgets.QFileDialog.ExistingFiles, './data/processed',
            'All image files (*.png *.jpg *.jpeg *.gif)'   
        )

        self.dirWatchFileDialog = self.createFileDialog(    
            'Select directories to watch', self.watchDirs, QtWidgets.QFileDialog.Directory, '../'
        )
        self.dirWatchFileDialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly)

        self.locationDataDialog = self.createFileDialog(
            'Add telemetry files', self.processAssociatedDataFiles, QtWidgets.QFileDialog.ExistingFiles, './data/info', 'All text files (*.txt)'
        )

        self.msgQBox = QtWidgets.QMessageBox(parent=self)

    def __normalizeFileAdding(self, paths):
        # Ensuring that paths added are relative to a common source eg
        # Files from folder ./data will be present on all GCS stations
        # so only the relative path not absolute path should be added
        normalizedPaths = []
        for path in paths:
            if path.find(curDirPath) >= 0:
                path = '.' + path.split(curDirPath)[1]

            normalizedPaths.append(dict(uri=path, title=path))

        self.preparePathsForDisplay(normalizedPaths)

    def __preparePathsForDisplay(self, pathDictList, onFinish=None):
        lastItem = None

        for index, pathDict in enumerate(pathDictList):
            path = pathDict.get('uri', None)
            key = utils.getLocalName(path) or path
   
            if key not in self.__resourcePool:
                self.iconStrip.addIconItem(path, self.renderImage)
                self.__resourcePool[key] = True

            self.renderImage(path)
            self.__resourcePool[key] = pathDict

            if lastItem is None:
                lastItem = path

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

    def editCurrentImage(self):
        print('Editing Current Image', self.ui_window.countDisplayLabel.text())

        srcPath = self.ui_window.countDisplayLabel.text()

        key = utils.getLocalName(srcPath) or srcPath
        stateDict = self.syncManager.getImageAttrsByKey(key)

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
        outDict = dict(
            id=currentMap.get('id', -1), uri=currentMap.get('uri', curPath), title=curPath
        )

        for k, v in content.items():
            outDict[k] = v

        # Getting the original ids in
        saveResponse = self.syncManager.saveImageToDB(key, outDict, needsCloudSave=True)
        # print('saveResponse', saveResponse)

    def initActions(self):
        self.popCurrentImageAction = QtWidgets.QAction(self.getIcon('icons/recyclebin_close.png'),
            "&Remove currentImage", self
        )
        self.popCurrentImageAction.triggered.connect(self.handleItemPop)

        # Synchronization with DB
        self.syncCurrentItemAction = QtWidgets.QAction(
            self.getIcon('icons/iconmonstr-upload.png'),"&Save to Cloud", self
        )
        self.syncCurrentItemAction.setShortcut('Ctrl+S')
        self.syncCurrentItemAction.triggered.connect(self.syncCurrentItem)

        self.dbSyncAction = QtWidgets.QAction(self.getIcon('icons/iconmonstr-save.png'), "&Sync from Cloud", self)
        self.dbSyncAction.triggered.connect(self.dbSync)
        self.dbSyncAction.setShortcut('Ctrl+R')

        self.dirWatchAction = QtWidgets.QAction(self.getIcon('icons/iconmonstr-eye.png'), "&Select directories to watch", self)
        self.dirWatchAction.triggered.connect(self.dirWatchTrigger)

        self.connectionStatusAction = QtWidgets.QAction("&Connection Status", self)

        self.syncUpdateAction = QtWidgets.QAction("&Updates Info", self)
        self.syncIconAction = QtWidgets.QAction("&SyncStatus", self)

        # Exit
        self.exitAction = QtWidgets.QAction(self.getIcon('icons/exit.png'), "&Exit", self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(self.cleanUpAndExit)

        # Finding and adding images
        self.findImagesAction = QtWidgets.QAction(
            self.getIcon('icons/iconmonstr-folder.png'), "&Add Images", self
        )
        self.findImagesAction.setShortcut('Ctrl+O')
        self.findImagesAction.triggered.connect(self.findImages)
        self.editCurrentImageAction = QtWidgets.QAction(
            self.getIcon('icons/iconmonstr-picture-edit.png'), "&Edit Current Image", self
        )
        self.editCurrentImageAction.triggered.connect(self.editCurrentImage)
        self.editCurrentImageAction.setShortcut('Ctrl+E')

        self.addLocationDataAction = QtWidgets.QAction(
            self.getIcon('icons/iconmonstr-note.png'), "&Add Telemetry Info", self
        )
        self.addLocationDataAction.triggered.connect(self.addLocationData)

        self.printCurrentImageDataAction = QtWidgets.QAction(
            self.getIcon('icons/iconmonstr-printer.png'), "&Print Current Image Info", self
        )
        self.printCurrentImageDataAction.triggered.connect(self.printCurrentImageData)

    def handleItemPop(self, currentItem=None):
        if not currentItem:
            currentItem = self.ui_window.countDisplayLabel.text()

        nextItemOnDisplay = None
        print('itemPop', currentItem)

        if currentItem:
            self.syncManager.deleteImageByKeyFromDB(
                self.syncManager.mapToLocalKey(currentItem), isGlobalDelete=True
            )
            nextItemOnDisplay = self.iconStrip.popIconItem(currentItem, None)
            key = utils.getLocalName(currentItem) or currentItem
            print('popping', self.__resourcePool.pop(key, None))

        self.renderImage(nextItemOnDisplay)

    def deleteMarkerFromDB(self, x, y):
        key = utils.getLocalName(self.ui_window.countDisplayLabel.text())
        return self.syncManager.deleteMarkerByAttrsFromDB(
            dict(associatedImage_id=self.syncManager.getImageId(key), x=x, y=y)
        )

    def eraseMarkersByKey(self, key):
        # We need to create a copy of keys of a dict
        # that we shall be popping from to avoid data
        # contention issues
        childMap = self.__keyToMarker.get(key, {})
        markerCopy = list(childMap.keys())[:] 
        for mKey in markerCopy:
            mk = childMap[mKey]
            if mk:
                print(mk.memComments)
                mk.erase(mk.x, mk.y, needsFlush=False)

    def syncCurrentItem(self):
        pathOnDisplay = self.ui_window.countDisplayLabel.text()
        localKey = self.syncManager.mapToLocalKey(pathOnDisplay)

        localizedPath = self.syncManager.syncImageToDB(localKey)
        if localizedPath:
            self.iconStrip.editStatusTipByKey(pathOnDisplay, localizedPath)
            pathOnDisplay = localizedPath

        dbConfirmation = self.syncManager.syncFromDB(uri=pathOnDisplay)
 
        associatedMarkerMap = self.__keyToMarker.get(localKey, {})
        markerDictList = []
        for m in associatedMarkerMap.values():
            markerDictList.append(
                dict(getter=m.induceSave, onSuccess=m.refreshAndToggleSave, onFailure=m.toggleUnsaved)
            )
   
        # Now the associated markers
        bulkSaveResults = self.syncManager.bulkSaveMarkers(localKey, markerDictList)

        if bulkSaveResults:
            associatedImageId = int(bulkSaveResults.get('associatedImageId', -1))
            if associatedImageId > 0:
                syncFromDBStatus = self.syncManager.syncFromDB(
                    qId=associatedImageId, metaDict=None
                )
                print('associatedImageId', associatedImageId)

        self.renderImage(pathOnDisplay)
        
    def setSyncTime(self, *args):
        curTime = QtCore.QTime.currentTime()
        text = curTime.toString('hh:mm:ss')
        self.__lastSyncLCD.display(text)

    def renderImage(self, path):
        localKey = self.syncManager.mapToLocalKey(path)
        markerSet = self.syncManager.getMarkerSetByKey(localKey)

        outDict = self.__keyToMarker.get(localKey, None)
        if outDict is None:
            outDict = dict()
            self.__keyToMarker[localKey] = outDict
        
        if not utils.pathExists(path): 
            localizedPath = self.syncManager.downloadFile(localKey)
            if localizedPath: # Path successfully written to
                print('New localized path', localizedPath)
                path = localizedPath

        memPixMap = self.iconStrip.addPixMap(path)
        print('memPixMap', memPixMap.isNull())
        self.ImageDisplayer.renderImage(
            path, markerSet=markerSet, currentMap=outDict, pixMap=memPixMap
        )

        associatedTextFile = self.getInfoFileNameFromImagePath(path)
        if associatedTextFile != -1:
            print('associatedTextFile', associatedTextFile)
            self.processAssociatedDataFiles([associatedTextFile])
            geoDataDict = GPSCoord.getInfoDict(associatedTextFile)
            self.ImageDisplayer.extractSetGeoData(geoDataDict)

        self.ui_window.countDisplayLabel.setText(path)

        # Now let's see if this image is in sync
        self.querySyncStatus()

    def dbSync(self):
        # It is neccessary to have the syncer run on the main UI thread
        # hence callback argument is None
        metaSaveDict = dict()
        result = self.preparePathsForDisplay(
            self.syncManager.syncFromDB(callback=None, metaDict=metaSaveDict), onFinish=self.setSyncTime
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
        return self.__jobRunner.run(self.__processAssociatedDataFiles, None, None, pathList, **kwargs)

    def __processAssociatedDataFiles(self, pathList, **kwargs):
        outMap = dict()
        for path in pathList:
            key = utils.getLocalName(path) or path
            outMap[key] = GPSCoord.getInfoDict(path)
            memResource = self.__resourcePool.get(key, {})
            outMap[key]['uri'] = memResource.get('uri', '')
            outMap[key]['path'] = memResource.get('path', '')
            outMap[key]['author'] = utils.getDefaultUserName()

        # Time to swap out the fields and replace
        for k in outMap:
            self.syncManager.editLocalImage(k, outMap[k])

        return outMap

    def getInfoFileNameFromImagePath(self, fPath):
        if not fPath:
            return -1

        splitPath = os.path.split(fPath)

        parentDir, axiom = os.path.split(fPath)

        seqIDExtSplit = axiom.split('.')

        if not seqIDExtSplit:
            print('Erraneous format, expecting pathId and extension eg from 12.jpg')
            return -1

        seqID, ext = seqIDExtSplit
        if ext != 'jpg':
            print("Could not find an info file associated with the image" + fPath)
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
