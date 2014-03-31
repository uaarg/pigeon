#!/usr/bin/python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import sys
import time
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QImage, QCursor, QPixmap, QIcon

import Tag # Local module
import utils # Local module
import DbLiason # Local module

class Marker(QtWidgets.QPushButton):
  def __init__(
      self, parent=None, x=0, y=0, width=10,height=20, mComments=None,
      markerPath='mapMarker.png', tree=None,onDeleteCallback=None, author=None
  ):
    super(Marker, self).__init__(parent)
    __slots__ = ('x', 'y', 'width', 'height', 'iconPath',)
    self.x = x
    self.y = y
    self.tag = None
    self.info = None
    self.tree = tree
    self._width = width
    self.author = author
    self._height = height
    self.imageMap = dict()
    self.iconPath = markerPath
    self.entryData = None
    self.styleSheet = 'opacity:0.9'
    self.memComments = mComments # Memoized comments
    self.onDeleteCallback = onDeleteCallback

    self.initUI()

  def initUI(self):
    self.setGeometry(self.x, self.y, self._width, self._height)
    self.initIcon()

    self.currentFilePath = __file__
    self.__lastLocation = None
    self.registerWithTree()
    self.setMouseTracking(True) # To allow for hovering detection

  def registerWithTree(self):
    if self.tree is not None:
        self.tree[(self.x, self.y)] = self
        print('Tree after self-registration', self.tree)

  def initIcon(self):
    imagePixMap = QPixmap(self.iconPath)
    icon = QIcon(imagePixMap)
    self.setIconSize(QtCore.QSize(self.width(), self.height()))
    self.setIcon(icon);
    self.setStyleSheet(self.styleSheet)

  def addTaggedInfo(self, tagIn):
    self.info, self.entryData = tagIn
    if self.tag:
        self.tag.hide() # del self.tag
        print('hiding tag', self.tag)

  def serialize(self):
    return self.__dict__

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
        author = utils.getDefaultUserName() if not self.author else self.author,
        filePath = self.currentFilePath,
        captureTime=time.time(), x=tagX, y=tagY
      ),

      entryList = [
        utils.DynaItem(dict(
            title='Location', isMultiLine=False,
            entryLocation=(1, 1,), labelLocation=(1, 0,),
            entryText='%s, %s'%(tagX, tagY)
          )
        ),
        utils.DynaItem(dict(
            title='Comments', isMultiLine=True, entryLocation=(2, 1, 5, 1),
            labelLocation=(2, 0,), entryText=self.memComments
          )
        )
      ]
   )

  def mousePressEvent(self, event):
    if event.button() == QtCore.QEvent.MouseButtonDblClick:
      # Weird mix here, needs more debugging on a computer
      # with a mouse since I don't use one
      # Request for a deletion
      if isinstance(self.tree, dict):
        print('Popped marker', self.tree.pop((self.x, self.y),'Not found'))
      if self.onDeleteCallback: 
        print(self.onDeleteCallback(self.x, self.y))

      self.close()
  
    else:
      # Thanks be to Stack Overflow
      buttonNumber = event.button()
      self.__pressPos, self.__movePos = None, None
      if buttonNumber == QtCore.Qt.LeftButton:
        self.__movePos = event.globalPos()
        self.__pressPos = event.globalPos()

        print('\033[43mActivating', self.tag, '\033[00m', self.info, self.entryData)
        if not self.tag:
            if self.info:
                self.tag = Tag.tagFromSource(self.info)
            else:
                self.createTag(event)
        else:
          print('Trying to activateWindow')
          self.tag.show()
          self.tag.activateWindow()

  def show(self):
    print('\033[47mShow invoked\033[00m')
    super().show()

  def hide(self):
    print('\033[46mHide invoked\033[00m')
    super().hide()
   
  def __lt__(self, other):
    return  type(self) is type(other)\
        and (self.x < other.x) and (self.y < other.y)

  def __gt__(self, other):
    return  type(self) is type(other)\
        and (self.x > other.x) and (self.y > other.y)

  def __eq__(self, other):
    return type(self) is type(other)\
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
