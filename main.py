#!/usr/bin/python

"""
Main interface for ground station.
"""

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QCursor, QPixmap
# Import all from QtWidgets for development for now.
from PyQt5.QtWidgets import *


class GroundStation(QtWidgets.QMainWindow):
    def __init__(self):
        super(GroundStation, self).__init__()

        # Set up window
        self.setWindowTitle("pigeon")
        self.setGeometry(300, 300, 250, 150)

        # Set up main display area
        self.imageLabel = QLabel()
        self.setCentralWidget(self.imageLabel)

        # Set up cursor
        self.cursor = QCursor()
        self.setCursor(self.cursor)

        self.openImage("data/processed/101.jpg")
        self.show()

    def openImage(self, filename):
        """
        Opens image from specified path.
        """
        if filename:
            image = QtGui.QImage(filename)
            if image.isNull():
                QMessageBox.information(self, "Error", "Can't load image %s." %(filename))
            else:
                # Convert from QImage to QPixmap, and display
                self.imageLabel.setPixmap(QPixmap.fromImage(image))

def main():
    print("Ground station running.")
    app = QtWidgets.QApplication(sys.argv)
    gs = GroundStation()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
