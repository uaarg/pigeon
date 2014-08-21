#!/usr/bin/env python3
# Author: Cindy Xiao <dixin@ualberta.ca>, Emmanuel Odeke <odeke@ualberta.ca>

import os
import re
import sys
import shutil
import random
from PyQt5 import QtCore, QtWidgets, QtGui, QtMultimedia

import gcs # Generated module by running: pyuic5 gcs.ui > gcs.py

import Tag # Local module
import utils # Local module
import Marker # Local module
import simplekml # module used for writing to Google Earth KML files
import kmlUtil # Local module
import GPSCoord # Local module
import DbLiason # Local module
import iconStrip # Local module
import constants # Local module
import ImageDisplayer # Local module
import DirWatchManager # Local module

import mpUtils.JobRunner # Local module

from resty import restDriver

REPORTS_DIR = './reports'
ATTR_VALUE_REGEX_COMPILE = re.compile('([^\s]+)\s*=\s*([^\s]+)\s*', re.UNICODE)

defaultImageFormDict = dict(
    time=0, utm_north=0, speed=0, image_width=1294.0, image_height=964.0, course=0,
    phi=0.0, psi=0, theta=0, alt=0, author=utils.getDefaultUserName(), utm_east=0.0,
    viewangle_horiz=21.733333, viewangle_vert=16.833333, pixel_per_meter=0, ppm_difference=0
)

isCallable = lambda obj: hasattr(obj, '__call__')
localizeToProcessedPath = lambda basename: os.sep.join(('.', 'data', 'processed', basename,))

