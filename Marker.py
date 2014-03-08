#!/usr/bin/python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import sys
import time
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QImage, QCursor, QPixmap, QIcon

import Tag # Local module
import utils # Local module

class Marker(QtWidgets.QPushButton):
  def __init__(self, parent=None, x=0, y=0, width=20, height=20, markerPath='mapMarker.png'):
    super(Marker, self).__init__(parent)
    self._x = x
    self._y = y
    self.tag = None
    self.info = None
    self._width = width
    self._height = height
    self.styleSheet = 'opacity:0.9'
    self.markerImagePath = markerPath

    self.initUI()

  def initUI(self):
    self.setGeometry(self._x, self._y, self._width, self._height)
    self.initIcon()

    self.currentFilePath = __file__
    self.__lastLocation = None
    self.setMouseTracking(True) # To allow for hovering detection

  def initIcon(self):
    imagePixMap = QPixmap(self.markerImagePath)
    icon = QIcon(imagePixMap)
    self.setIconSize(QtCore.QSize(self.width(), self.height()))
    self.setIcon(icon);
    self.setStyleSheet(self.styleSheet)

  def addTaggedInfo(self, info):
    self.info = info
    if self.tag:
        self.tag.hide()
        self.tag = None # Garbage collection can now kick in

  def serialize(self):
    pass

  def createTag(self, event):
    curPos = self.pos()
    self.tag = Tag.Tag(
      parent=None, title = '@%s'%(time.ctime()),
      location = Tag.DynaItem(dict(x=curPos.x(), y=curPos.y())),
      size = Tag.DynaItem(dict(x=300, y=240)),
      onSubmit = self.addTaggedInfo,
      metaData = dict(
        author = utils.getDefaultUserName(),
        filePath = self.currentFilePath,
        captureTime = time.time(), x = event.x(), y = event.y()
      ),

      entryList = [
        Tag.DynaItem(dict(
            title='Location', isMultiLine=False,
            entryLocation=(1, 1,), labelLocation=(1, 0,),
            entryText='%s, %s'%(event.x(), event.y())
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
    # Thanks be to Stack Overflow
    buttonNumber = event.button()
    self.__pressPos, self.__movePos = None, None
    if buttonNumber == QtCore.Qt.LeftButton: # Left Click here 
        self.__movePos = event.globalPos()
        self.__pressPos = event.globalPos()
        print(self.__dict__)
        # print(self.__movePos, self.__pressPos)

        if not self.tag:
          self.createTag(event)
        else:
          self.tag.activateWindow()
    elif buttonNumber == QtCore.Qt.RightButton: # Right Click here
        self.hide()
        del self

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
