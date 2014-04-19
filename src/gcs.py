# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gcs.ui'
#
# Created: Fri Apr 18 18:35:23 2014
#      by: PyQt5 UI code generator 5.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(873, 638)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QtCore.QSize(200, 200))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.thumbnailScrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.thumbnailScrollArea.setGeometry(QtCore.QRect(80, 520, 711, 81))
        self.thumbnailScrollArea.setMinimumSize(QtCore.QSize(521, 81))
        self.thumbnailScrollArea.setWidgetResizable(True)
        self.thumbnailScrollArea.setObjectName("thumbnailScrollArea")
        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 709, 79))
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
        self.nextButton = QtWidgets.QPushButton(self.centralwidget)
        self.nextButton.setGeometry(QtCore.QRect(790, 520, 71, 81))
        self.nextButton.setMinimumSize(QtCore.QSize(71, 81))
        self.nextButton.setStyleSheet("font: 75 11pt \"URW Gothic L\";")
        self.nextButton.setObjectName("nextButton")
        self.previousButton = QtWidgets.QPushButton(self.centralwidget)
        self.previousButton.setGeometry(QtCore.QRect(10, 520, 71, 81))
        self.previousButton.setMinimumSize(QtCore.QSize(71, 81))
        self.previousButton.setStyleSheet("font: 75 11pt \"URW Gothic L\";")
        self.previousButton.setObjectName("previousButton")
        self.countDisplayLabel = QtWidgets.QLabel(self.centralwidget)
        self.countDisplayLabel.setGeometry(QtCore.QRect(100, 0, 641, 20))
        self.countDisplayLabel.setMinimumSize(QtCore.QSize(200, 10))
        self.countDisplayLabel.setText("")
        self.countDisplayLabel.setObjectName("countDisplayLabel")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 873, 25))
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
        self.nextButton.setText(_translate("MainWindow", "Next"))
        self.previousButton.setText(_translate("MainWindow", "Previous"))

