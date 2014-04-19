#!/usr/bin/env python3

import sys
import collections
from PyQt5 import Qt, QtGui, QtWidgets, QtCore

try:
    from .IconItem import IconItem
except Exception as e:
    from IconItem import IconItem

class IconStrip(QtWidgets.QFrame):
    def __init__(self, parent=None):
        self.__itemDict = collections.OrderedDict()
        super(IconStrip, self).__init__(parent)
        self.setAcceptDrops(True)
        self.xL = 0
        self.widgetFrame = QtWidgets.QFrame(self)

    def addIconItem(self, path):
        iItem = IconItem(self, iconPath=path)
        self.__itemDict[path] = iItem
        iItem.setGeometry((self.xL * iItem.width()), iItem.y(), iItem.width(), iItem.height())
        print('\033[91madding path', path, '\033[00m')
        self.xL += 1

    def getPixMap(self, key):
        retrIconItem = self.__itemDict.get(key, None)
        if isinstance(retrIconItem, IconItem):
            return retrIconItem.getPixMap()

def main():
    argc = len(sys.argv)
    app = QtWidgets.QApplication(sys.argv)
    mainWin = QtWidgets.QMainWindow()
    print(argc, sys.argv)
    iStrip = IconStrip(mainWin)
    iStrip.setGeometry(20, 10, 800, 800)
    for i in range(1, argc):
        iStrip.addIconItem(sys.argv[i])

    iStrip.show()
    mainWin.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
