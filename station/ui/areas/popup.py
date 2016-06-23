# Ruler class for measuring distance
from PyQt5 import QtCore, QtGui, QtWidgets

translate = QtCore.QCoreApplication.translate


class AboutPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("about_window")
        self.setMinimumSize(QtCore.QSize(500, 500))
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(1)
        self.setSizePolicy(size_policy)
        self.setWindowTitle(translate("About Window", "About"))
        self.initUI()

    def initUI(self):
        QtWidgets.QLabel("Pigeon is a cool piece of software", self)

