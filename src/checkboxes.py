from PyQt5 import QtCore, QtGui, QtWidgets

class Checkbox_Dialog():

    def __init__(self, parent = None):
        self.Dialog = QtWidgets.QDialog(parent)
        self.setupUi()
        self.pushButton.clicked.connect(self.Dialog.reject)

        self.Dialog.setModal(True)
        # self.Dialog.setWindowModality(QtCore.Qt.WindowModal)
        # self.Dialog.setWindowModality(QtCore.Qt.ApplicationModal)

    def setupUi(self):


        self.Dialog.setObjectName("Pick columns to export")
        self.Dialog.resize(636, 470)


        self.horizontalLayout = QtWidgets.QHBoxLayout(self.Dialog)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.widget = QtWidgets.QWidget(self.Dialog)
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollArea = QtWidgets.QScrollArea(self.widget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 622, 408))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.scrollAreaWidgetContents)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.widget_3 = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        self.widget_3.setObjectName("widget_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.widget_3)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")

        # self.checkBox = QtWidgets.QCheckBox(self.widget_3)
        # self.checkBox.setObjectName("checkBox")
        # self.verticalLayout_2.addWidget(self.checkBox)


        self.horizontalLayout_3.addWidget(self.widget_3)
        self.widget_4 = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        self.widget_4.setObjectName("widget_4")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.widget_4)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")



        self.widgets = [self.widget_3, self.widget_4]
        self.verticalLayouts = [self.verticalLayout_2, self.verticalLayout_3]

        self.horizontalLayout_3.addWidget(self.widget_4)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.widget_2 = QtWidgets.QWidget(self.widget)
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.widget_2)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButton = QtWidgets.QPushButton(self.widget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.commandLinkButton = QtWidgets.QCommandLinkButton(self.widget_2)
        self.commandLinkButton.setObjectName("commandLinkButton")
        self.horizontalLayout_2.addWidget(self.commandLinkButton)
        self.verticalLayout.addWidget(self.widget_2)
        self.horizontalLayout.addWidget(self.widget)






        # self.verticalLayouts = [self.verticalLayout, self.verticalLayout_2]

        self.checkBoxes = {}

        self.retranslateUi(self.Dialog)
        QtCore.QMetaObject.connectSlotsByName(self.Dialog)

    def addButton(self, text):
        _translate = QtCore.QCoreApplication.translate
        cbox = QtWidgets.QCheckBox(self.widgets[(len(self.checkBoxes) + 1) % 2])

        self.checkBoxes[text] = cbox
        self.checkBoxes[text].setCheckable(True)
        self.checkBoxes[text].setChecked(True)
        self.checkBoxes[text].setObjectName("checkBox {}".format(text))
        self.verticalLayouts[len(self.checkBoxes) % 2].addWidget(self.checkBoxes[text])
        self.checkBoxes[text].setText(_translate("Dialog", text))





    def getCheckedBoxes(self, input, callback = None):

        def wrapCallback():
            if callback: callback()
            self.Dialog.accept()


        self.commandLinkButton.clicked.connect(wrapCallback)
        self.addOptions(input)

        # QtWidgets.QCheckBox.isChecked()

        self.Dialog.exec_()

        return {thing:cbox.isChecked() for thing, cbox in self.checkBoxes.items()}





    def addOptions(self, opts):
        for opt in opts:
            self.addButton(str(opt))


    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))

        self.pushButton.setText(_translate("Dialog", "Cancel"))
        self.commandLinkButton.setText(_translate("Dialog", "Do the export!"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = Checkbox_Dialog()
    ui.getCheckedBoxes(["pizza", "cake", "toast"])
    sys.exit(app.exec_())

