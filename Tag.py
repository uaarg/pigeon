#!/usr/bin/python3

# Author: Emmanuel Odeke <odeke@ualberta.ca>
# Module to allow for tagging and meta data entering

import sys
import time
from PyQt5 import QtWidgets
from threading import Lock

class LabelEntryPair(object):
    __idCounter = 0
    __classLock = Lock()
    def __init__(
      self, labelText, entryWidget=None, title=None, entryLocation=(),
      labelLocation=(), initContent=None, parent=None
    ):
        self.__title = title
        self.__labelWidget = QtWidgets.QLabel(labelText, parent=parent)
        self.__entryWidget = entryWidget if entryWidget else QtWidgets.QLineEdit(parent=parent)
        self.__entryWidget.setText(initContent)
        self.entryLocation = entryLocation
        self.labelLocation = labelLocation
        print(title, entryWidget)

        # For thread safety
        self.__classLock.acquire()
        self.__id = self.__idCounter
        self.__idCounter = self.__idCounter + 1
        self.__classLock.release()

    def getContent(self):
        return dict(
            label = self.__labelWidget.text(),
            entryText = self.__entryWidget.text()
        )

    @property
    def title(self): return self.__title
    @property
    def entryWidget(self): return self.__entryWidget

    @property
    def labelWidget(self): return self.__labelWidget

    @property
    def getId(self): return self.__id

    def __repr__(self):
        return self.__dict__
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
        self.__entryList = entryList
        self.__spacing   = spacing
        self.location    = location
        self.size        = size
        self.title       = title
        self.__metaData  = metaData
        self.__parent    = parent
        self.onSubmit    = onSubmit if onSubmit else lambda c : print(c)
        self.initUI()

    def initUI(self):
        self.__entries = []
        for entry in self.__entryList:
            labelEntryItem = LabelEntryPair(
              entry.title, title=entry.title,
              entryWidget=QtWidgets.QTextEdit if entry.isMultiLine else None,
              labelLocation=entry.lLocation,
              entryLocation=entry.eLocation, initContent=entry.initContent
            )
            self.__entries.append(labelEntryItem)
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(self.__spacing)

        for e in self.__entries:
            self.grid.addWidget(e.labelWidget, *e.labelLocation)
              # Bug notice: QT won't recognize unravelled
              # tuples for grid location for multiline elements
              # eg a TextEdit
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
        content = dict()
        for item in self.__entries:
          # To allow for quick searches
          content[item.title] = item.getContent()

        content['tagSaveTime'] = time.time()
        content['metaData'] = self.__metaData

        self.onSubmit(content)
        self.close()

def main():
    app = QtWidgets.QApplication(sys.argv)
    t = Tag(
      title = 'Locked_Target',
      size = DynaItem(dict(x=200, y=200)),
      location = DynaItem(dict(x=600, y=200)),
      onSubmit = lambda content : print(content),
      entryList = [
        DynaItem(dict(title='Target', isMultiLine=False, eLocation=(1, 1,), lLocation=(1, 0,), initContent=None)),
        DynaItem(dict(title='Author', isMultiLine=False, eLocation=(2, 1,), lLocation=(2, 0,), initContent=None)),
        DynaItem(dict(title='Approx', isMultiLine=False, eLocation=(3, 1,), lLocation=(3, 0,), initContent='10.23NE'))
    ])

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
