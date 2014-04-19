#!/usr/bin/env python3

import sys
import collections
from PyQt5 import Qt, QtGui, QtWidgets, QtCore

try:
    from IconItem import IconItem # Local module
except Exception as e:
    from .IconItem import IconItem

class IconStrip(QtWidgets.QFrame):
    def __init__(self, parent=None):
        self.__itemDict = collections.OrderedDict()
        super(IconStrip, self).__init__(parent)
        self.setAcceptDrops(True)
        self.xL = 0

    def addIconItem(self, path, pixIn=None):
        if self.__itemDict.get(path, None) is None:
            iItem = IconItem(self, iconPath=path, pix=pixIn)
            self.__itemDict[path] = iItem
            iItem.setGeometry(
                iItem.x() + (self.xL * iItem.width()),
                iItem.y(), iItem.width(), iItem.height()
            )
            self.xL += 1
            print('self.xL', self.xL, iItem.show())

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
