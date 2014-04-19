#!/usr/bin/env python3

# Author: Emmanuel Odeke <odeke@ualberta.ca>

import sys
from PyQt5 import QtWidgets, QtGui

class IconItem(QtWidgets.QLabel):
    __pixmapMemoizer = dict()
    def __init__(self, parent, iconPath=None, x=10, y=10, w=150, h=150):
        super(IconItem, self).__init__(parent)

        self.changePixMap(iconPath)
        self.setGeometry(x, y, w, h)
        self.__deriveStaticDimensions()

        self.setMouseTracking(True)

    def __deriveStaticDimensions(self):
        "Maintain static dimensions in case item gets resized"
        self._x = self.x()
        self._y = self.y()
        self.w = self.width()
        self.h = self.height()

    def initWH(self):
        self.w = self.width()
        self.h = self.height()

    def getPixMap(self):
        return self.__pixMap

    def createPixMap(self, path):
        "Creates a pixmap and memoizes it since regeneration\
        of data that potentially needs no modification is expensive"
        memPix = self.__pixmapMemoizer.get(path, None)
        if not isinstance(memPix, QtGui.QPixmap):
            print('\033[47mMemoizing', path, ' pixMap\033[00m')
            self.__pixmapMemoizer[path] = QtGui.QPixmap(path)
            memPix = self.__pixmapMemoizer[path]

        return memPix

    def changePixMap(self, imagePath):
        self.__iconPath = imagePath
        self.__pixMap = self.createPixMap(self.__iconPath) 
        self.setPixmap(self.__pixMap)

    def setLeavePixMap(self, leavePixPath):
        self.__leavePixPath = leavePixPath
        self.__leavePixMap = self.createPixMap(self.__leavePixPath)

    def enterEvent(self, event):
        print('Entering', self.__iconPath)
        self.setGeometry(self.x(), self.y(), self.w * 2, self.h * 2)

    def leaveEvent(self, event):
        print('Leaving now', self.__iconPath)
        self.setGeometry(self.x(), self.y(), self.w, self.h)

def main():
    argc = len(sys.argv)
    app = QtWidgets.QApplication(sys.argv)
    mainWin = QtWidgets.QMainWindow()
    print(argc, sys.argv)
    path = sys.argv[1] if argc > 1 else None
    iItem = IconItem(mainWin, iconPath=path)

    iItem.show()
    mainWin.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
