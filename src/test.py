#!/usr/bin/env python3
import sys
from PyQt5 import QtWidgets, QtGui, uic

import gcs

class Temple(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Temple, self).__init__(parent)
        self.ui_window = gcs.Ui_MainWindow()
        self.ui_window.setupUi(self)

        # Set up actions
        self.initActions()

        # Set up menus
        self.initMenus()

        self.initFileDialog()

    def initFileDialog(self):
        self.fileDialog = QtWidgets.QFileDialog()
        self.fileDialog.setFileMode(3) # Multiple files can be selected
        self.fileDialog.filesSelected.connect(self.__normalizeFileAdding)

    def __normalizeFileAdding(self, paths):
        print(self.ui.fullSizeImageView)
        print(paths)

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
        print('showNext')

    def showPrev(self):
        print('showPrev')

    def handleItemPop(self):
        print('handleItemPop')

    def saveCoords(self):
        print('saveCoords')

    def dbSync(self):
        print('dbSync')

    def cleanUpAndExit(self):
        self.close()

    def findImages(self):
        if isinstance(self.fileDialog, QtWidgets.QFileDialog):
            self.fileDialog.show()
        else:
            qBox = QMessageBox(parent=self)
            qBox.setText('FileDialog was not initialized')
            qBox.show()


class MyWidget(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MyWidget, self).__init__(parent)
        self.ui = uic.loadUi('gcs.ui', self)
        ui_window = gcs.Ui_MainWindow()
        ui_window.setupUi(self)

        # Set up actions
        self.initActions()

        # Set up menus
        self.initMenus()

        self.initFileDialog()

    def initFileDialog(self):
        self.fileDialog = QtWidgets.QFileDialog()
        self.fileDialog.setFileMode(3) # Multiple files can be selected
        self.fileDialog.filesSelected.connect(self.__normalizeFileAdding)

    def __normalizeFileAdding(self, paths):
        print(self.ui.fullSizeImageView)
        print(paths)

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
        print('showNext')

    def showPrev(self):
        print('showPrev')

    def handleItemPop(self):
        print('handleItemPop')

    def saveCoords(self):
        print('saveCoords')

    def dbSync(self):
        print('dbSync')

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

    mItem = Temple()
    mItem.show()
    q = QtGui.QPixmap('slsl')
    help(q)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
