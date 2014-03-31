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
      self, parent=None, x=0, y=0, width=10,height=20,
      markerPath='mapMarker.png', tree=None,onDeleteCallback=None
  ):
    super(Marker, self).__init__(parent)
    __slots__ = ('x', 'y', 'width', 'height', 'iconPath',)
    self.x = x
    self.y = y
    self.tag = None
    self.info = None
    self.tree = tree
    self._width = width
    self._height = height
    self.imageMap = dict()
    self.iconPath = markerPath
    self.entryData = None
    self.styleSheet = 'opacity:0.9'
    self.onDeleteCallback = onDeleteCallback

    self.initUI()

  def initUI(self):
    self.setGeometry(self.x, self.y, self._width, self._height)
    self.initIcon()

    self.currentFilePath = __file__
    self.__lastLocation = None
    self.setMouseTracking(True) # To allow for hovering detection

    if self.tree is not None:
        self.tree[(self.x, self.y)] = self
        # print('added in', self.tree)

  def initIcon(self):
    imagePixMap = QPixmap(self.iconPath)
    icon = QIcon(imagePixMap)
    self.setIconSize(QtCore.QSize(self.width(), self.height()))
    self.setIcon(icon);
    self.setStyleSheet(self.styleSheet)

  def addTaggedInfo(self, tagIn):
    self.info, self.entryData = tagIn
    print('entryData', self.entryData)
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
      location = Tag.DynaItem(dict(x=lPos.x(), y=lPos.y())),
      size = Tag.DynaItem(dict(x=300, y=240)),
      onSubmit = self.addTaggedInfo,
      metaData = dict(
        author = utils.getDefaultUserName(),
        filePath = self.currentFilePath,
        captureTime=time.time(), x=tagX, y=tagY
      ),

      entryList = [
        Tag.DynaItem(dict(
            title='Location', isMultiLine=False,
            entryLocation=(1, 1,), labelLocation=(1, 0,),
            entryText='%s, %s'%(tagX, tagY)
          )
        ),
        Tag.DynaItem(dict(
            title='Comments', isMultiLine=True, entryLocation=(2, 1, 5, 1),
            labelLocation=(2, 0,), entryText=None
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
        print(self.onDeleteCallback(self.mapToGlobal(self.pos())))

      self.close()
      del self
  
    else:
      # Thanks be to Stack Overflow
      buttonNumber = event.button()
      self.__pressPos, self.__movePos = None, None
      if buttonNumber == QtCore.Qt.LeftButton: # Left Click here 
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
   
  def __lt__(self, other):
    return  type(self) is type(other)\
        and (self.x < other.x) and (self.y < other.y)

  def __gt__(self, other):
    return  type(self) is type(other)\
        and (self.x > other.x) and (self.y > other.y)

  def __eq__(self, other):
    return type(self) is type(other)\
      and (self.x == other.x) and (self.y == other.y)
 
  '''
  # Uncomment to allow for moving of markers -- Still buggy
  def mouseMoveEvent(self, event):
    # Thanks to Stack Overflow
    if event.button() == QtCore.Qt.LeftButton:
        curPos = self.mapToGlobal(self.pos())
        globalPos = event.globalPos()
        diff = globalPos - self.__movePos
        newPos = self.mapFromGlobal(curPos + diff)
        self.__movePos = globalPos
        print('mouseMove')
  def mouseReleaseEvent(self, event):
    # Thanks to Stack Overflow
    if self.__pressPos is not None:
        moved = event.globalPos() - self.__pressPos
        if moved.manhattanLength() < 2:
          event.ignore()
        else:
          self.move(moved)

  def enterEvent(self, event):
    self.__lastLocation = event.pos()

  def leaveEvent(self, event):
    print('leaveEvent',event.type())
'''

def main():
  app = QtWidgets.QApplication(sys.argv)
  mainWindow = QtWidgets.QMainWindow()
  for i in range(4):
    mark = Marker(parent=mainWindow, x=i*15, y=i*10)
    mark.show()
  mainWindow.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
