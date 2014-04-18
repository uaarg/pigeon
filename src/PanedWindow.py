#!/usr/bin/python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>
# Window that automatically moves it's children along with it
# Has two extreme side bars, left and right that you can choose to
# rig different actions to

import sys
import time
from PyQt5 import QtWidgets, QtGui, QtCore

class Pane(QtWidgets.QFrame):
  def __init__(self, parent=None, onClick=None):
    super(Pane, self).__init__(parent)
    self.mouseIsInPane = False
    self.onClick = onClick
    self.setMouseTracking(True)

  def leaveEvent(self, event):
    if self.mouseIsInPane:
      self.setFrameShadow(QtWidgets.QFrame.Raised)
      self.setFrameShape(QtWidgets.QFrame.NoFrame)
      self.mouseIsInPane = False

  def enterEvent(self, event):
    if not self.mouseIsInPane:
      self.setFrameShadow(QtWidgets.QFrame.Raised)
      self.setFrameShape(QtWidgets.QFrame.WinPanel)
      self.mouseIsInPane = True

  def mousePressEvent(self, event):
    print('Mouse clicked', event.type(), self.onClick)
    if self.onClick: self.onClick()

  def moveEvent(self, event):
    print('moveEvent', event.type())

  def setGeometry(self, *args, **kwargs):
    print(args, kwargs)
    super(Pane, self).setGeometry(*args, **kwargs)

class PanedWindow(QtWidgets.QMainWindow):
  def __init__(self, parent=None, onLeftPaneClick=None, onRightPaneClick=None):
    super(PanedWindow, self).__init__(parent)

    self.lastGeometry = self.geometry()
    self.onLeftPaneClick = onLeftPaneClick
    self.onRightPaneClick = onRightPaneClick

    self.children = dict()
    self.setMouseTracking(True)

    # Don't forget to invoke addPanes() after you've added all the
    # desired children => Reason: So that the side panes always
    # appear onto of all content in the Window

  def genericDimensionResolver(curGeometry, parent, child):
    return (child.x(), child.y(), parent.width(), child.height())

  def addChild(self, childConstructor, 
      initArgs=dict(), dimenResolver=genericDimensionResolver
  ):
    _id = len(self.children)
    child = childConstructor(self, **initArgs)
    self.children[_id] = dict(child=child, dResolver=dimenResolver)
    return _id

  def lPaneDimenResolve(self, curGeometry, parent, child):
    return (0, 0, parent.width() // 12, parent.height(),)

  def addPanes(self):
    leftPaneId = self.addChild(
      Pane, dict(onClick=self.onLeftPaneClick), self.lPaneDimenResolve
    )

    def rPaneDimenResolve(geom, parent, child):
      leftPanePropertyDict = self.children.get(leftPaneId, None)
      if leftPanePropertyDict:
        leftPane = leftPanePropertyDict['child']
        ldResolver = leftPanePropertyDict['dResolver']
        
        # Right pane is a mirror of the left, about mid width
        return (parent.width() - leftPane.width(), 0, 
            parent.width() // 12, parent.height(),
        )
      else:
        return (0, 0, 0, 0,)

    rightPaneId = self.addChild(
      Pane, dict(onClick=self.onRightPaneClick), rPaneDimenResolve
    )
    
  def changeEvent(self, event):
    curGeometry = self.geometry()
    if curGeometry != self.lastGeometry:
      for _id, propertyDict in self.children.items():
         child, dResolver = propertyDict['child'], propertyDict['dResolver']
         child.setGeometry(*dResolver(curGeometry, self, child))

    self.lastGeometry = curGeometry

def main():
  app = QtWidgets.QApplication(sys.argv)
  pw = PanedWindow()
  pw.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
