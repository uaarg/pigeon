#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import sys
import collections
from PyQt5 import Qt, QtGui, QtWidgets, QtCore

try:
    from IconItem import IconItem # Local module
except Exception as e:
    from .IconItem import IconItem

class IconStrip(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super(IconStrip, self).__init__(parent)

        self.setAcceptDrops(True)
        self.xL = 0

        self.__itemDict = dict()
        self.__pixMapCache = dict()

    def addIconItem(self, path, onClick):
        if self.__itemDict.get(path, None) is None:
            return self.__addIconItem(path, onClick)

    def __addIconItem(self, path, onClick):
        print('path', path, onClick)
        iItem = IconItem(self, iconPath=path, pix=self.addPixMap(path), onClick=onClick)
        self.__itemDict[path] = iItem
        iItem.setGeometry(
            iItem.x() + (self.xL * iItem.width()),
            iItem.y(), iItem.width(), iItem.height()
        )
        iItem.show()

        self.xL += 1

    def addPixMap(self, path):
        memPixMap = self.getPixMap(path, None)
        if memPixMap is None:
            memPixMap = QtGui.QPixmap(path)
            self.__pixMapCache[path] = memPixMap

        return memPixMap

    def popPixMap(self, path, altValue=None):
        popd = self.__pixMapCache.pop(path, altValue)
        if popd is not altValue:
            popd.close()

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
