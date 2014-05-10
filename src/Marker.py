#!/usr/bin/python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import sys
import time
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QImage, QCursor, QPixmap, QIcon

import Tag # Local module
import utils # Local module
import DbLiason # Local module
import GPSCoord # Local GPS calculation module

class Marker(QtWidgets.QPushButton):
    def __init__(
        self, parent=None, x=0, y=0, lat=0, lon=0, width=30,height=58, mComments=None,
        iconPath='icons/iconmonstr-syncdMarker.png', tree=None,onDeleteCallback=None, author=None
    ):
        super(Marker, self).__init__(parent)
        __slots__ = ('x', 'y', 'width', 'height', 'iconPath',)
        self.x = x
        self.y = y
        self.lat = lat
        self.lon = lon
        self.tag = None
        self.info = None
        self.tree = tree
        self.author = author
        self._width = width
        self._height = height
        self.imageMap = dict()
        self.iconPath = iconPath
        self.entryData = None
        self.memComments = mComments # Memoized comments
        self.onDeleteCallback = onDeleteCallback

        self.__pixmapCache = dict() # Keep private to avoid resource leaks

        self.initUI()

    def initExpandDimensions(self):
        self.origW = self.width()
        self.origH = self.height()
        self.expandedW = self.origW * 1.2
        self.expandedH = self.origH * 1.2

    def toggleUnsaved(self):
        self.initIcon('icons/iconmonstr-unsyncdMarker.png')

    def refreshAndToggleSave(self, attrDict):
        self.memComments = attrDict.get('comments', None)
        self.author = attrDict.get('author', None)
        self.toggleSaved()

    def toggleSaved(self):
        self.initIcon('icons/iconmonstr-syncdMarker.png')
        self.initIcon(self.iconPath)

    def __resetToNormalIcon(self):
        self.setGeometry(self.x, self.y, self.origW, self.origH)

    def initUI(self):
        self.setGeometry(self.x, self.y, self._width, self._height)
        self.initIcon(self.iconPath)

        self.registerWithTree()
        self.setMouseTracking(True) # To allow for hovering detection
        self.setStyleSheet(
            "width:10%;height:0;padding-bottom:10%;border-radius:70%;opacity:80;"
        )
        self.initExpandDimensions()

    def registerWithTree(self):
        if self.tree is not None:
            self.tree[(self.x, self.y)] = self
            # print('Tree after self-registration', self.tree)

    def memoizeIcon(self, path):
        memPixMap, memIcon = self.__pixmapCache.get(path, (None, None,))
        NEEDS_MEMOIZE = False
        if memPixMap is None:
            NEEDS_MEMOIZE = True
            memPixMap = QPixmap(path)

        if memIcon is None:
            NEEDS_MEMOIZE = True
            memIcon = QIcon(memPixMap)

        if NEEDS_MEMOIZE:
            self.__pixmapCache[path] = (memPixMap, memIcon,)

        return memIcon

    def initIcon(self, iconPath):
        memIcon = self.memoizeIcon(iconPath)
        self.setIcon(memIcon);
        self.setIconSize(QtCore.QSize(self.width() * 0.7, self.height() * 0.7))

    def addTaggedInfo(self, tagIn):
        self.entryData = tagIn
        if self.tag:
            self.tag.hide()
            # print('hiding tag', self.tag)

    def serialize(self):
        return self.__dict__

    def induceSave(self):
        if self.tag:
            self.tag.submit()
            if self.entryData:
                self.author=self.entryData.get('Author', None)
                self.memComments=self.entryData.get('Comments', None)

        return self.getReprForDBSave()

    def createTag(self, event):
        lPos = self.pos()
        gPos = self.mapToGlobal(lPos)
        tagX = gPos.x()
        tagY = gPos.y()

        self.tag = Tag.Tag(
            parent=None, title = '@%s'%(time.ctime()),
            location = utils.DynaItem(dict(x=lPos.x(), y=lPos.y())),
            size = utils.DynaItem(dict(x=300, y=240)),
            onSubmit = self.addTaggedInfo,
            metaData = dict(
                captureTime=time.time(), x=tagX, y=tagY,
                author = utils.getDefaultUserName() if not self.author else self.author
            ),

            entryList = [
                utils.DynaItem(
                    dict(
                        labelLocation=(1, 0,), entryText='%s, %s'%(tagX, tagY),
                        title='Pixel Coords', isMultiLine=False,entryLocation=(1, 1,), isEditable=False
                    )
                ),
                utils.DynaItem(
                    dict(
                        labelLocation=(2, 0,), entryText='%s, %s'%(self.lat, self.lon),
                        title='GPS Location', isMultiLine=False,entryLocation=(2, 1,), isEditable=False
                    )
                ),
                utils.DynaItem(
                    dict(
                        labelLocation=(3, 0), entryText=self.author, title='Author', isMultiLine=False,
                        entryLocation=(3, 1,), isEditable=False
                    )
                ),
                utils.DynaItem(
                    dict(
                        labelLocation=(4, 0,), entryText=self.memComments, isEditable=True,
                        title='Comments', isMultiLine=True, entryLocation=(4, 1, 6, 1)
                    )
                )
            ]
        )
        self.toggleUnsaved()

    def erase(self, x, y, needsFlush=True):
        if isinstance(self.tree, dict):
            # print('Popped marker', self.tree.pop((x, y),'Not found'))

            if self.onDeleteCallback and needsFlush: 
                print(self.onDeleteCallback(x, y))

        self.close()

    def close(self, **kwargs):
        if hasattr(self.tag, 'close'):
            self.tag.close()

        # print(self, 'closing')
        super().close()

    def enterEvent(self, event):
        # Make the marker pop out
        self.setGeometry(self.x, self.y, self.expandedW, self.expandedH)


    def leaveEvent(self, event):
        # Revert to the original dimensions
        self.__resetToNormalIcon()


    def mousePressEvent(self, event):
        if event.button() == QtCore.QEvent.MouseButtonDblClick:
            # Weird mix here, needs more debugging on a computer
            # with a mouse since I don't use one
            # Request for a deletion
            self.erase(self.x, self.y)
    
        else:
            # Thanks be to Stack Overflow
            buttonNumber = event.button()
            self.__pressPos, self.__movePos = None, None
            if buttonNumber == QtCore.Qt.LeftButton:
                self.__movePos = event.globalPos()
                self.__pressPos = event.globalPos()

                # print('\033[43mActivating', self.tag, '\033[00m', self.info, self.entryData)
                if not self.tag:
                    if self.info:
                        self.tag = Tag.tagFromSource(self.info)
                    else:
                        self.createTag(event)
                else:
                    print('Trying to activateWindow')
                    self.tag.show()
                    self.tag.activateWindow()

    def getReprForDBSave(self):
        return dict(
            lat=self.lat, lon=self.lon, author=self.author,
            comments=self.memComments, x=self.x, y=self.y
        )

    def show(self):
        # print('\033[47mShow invoked\033[00m')
        super().show()

    def hide(self):
        # print('\033[46mHide invoked\033[00m')
        super().hide()
     
    def __lt__(self, other):
        return    isinstance(other, Marker)\
                and (self.x < other.x) and (self.y < other.y)

    def __gt__(self, other):
        return    isinstance(other, Marker)\
                and (self.x > other.x) and (self.y > other.y)

    def __eq__(self, other):
        return    isinstance(other, Marker)\
            and (self.x == other.x) and (self.y == other.y)

def main():
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = QtWidgets.QMainWindow()
    for i in range(6):
        mark = Marker(parent=mainWindow, x=i*15, y=i*10)
        mark.show()

    mainWindow.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
