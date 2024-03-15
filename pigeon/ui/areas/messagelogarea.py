from PyQt6 import QtCore, QtWidgets
import datetime

from pigeon.ui.commonwidgets import BoldQLabel

translate = QtCore.QCoreApplication.translate


class MessageLogArea(QtWidgets.QFrame):

    def __init__(self, *args, minimum_width=250, **kwargs):
        super().__init__(*args, **kwargs)

        size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(minimum_width, 200))

        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.setObjectName("message_log_area")

        self.title = BoldQLabel(self)
        self.title.setText("Message Log:")

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(self.title, 0, 0, 1, 1)

        self.textbox = QtWidgets.QTextEdit()
        self.textbox.setObjectName("message_log_textbox")
        self.textbox.setReadOnly(True)
        self.textbox.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.layout.addWidget(self.textbox, 1, 0, 1, 1)

    def queueMessage(self, message):
        time = datetime.datetime.now().strftime("%H:%M:%S")
        self.textbox.append(f"[{time}] {message}")
