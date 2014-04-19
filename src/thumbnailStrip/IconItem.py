#!/usr/bin/env python3

# Author: Emmanuel Odeke <odeke@ualberta.ca>

import sys
from PyQt5 import QtWidgets, QtGui

class IconItem(QtWidgets.QLabel):
    __pixmapMemoizer = dict()
    def __init__(self, parent, iconPath=None, pix=None, x=10, y=10, w=50, h=50, onClick=None):
        super(IconItem, self).__init__(parent)

        self.__onClick = onClick
        self.setGeometry(x, y, w, h)
        self.__deriveStaticDimensions()
        self.initPixMapInfo(iconPath, pix)

        self.setMouseTracking(True)

    def initPixMapInfo(self, path, pix):
        self.__pixMap = pix
        self.__iconPath = path
        self.setPixmap(self.__pixMap)

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

    def enterEvent(self, event):
        # print('Entering', self.__iconPath)
        self.setGeometry(self.x(), self.y(), self.w * 2, self.h * 2)

    def leaveEvent(self, event):
        # print('Leaving now', self.__iconPath)
        self.setGeometry(self.x(), self.y(), self.w, self.h)

    def mousePressEvent(self, event):
        if self.__onClick is not None:
            self.__onClick(self.__iconPath)

    def close(self):
        print('\033[96m', self, 'closing\033[00m')
        super().close()

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
