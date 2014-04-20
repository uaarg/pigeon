# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gcs.ui'
#
# Created: Sun Apr 20 01:19:36 2014
#      by: PyQt5 UI code generator 5.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(879, 693)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QtCore.QSize(200, 200))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.thumbnailScrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.thumbnailScrollArea.setGeometry(QtCore.QRect(10, 520, 851, 121))
        self.thumbnailScrollArea.setMinimumSize(QtCore.QSize(521, 81))
        self.thumbnailScrollArea.setWidgetResizable(True)
        self.thumbnailScrollArea.setObjectName("thumbnailScrollArea")
        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 849, 119))
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")
        self.thumbnailScrollArea.setWidget(self.scrollAreaWidgetContents_2)
        self.fullSizeImageScrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.fullSizeImageScrollArea.setGeometry(QtCore.QRect(10, 20, 851, 491))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(100)
        sizePolicy.setHeightForWidth(self.fullSizeImageScrollArea.sizePolicy().hasHeightForWidth())
        self.fullSizeImageScrollArea.setSizePolicy(sizePolicy)
        self.fullSizeImageScrollArea.setMinimumSize(QtCore.QSize(681, 451))
        self.fullSizeImageScrollArea.setWidgetResizable(True)
        self.fullSizeImageScrollArea.setObjectName("fullSizeImageScrollArea")
        self.midWidget = QtWidgets.QWidget()
        self.midWidget.setGeometry(QtCore.QRect(0, 0, 849, 489))
        self.midWidget.setObjectName("midWidget")
        self.fullSizeImageScrollArea.setWidget(self.midWidget)
        self.countDisplayLabel = QtWidgets.QLabel(self.centralwidget)
        self.countDisplayLabel.setGeometry(QtCore.QRect(100, 0, 641, 20))
        self.countDisplayLabel.setMinimumSize(QtCore.QSize(200, 10))
        self.countDisplayLabel.setText("")
        self.countDisplayLabel.setObjectName("countDisplayLabel")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 879, 25))
        self.menubar.setDefaultUp(False)
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))