class GroundStation(QtWidgets.QMainWindow):
    __jobRunner     = mpUtils.JobRunner.JobRunner()
    def __init__(self, ip, port, parent=None, eavsDroppingMode=False):
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
        self.initRestHandler(ip, port)

        self.initUI()
        self.initSaveSound()
        self.initLCDDisplays()
        self.initTimers()

        # Now load all content from the DB
        self.fullDBSync()

    def initRestHandler(self, ip, port):
        self.__cloudConnector = restDriver.RestDriver(ip, port)

        assert(self.__cloudConnector.registerLiason('Image', '/gcs/imageHandler'))
        assert(self.__cloudConnector.registerLiason('Marker', '/gcs/markerHandler'))

    def initTimers(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.showCurrentTime)

        self.syncTimer = QtCore.QTimer(self)
        func = self.querySyncStatus
        timeout = 5000
        if self.inEavsDroppingMode:
            func = self.fullDBSync
            timeout = 8000

        self.syncTimer.timeout.connect(func)
        self.syncTimer.start(timeout)

        self.timer.start(1000)

    def initLCDDisplays(self):
        self.__nowLCD = self.ui_window.nowLCDNumber
        self.__nowLCD.setDigitCount(8)

        self.__lastSyncLCD = self.ui_window.lastSyncLCDNumber
        self.__lastSyncLCD.setDigitCount(8)

        self.showCurrentTime()

    def fullDBSync(self, popUnSavedChanges=True):
        print('FullDBSync')
        if popUnSavedChanges:
            keyManifest = list(self.__resourcePool.keys())
            for p in keyManifest:
                syncStatus, dbImageCount = self.findSyncStatus(p)
                if syncStatus != constants.IS_IN_SYNC:
                    self.handleItemPop(p, isGlobalPop=False, callback=print)

        self.dbSync()

        self.__normalizeFileAdding(self.__resourcePool.keys())

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
            localImageCount = len(self.iconStrip.rawKeys())
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
        queryDict = dict(format='short', uri=path, select='lastEditTime')

        parsedResponse = self.__cloudConnector.getImages(format='short', uri=path, select='lastEditTime')

        data = None
        status_code = 400
        countOnCloud = -1

        if hasattr(parsedResponse, 'get'):
            status_code = parsedResponse.get('status_code', 400)
            result = parsedResponse['value']
            data = result.get('data', None)
            meta = result.get('meta', None)
            if hasattr(meta, 'keys'): 
                countOnCloud = meta.get('collectionCount', -1)

        if status_code != 200:
            return constants.NO_CONNECTION, countOnCloud

        elif data:
            memAttrMap = self.getImageAttrsByKey(path)

            memId = int(memAttrMap.get('id', -1))
            memlastEditTime = float(memAttrMap.get('lastEditTime', -1))

            itemInfo = data[0]
            idOnCloud = int(itemInfo.get('id', -1))
            imageOnCloudlastEditTime = float(itemInfo['lastEditTime'])

            if idOnCloud < 1:
                print('\033[48mThis data is not present on cloud, path:', path, '\033[00m')
                return constants.IS_FIRST_TIME_SAVE, countOnCloud

            elif imageOnCloudlastEditTime > memlastEditTime:
                print('\033[47mDetected a need for saving here since')
                print('your last memoized local editTime was', memlastEditTime)
                print('Most recent db editTime is\033[00m', imageOnCloudlastEditTime)
                return constants.IS_OUT_OF_SYNC, countOnCloud
            else:
                print('\033[42mAll good! No need for an extra save for',\
                     path, '\033[00m'
                )
                return constants.IS_IN_SYNC, countOnCloud
        else:
            print("\033[41mNo data back from querying about lastEditTime\033[00m")
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
            onDeleteMarkerFromDB=self.deleteMarkerFromDB, onMarkerMove=self.onMarkerMove
        )
        self.ui_window.fullSizeImageScrollArea.setWidget(self.ImageDisplayer)

        self.imgAttrFrame = self.ui_window.imageAttributesFrame

    def onMarkerMove(self, oldPos, newPos, mHash):
        self.__jobRunner.run(self.__onMarkerMove, None, print, oldPos, newPos, mHash)

    def __onMarkerMove(self, *args):
        oldPos, newPos, mHash = args[0]
        # ownMap = self.__keyToMarker.get(self.ui_window.pathDisplayLabel.text(), {})
        # print('oldPos', oldPos, 'newPos', newPos, mHash, ownMap)
        # print('picked marker', ownMap.get(mHash, None))

    def createMarker(self, isSaved=False, isHidden=False, **kwargs):
        m = Marker.Marker(onMoveEvent=self.onMarkerMove, **kwargs)
        isSaved and m.toggleSaved()
        isHidden and m.hide()

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

            if not utils.pathExists(path):
                dlPath = self.downloadBlob(path)
                print('dlPath', dlPath)
                if dlPath:
                    path = dlPath

            if not self.iconStrip.isMemoized(path):
                self.iconStrip.addIconItem(path, self.renderImage)

            lastItem = path

        # Display the last added item
        self.renderImage(lastItem)

        if lastItem: # Sound only if there is an item to be displayed
            self.__saveSound.play()
        else:
            self.querySyncStatus()

        isCallable(onFinish) and onFinish()

    def preparePathsForDisplay(self, dynaDictList, onFinish=None):
        return self.__preparePathsForDisplay(dynaDictList or [], onFinish=onFinish)
        
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
        memDict = self.__resourcePool.get(key, None)
        if memDict is None:
            memDict = dict(uri=key, title=key)
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
                utils.DynaItem(
                    title=entry, isMultiLine=False, labelLocation=(index, 0,),
                    isEditable=True, entryLocation=(index, 1,), entryText=str(textExtracted)
                )
            )


        imageTag = Tag.Tag(
            size=utils.DynaItem(x=self.imgAttrFrame.width(), y=self.imgAttrFrame.height()),
            location=utils.DynaItem(x=self.imgAttrFrame.x(), y=self.imgAttrFrame.y()),
            title='Location data for: ' + self.ui_window.pathDisplayLabel.text(),
            onSubmit=self.saveCurrentImageContent,
            entryList=entryList
        )
        imageTag.show()

    def saveCurrentImageContent(self, content):
        print('Saving currentImage content', content)
        curPath = self.ui_window.pathDisplayLabel.text()
        
        currentMap = self.getImageAttrsByKey(curPath)

        if isinstance(content, dict):
            for k, v in content.items():
                currentMap[k] = v

        currentMap.setdefault('uri', curPath)
        currentMap.setdefault('title', curPath)

        # Getting the original ids in
        self.editLocalContent(curPath, content, None)
        return self.syncByPath(curPath)

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

        self.dbSyncAction = QtWidgets.QAction(
            self.getIcon('icons/iconmonstr-save.png'), '&Sync from Cloud', self
        )
        self.dbSyncAction.triggered.connect(self.fullDBSync)
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

    def handleItemPop(self, currentItem=None, callback=print, isGlobalPop=True):
        pathOnDisplay = currentItem or self.ui_window.pathDisplayLabel.text()
        popd = self.__resourcePool.pop(pathOnDisplay, None)
            
        dQuery = self.__cloudConnector.getImages(uri=pathOnDisplay, select='uri,id')

        if isGlobalPop and isinstance(dQuery, dict) and dQuery.get('status_code', 400) == 200:
            data = dQuery['value'].get('data', None)
            if data:
                for dDict in data:
                    # TODO: Decide if you want to delete the file from the cloud as well
                    # print('\033[46m%s\033[00m'%(self.__cloudConnector.deleteFile(uri=pathOnDisplay)))
                    print(self.__cloudConnector.deleteMarkers(associatedImage_id=dDict.get('id', -1)))
                    print(self.__cloudConnector.deleteImages(id=dDict.get('id', -1)))

                    self.handleItemPop(dDict.get('uri', ''))

        mpopd = self.__keyToMarker.pop(pathOnDisplay, None)
        self.__jobRunner.run(self.closeMarkers, None, callback, mpopd)

        nextPath = self.iconStrip.popIconItem(pathOnDisplay)
        # print('iconStripKeys', self.iconStrip.rawKeys())
        return self.renderImage(nextPath)

    def closeMarkers(self, *args, **kwargs):
        markerMap = args[0]
        if isinstance(markerMap, dict):
            markerList = list(markerMap.values())
            for marker in markerList:
                if hasattr(marker, 'close') and isCallable(marker.close):
                    marker.close()
            
    def deleteMarkerFromDB(self, markerHash, srcPath=None):
        # Contract is that by the time this method gets invoked, it is
        # originating from the current path on display
        targetPath = srcPath or self.ui_window.pathDisplayLabel.text()

        markerSect = self.__keyToMarker.get(targetPath)
        if markerSect:
            memMarker = markerSect.get(markerHash, None)
        
            x, y = memMarker.x, memMarker.y
            if memMarker and hasattr(memMarker, 'close') and isCallable(memMarker):
                memMarker.close()

            queryDict = self.getImageAttrsByKey(targetPath)
            return self.__cloudConnector.deleteMarkers( 
                associatedImage_id=queryDict.get('id', -1), x=x, y=y
            )

    def syncByPath(self, path):
        elemData = self.getImageAttrsByKey(path)
        isDirty = lambda k: k == 'marker_set' or k == 'id'
        elemAttrDict = dict((k, v) for k, v in elemData.items() if not isDirty(k))
        pathSelector = elemData.get('uri', '') or elemData.get('title', '')

        basename = os.path.basename(pathSelector)
        localizedDataPath = os.sep.join(('.', 'data', 'processed', basename,))

        dQuery = self.__cloudConnector.getCloudFilesManifest(uri=localizedDataPath)
        print('dQuery', dQuery)

        statusCode = dQuery['status_code']
        if statusCode == 200:
            needsUpload = True
            data = dQuery.get('value', {}).get('data', None)
            if data:
                # Now time for a size inquiry
                if utils.pathExists(pathSelector):
                    statDict = os.stat(pathSelector)
                    randSample = random.sample(data, 1)[0]
                    queriedSize = randSample.get('size', -1)
                    if int(statDict.st_size) == int(queriedSize):
                        # Simple litmus test. In the future will add checksum checks
                        needsUpload = False

            if needsUpload:
                uploadResponse = self.__cloudConnector.uploadBlob(
                    pathSelector, uri=localizedDataPath, author=utils.getDefaultUserName()
                )
                if uploadResponse.status_code == 200:
                    print('\033[92mSuccessfully uploaded: %s\033[00m'%(pathSelector))
                    if not utils.pathExists(localizedDataPath):
                        try:
                            shutil.copy(pathSelector, localizedDataPath)
                        except Exception as e:
                            print('\033[91mException: %s while trying to copy %s to %s'%(
                                pathSelector, localizedDataPath, e
                            ))
                        else:
                            print('\033[47mSuccessfully copied %s to %s\033[00m'%(
                                pathSelector, localizedDataPath
                            ))
                else:
                    print('\033[91mFailed to uploaded: %s\033[00m'%(pathSelector))
                print('responseText', uploadResponse.text)

        
        if localizedDataPath != pathSelector:
            # Swap out this path
            self.__jobRunner.run(
                self.__swapOutResourcePaths, None, None, pathSelector, localizedDataPath
            )

        elemAttrDict['uri'] = localizedDataPath
        existanceQuery = self.__cloudConnector.getImages(uri=localizedDataPath)

        methodName = 'newImage'
        if isinstance(existanceQuery, dict) and existanceQuery.get('status_code', 400) == 200:
            data = existanceQuery.get('value', {}).get('data', None)
            if data:
                for item in data:
                    self.editLocalContent(item.get('uri', ''), item, None)

                sample = random.sample(data, 1)[0]
                elemAttrDict = {'queryParams': {'id':int(sample.get('id', -1))}, 'updatesBody':elemAttrDict}
                methodName = 'updateImages'

        func = getattr(self.__cloudConnector, methodName)

        parsedResponse = func(**elemAttrDict)
        statusCode = parsedResponse.get('status_code', 400)
        if statusCode == 200:
            pathDict = self.getImageAttrsByKey(localizedDataPath)
            if pathDict is None:
                pathDict = dict(uri=localizedDataPath)
         
            idFromDB = -1 
            result = parsedResponse.get('value', {})
            print('Result', result) 
            if result.get('id', None):
                idFromDB = result['id']
            elif parsedResponse.get('data', None):
                idFromDB = result['data'].get('id', -1)

            pathDict['id'] = idFromDB
            self.__resourcePool[localizedDataPath] = pathDict
            
            return localizedDataPath

    def downloadBlob(self, resourceKey, callback=None):
        self.__jobRunner.run(self.__downloadBlob, None, callback, resourceKey)

    def __downloadBlob(self, resourceKey):
        elemAttrDict = self.getImageAttrsByKey(resourceKey)
        print('Downloading by key', resourceKey, elemAttrDict)

        pathSelector = elemAttrDict.get('uri', '') or elemAttrDict.get('title', '')
        basename = os.path.basename(pathSelector) or '%s.jpg'%(resourceKey)

        localizedDataPath = os.sep.join((os.path.abspath('.'), 'data', 'processed', basename,))

        writtenBytes = self.__cloudConnector.downloadBlob(
            basename, altName=localizedDataPath
        )
        if writtenBytes:
            elemAttrDict['uri'] = localizedDataPath
            elemAttrDict['title'] = localizedDataPath

            return localizedDataPath

    def __swapOutResourcePaths(self, *args):
        oldPath, newPath = args
        print('Swapping out', oldPath, newPath)
        popd = self.__resourcePool.pop(oldPath, None)
        if popd is not None:
            popd['uri'] = popd['title'] = newPath
            self.__resourcePool[newPath] = popd
            
        mPop = self.__keyToMarker.pop(oldPath, None)
        if mPop is not None: 
            print('mPop', mPop)
            self.__keyToMarker[newPath] = mPop 

        self.iconStrip.swapOutMapKeys(oldPath, newPath)

    def bulkSaveMarkers(self, associatedKey, markerDictList):
        return self.__jobRunner.run(self.__bulkSaveMarkers, None, print, associatedKey, markerDictList)

    def __bulkSaveMarkers(self, *args):
        associatedKey, markerDictList = args[0]
        memImageAttr = self.getImageAttrsByKey(associatedKey)
        print('memImageAttr', memImageAttr)
        if (isinstance(memImageAttr, dict) and int(memImageAttr.get('id', -1)) >= 1):
            memId = memImageAttr['id']
            prepMemDict = dict(associatedImage_id=memId, select='id')
            savedMarkers = []
            for mDict in markerDictList: 
                saveDictGetter = mDict.get('getter', None) 
                failedSave = True
                funcAttrToInvoke = 'onFailure'

                if isCallable(saveDictGetter):
                    saveDict = saveDictGetter()

                    prepMemDict['longHashNumber'] = saveDict.get('longHashNumber', -1)

                    idQuery = self.__cloudConnector.getMarkers(**prepMemDict)

                    connAttrForSave = self.__cloudConnector.newMarker
                    data = idQuery.get('value', {}).get('data', None)
                    if data:
                        sample = data[0]
                        sampleId = sample.get('id', -1)
                        connAttrForSave = self.__cloudConnector.updateMarkers
                        saveDict = {'queryParams':{'id':sampleId}, 'updatesBody':saveDict}
                    else:
                        saveDict['associatedImage_id'] = memId

                    saveResponse = connAttrForSave(**saveDict)
                    if saveResponse.get('status_code', 400) == 200:
                        funcAttrToInvoke = 'onSuccess'
                        savedMarkers.append(saveResponse.get('data', {}))

                if isCallable(mDict.get(funcAttrToInvoke, None)):
                    mDict[funcAttrToInvoke](saveDict)

            return savedMarkers
    
    def syncCurrentItem(self):
        pathOnDisplay = self.ui_window.pathDisplayLabel.text()
        print('Syncing current item', pathOnDisplay)

        associatedMarkerMap = self.__keyToMarker.get(pathOnDisplay, {})
        localizedPath = self.syncByPath(pathOnDisplay)

        if localizedPath:
            pathOnDisplay = localizedPath

        markerDictList = []
        # print('associatedMMap', associatedMarkerMap)
        for m in associatedMarkerMap.values():
            markerDictList.append({
                'getter':m.induceSave, 'onSuccess':m.refreshAndToggleSave, 'onFailure':m.toggleUnsaved
            })

        # Let's get those markers in
        bulkSaveResults = self.bulkSaveMarkers(pathOnDisplay, markerDictList)

        # Next pull changes
        self.dbSync(uri=pathOnDisplay)

        self.renderImage(pathOnDisplay)

    def setSyncTime(self, *args):
        curTime = QtCore.QTime.currentTime()
        text = curTime.toString('hh:mm:ss')
        self.__lastSyncLCD.display(text)

    def renderImage(self, path):
        if not (path and os.path.exists(path)):
            path = utils._PLACE_HOLDER_PATH

        memPixMap = self.iconStrip.addPixMap(path)
        markerSet = self.__resourcePool.get(path, {}).get('marker_set', [])
        markerMap = self.__keyToMarker.setdefault(path, {})

        if self.ImageDisplayer.renderImage(path, markerSet, markerMap, memPixMap):
            self.ui_window.pathDisplayLabel.setText(path)
            associatedTextFile = utils.getInfoFileNameFromImagePath(path)
            if associatedTextFile != -1:
                self.processAssociatedDataFiles([associatedTextFile])
                geoDataDict = GPSCoord.getInfoDict(associatedTextFile)
                self.ImageDisplayer.extractSetGeoData(geoDataDict)

            for marker in markerMap.values():
                marker.show()

    def dbSync(self, **queryDict):
        print('DBSync in progress')
        queryDict['sort'] = 'lastEditTime'
        imgQuery = self.__cloudConnector.getImages(**queryDict)
        data = imgQuery.get('value', {}).get('data', None)
        if imgQuery.get('status_code', 400) == 200 and data:
            for imgDict in data:
                markerSet = imgDict.get('marker_set', [])
                pathSelector = imgDict.get('uri', '') or imgDict.get('title', '')

                basename = os.path.basename(pathSelector)
                localizedDataPath = os.sep.join(('.', 'data', 'processed', basename,))
                if not utils.pathExists(localizedDataPath):
                    dlPath = self.downloadBlob(pathSelector)
                    if dlPath:
                        print('Downloaded', dlPath)

                memDict = self.__keyToMarker.get(pathSelector, None)
                if hasattr(memDict, 'keys'):
                    cpValues = list(memDict.values())
                    for m in cpValues:
                        m.close()

                for mDict in markerSet:
                    tree = self.__keyToMarker.setdefault(pathSelector, dict())
                    mDict['x'] = int(mDict.get('x', 0))
                    mDict['y'] = int(mDict.get('y', 0))

                    memMarker = tree.get(mDict.get('longHashNumber', None), None)
                    mDict.setdefault('author', utils.getDefaultUserName())

                    if memMarker is None:
                        memMarker = self.createMarker(
                            isSaved=True, isHidden=True, parent=self.ImageDisplayer,
                            tree=self.__keyToMarker.setdefault(pathSelector, {}),
                            onDeleteCallback=self.deleteMarkerFromDB, **mDict
                        )
                    else:
                        memMarker.updateContent(**mDict)
            
                self.__resourcePool[pathSelector] = imgDict

            self.setSyncTime()

        self.querySyncStatus()

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
        
        storedMap = self.__resourcePool.get(srcPath, None)
        if storedMap:
            if not os.path.exists(REPORTS_DIR):
                try:
                    os.mkdir(REPORTS_DIR)
                except Exception as e:
                    print('\033[91m', e, '\033[00m')
                    return

            imageInfoPath = os.path.join(REPORTS_DIR, key + '-image.csv')
            imagesIn = markersIn = False
            exclusiveOfMarkerSetKeys = [k for k in storedMap.keys() if k != 'marker_set']
            with open(imageInfoPath, 'w') as f:
                f.write(','.join(exclusiveOfMarkerSetKeys))
                f.write('\n')
                f.write(','.join(str(storedMap[k]) for k in exclusiveOfMarkerSetKeys))
                f.write('\n')
                
                imagesIn = True
            
            kmlPath = os.path.join(REPORTS_DIR, key + '.kml')
            self.printAllKMLData(kmlPath)

            markerSet = storedMap.get('marker_set', [])
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

    def printAllKMLData(self, kmlPath):
        """
        Saves data for all images in the current marked image set into a Google Earth KML file.
        """
        import simplekml
        imagekml = simplekml.Kml()

        for image in self.__resourcePool.keys():
            try:
                markerSet = self.__resourcePool[image]['marker_set']
                for marker in markerSet:
                    print(marker)
                    marker_lat = float(marker['lat'])
                    marker_lon = float(marker['lon'])
                    marker_id = marker['associatedImage_id'] + "-" + marker['id'] 
                    marker_coords = [(marker_lon, marker_lat)]
                    print(marker_coords)
                    imagekml.newpoint(name=str(marker_id), coords=marker_coords)
            except:
                continue

        kml_data = imagekml.kml()
        with open(kmlPath, 'w') as h:
            h.write(kml_data) and print('\033[95mWrote KML info to', kmlPath)

    def writeImageKMLData(self, imageDataMap, imageSetKMLObject):
        """
        Writes data for the current image and all its contained markers into the KML object for this set of files, or this instance of the station.
        """

        markerSet = imageDataMap.get('marker_set', [])
        exclusiveOfMarkerSetKeys = [k for k in imageDataMap.keys() if k != 'marker_set']
        fmtdTree = dict((k, imageDataMap[k]) for k in exclusiveOfMarkerSetKeys)
        fmtdTree['marker_set'] = [dict(Marker=m) for m in markerSet]
        marker_kml = kmlUtil.placemarkKMLConvert(fmtdTree, imageSetKMLObject)


    def addLocationData(self):
        if isinstance(self.locationDataDialog, QtWidgets.QFileDialog):
            self.locationDataDialog.show()
        else:
            self.msgQBox.setText('LocationData fileDialog was not initialized')
            self.msgQBox.show()

    def processAssociatedDataFiles(self, pathList):
        return self.__jobRunner.run(self.__processAssociatedDataFiles, None, lambda a: a, pathList)

    def __processAssociatedDataFiles(self, pathList, *args, **kwargs):
        pathList = pathList[0]
        outMap = dict()
        for path in pathList:
            key = localizeToProcessedPath('%s.jpg'%(utils.getLocalName(path) or path))
            outMap[key] = GPSCoord.getInfoDict(path)
            outMap[key]['author'] = utils.getDefaultUserName()

        # Time to swap out the fields and replace
        for k, v in outMap.items():
            self.editLocalContent(k, v)

        return outMap

    def editLocalContent(self, key, outMap, callback=None):
        return self.__jobRunner.run(self.__editLocalContent, None, callback, key, outMap)

    def __editLocalContent(self, key, outMap):
        memMap = self.__resourcePool.setdefault(key, dict(uri=key, title=key))
        for k, v in outMap.items():
            memMap[k] = v

        return memMap

def main():
    app = QtWidgets.QApplication(sys.argv)
    args, options = utils.cliParser()

    # Time to get address that the DB can be connected to via
    eavsDroppingMode = args.eavsDroppingMode
    gStation = GroundStation(args.ip.strip('/'), args.port.strip('/'), eavsDroppingMode=eavsDroppingMode)

    gStation.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
