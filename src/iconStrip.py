#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import re
import sys
import collections
from PyQt5 import Qt, QtGui, QtWidgets, QtCore

class IconStrip(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super(IconStrip, self).__init__(parent)

        self.__itemDict = dict()
        self.__pixMapCache = dict()
        self.setIconSize(QtCore.QSize(self.width(), self.width()))
        self.setFlow(QtWidgets.QListWidget.LeftToRight)

        self.setAcceptDrops(True)

    def rawKeys(self):
        return self.__itemDict.keys()

    def itemDictManifest(self):
        return list(self.rawKeys())

    def isMemoized(self, path):
        return path in self.__itemDict

    def setOnItemClick(self, clickHandler):
        self.__onClick = clickHandler

    def addIconItem(self, path, onClick=None):
        pixMap = self.addPixMap(path)
        if pixMap:
            icon = QtGui.QIcon(pixMap)
            item = QtWidgets.QListWidgetItem('', self)
            item.setIcon(icon)
            item.setStatusTip(path)

            self.__itemDict[path] = item 
            return self.currentRow() or 1

    def editStatusTipByKey(self, path, newStatusTip):
        memItem = self.__itemDict.get(path, None)
        if hasattr(memItem, 'setStatusTip') and hasattr(memItem.setStatusTip, '__call__'):
            memItem.setStatusTip(newStatusTip)

    def mousePressEvent(self, event):
        curItem = self.currentItem()
        if curItem:
            curIndex = self.currentIndex()
            self.__onClick(curItem.statusTip())

    def addPixMap(self, path):
        memPixMap = self.getPixMap(path, None)
        if memPixMap is None:
            memPixMap = QtGui.QPixmap(path)
            self.__pixMapCache[path] = memPixMap

        return memPixMap

    def showItem(self, path):
        retrValue = self.__itemDict.get(path, None)
        print('\033[45mShowing', path, retrValue, '\033[00m')
        if retrValue is not None:
            self.scrollToItem(retrValue)

    def popIconItem(self, path, altValue=None):
        popd = self.__itemDict.pop(path, altValue)
        if popd is not altValue:
            self.takeItem(self.row(popd))

        newlySelectedPath = None
        curItem = self.currentItem()
        if hasattr(curItem, 'statusTip'):
            newlySelectedPath = curItem.statusTip() 

        elif self.__itemDict:
            it = iter(self.__itemDict)
            for p in it:
                if p:
                    newlySelectedPath = p
                    break
            

        return newlySelectedPath

    def close(self):
        for iconItem in self.__itemDict.values():
            if hasattr(iconItem, 'close'):
                iconItem.close()

        del self.__pixMapCache
        del self.__itemDict

        print('\033[35m', self, 'closing\033[00m')
        super().close()

    def getPixMap(self, key, altValue=None):
        return self.__pixMapCache.get(key, altValue)

def main():
    argc = len(sys.argv)
    app = QtWidgets.QApplication(sys.argv)
    mainWin = QtWidgets.QMainWindow()
    print(argc, sys.argv)
    iStrip = IconStrip(mainWin)
    iStrip.setGeometry(20, 10, 800, 800)
    for i in range(1, argc):
        iStrip.addIconItem(sys.argv[i])

    mainWin.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
