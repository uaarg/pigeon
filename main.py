#!/usr/bin/python
"""
Main interface for ground station.
"""

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QCursor, QPixmap
# Import all from QtWidgets for development for now.
# So for classes that are part of QtWidgets, I've specifically stated QtWidget.Class() for now.
from PyQt5.QtWidgets import *


class GroundStation(QtWidgets.QMainWindow):
    def __init__(self, sysargs):
        super(GroundStation, self).__init__()

        # Set up window
        self.setWindowTitle("pigeon")
        self.setGeometry(300, 300, 250, 150)

        # Set up main display area
        self.imageLabel = QtWidgets.QLabel()
        self.setCentralWidget(self.imageLabel)

        # Set up cursor
        self.cursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.cursor)
        self.getCursorPosition()

        # Open image
        try:
            self.imagePath = sysargs[1]
        except:
            print("Usage: python main.py [image_path]")
            sys.exit()
        else:
            self.openImage(self.imagePath)


    def openImage(self, filename):
        """
        Opens image from specified path.
        """
        if filename:
            image = QImage(filename)
            if image.isNull():
                QMessageBox.information(self, "Error", "Can't load image %s." %(filename))
            else:
                # Convert from QImage to QPixmap, and display
                self.imageLabel.setPixmap(QPixmap.fromImage(image))

    def getCursorPosition(self):
        """
        Gets the position of the mouse cursor on the image.
        """
        self.cursorPosition = QWidget.mapFromGlobal(self, self.cursor.pos())


def main():
    print("Ground station running.")
    app = QtWidgets.QApplication(sys.argv)
    gs = GroundStation(sys.argv)
    gs.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
