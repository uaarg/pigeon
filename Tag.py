#!/usr/bin/python3

# Author: Emmanuel Odeke <odeke@ualberta.ca>
# Module to allow for tagging and meta data entering

import sys
import time
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from threading import Lock

def labelEntryPairFromSource(srcDict):
    lbPair = LabelEntryPair(**srcDict)
    return lbPair

def tagFromSource(srcDict):
    entryList = srcDict.get('entryList', [])
    srcDict['entryList'] = [DynaItem(initArgs) for initArgs in entryList]
    return Tag(**srcDict)

class LabelEntryPair(object):
    def __init__(
      self, labelText, isMultiLine=True, title=None, parent=None,
      labelLocation=(), entryText=None, entryLocation=()
    ):
        self.__title = title
        self.__labelWidget = QtWidgets.QLabel(labelText, parent=parent)
        self.isMultiLine = isMultiLine
        __widget = QtWidgets.QTextEdit if isMultiLine else QtWidgets.QLineEdit
        self.__textGetter = 'toPlainText' if isMultiLine else 'text'
        self.__entryWidget = __widget(parent)
        self.__entryWidget.setText(entryText)
        self.entryLocation = entryLocation
        self.labelLocation = labelLocation

    def getContent(self):
        return dict(
            labelText = self.__labelWidget.text(),
            entryText = getattr(self.__entryWidget, self.__textGetter)()
        )

    def serialize(self):
        return dict(
          isMultiLine = self.isMultiLine,
          labelLocation = self.labelLocation,
          entryLocation = self.entryLocation, title = self.__title,
          labelText = self.__labelWidget.text(),
          entryText = getattr(self.__entryWidget, self.__textGetter)()
        )

    @property
    def title(self): return self.__title

    @property
    def entryWidget(self): return self.__entryWidget

    @property
    def labelWidget(self): return self.__labelWidget

    @property
    def getId(self): return self.__id

    def __str__(self):
        return self.__dict__.__str__()

class DynaItem:
    def __init__(self, initArgs):
        __slots__ = (arg for arg in initArgs)
        for arg in initArgs:
            setattr(self, arg, initArgs[arg])

class Tag(QtWidgets.QWidget):
    def __init__(
      self, parent=None, spacing=10, entryList=[], size=None,
      title='Tag', onSubmit=None, location=None, metaData=None
    ):
        super(Tag, self).__init__(parent=parent)
        self.entryList = entryList
        self.spacing   = spacing
        self.location    = location
        self.size        = size
        self.title       = title
        self.metaData  = metaData
        self.parent    = parent
        self.onSubmit    = onSubmit if onSubmit else lambda c : print(c)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def initUI(self):
        self.entries = []
        for entry in self.entryList:
            labelEntryItem = LabelEntryPair(
              entry.title, title=entry.title,
              isMultiLine = entry.isMultiLine,
              labelLocation=entry.labelLocation,
              entryLocation=entry.entryLocation, entryText=entry.entryText
            )
            self.entries.append(labelEntryItem)
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(self.spacing)

        for e in self.entries:
            self.grid.addWidget(e.labelWidget, *e.labelLocation)
            self.grid.addWidget(e.entryWidget, *e.entryLocation)

        saveButton = QtWidgets.QPushButton()
        saveButton.clicked.connect(self.submit)
        cancelButton = QtWidgets.QPushButton()
        cancelButton.clicked.connect(lambda : self.close())

        cancelButton.setText('&Cancel')
        saveButton.setText('&Save')

        lastRow = self.grid.rowCount() + 1
        self.grid.addWidget(saveButton, lastRow, 0)
        self.grid.addWidget(cancelButton, lastRow, 1)
        
        self.setLayout(self.grid)
        self.setGeometry(
          self.location.x, self.location.y,
          self.size.x, self.size.y
        )
        self.setWindowTitle(self.title)
        self.show()

    def submit(self):
        serialized = self.serialize()
        self.onSubmit(serialized)
        self.close()
        # Uncomment to test the serialization
        # t = tagFromSource(serialized)

    def serialize(self):
        return dict(
            location = self.location, 
            size = self.size, title = self.title,
            metaData = self.metaData, spacing = self.spacing, entryList = [
              item.serialize() for item in self.entries
            ]
        )

def main():
    app = QtWidgets.QApplication(sys.argv)
    t = Tag(
      title = 'Locked_Target',
      size = DynaItem(dict(x=200, y=200)),
      location = DynaItem(dict(x=600, y=200)),
      onSubmit = lambda content : print(content),
      entryList = [
        DynaItem(dict(title='Target', isMultiLine=False, entryLocation=(1, 1,), labelLocation=(1, 0,), entryText=None)),
        DynaItem(dict(title='Author', isMultiLine=False, entryLocation=(2, 1,), labelLocation=(2, 0,), entryText=None)),
        DynaItem(dict(title='Approx', isMultiLine=True, entryLocation=(3, 1,5, 1,), labelLocation=(3, 0,), entryText='10.23NE'))
    ])

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
