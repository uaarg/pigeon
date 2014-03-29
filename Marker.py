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
  def __init__(self, parent=None, x=0, y=0, width=10, height=20, markerPath='mapMarker.png', tree=None):
    super(Marker, self).__init__(parent)
    __slots__ = ('x', 'y', 'width', 'height', 'markerImagePath',)
    self._x = x
    self._y = y
    self.tag = None
    self.info = None
    self._width = width
    self._height = height
    self.imageMap = dict()
    self.styleSheet = 'opacity:0.9'
    self.markerImagePath = markerPath
    self.tree = tree

    self.initUI()

  def initUI(self):
    self.setGeometry(self._x, self._y, self._width, self._height)
    self.initIcon()

    self.currentFilePath = __file__
    self.__lastLocation = None
    self.setMouseTracking(True) # To allow for hovering detection

    if self.tree is not None:
        self.tree[(self._x, self._y)] = self
        print('added in', self.tree)

  def initIcon(self):
    imagePixMap = QPixmap(self.markerImagePath)
    icon = QIcon(imagePixMap)
    self.setIconSize(QtCore.QSize(self.width(), self.height()))
    self.setIcon(icon);
    self.setStyleSheet(self.styleSheet)

  def addTaggedInfo(self, info):
    self.info = info
    if self.tag:
        self.tag.close()
        print('hiding tag')
        self.tag = None # Garbage collection can now kick in

  def serialize(self):
    return self.__dict__

  def createTag(self, event):
    curPos = self.mapToGlobal(self.pos())
    print(self.pos(), curPos.x(), curPos.y())
    tagX = curPos.x()
    tagY = curPos.y()

    self.tag = Tag.Tag(
      parent=None, title = '@%s'%(time.ctime()),
      location = Tag.DynaItem(dict(x=tagX, y=tagY)),
      size = Tag.DynaItem(dict(x=300, y=240)),
      onSubmit = self.addTaggedInfo,
      metaData = dict(
        author = utils.getDefaultUserName(),
        filePath = self.currentFilePath,
        captureTime = time.time(), x = tagX, y = tagY
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
      self.hide()
      if isinstance(self.tree, dict):
        print('Popped marker', self.tree.pop((self._x, self._y), 'Not found'))
      del self
  
    else:
      # Thanks be to Stack Overflow
      buttonNumber = event.button()
      self.__pressPos, self.__movePos = None, None
      if buttonNumber == QtCore.Qt.LeftButton: # Left Click here 
        self.__movePos = event.globalPos()
        self.__pressPos = event.globalPos()

        if not self.tag:
            if self.info:
                self.tag = Tag.tagFromSource(self.info)
            else:
                self.createTag(event)
        else:
          self.tag.activateWindow()
   
  def __lt__(self, other):
    return  type(self) is type(other)\
        and (self._x < other._x) and (self._y < other._y)

  def __gt__(self, other):
    return  type(self) is type(other)\
        and (self._x > other._x) and (self._y > other._y)

  def __eq__(self, other):
    return type(self) is type(other)\
      and (self._x == other._x) and (self._y == other._y)
 
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
