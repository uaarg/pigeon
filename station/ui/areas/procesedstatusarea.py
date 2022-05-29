from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QSizePolicy

class ProcessedStatusArea(QtWidgets.QWidget):
    """Shows image processing status and controls if image is a web image."""

    mark_processed_clicked = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.processed_status = ProcessedStatus(self)
        self.layout.addWidget(self.processed_status)
        self.mark_processed_clicked.connect(lambda: self.set_is_processed(True))

        self.mark_processed_button = QtWidgets.QPushButton("Mark As Processed", self)
        self.mark_processed_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.mark_processed_button.clicked.connect(self.mark_processed_clicked)
        self.layout.addWidget(self.mark_processed_button)

    def set_is_processed(self, state: bool):
        if state:
            self.processed_status.set_status(True)
            self.mark_processed_button.setDisabled(True)
        else:
            self.processed_status.set_status(False)
            self.mark_processed_button.setDisabled(False)

class ProcessedStatus(QtWidgets.QWidget):
    """Shows human readable text for image processing status."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        size_policy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.setSizePolicy(size_policy)
        self.layout = QtWidgets.QHBoxLayout(self)

        self.label = QtWidgets.QLabel("Status:", self)
        label_font = QtGui.QFont()
        label_font.setBold(True)
        self.label.setFont(label_font)
        self.layout.addWidget(self.label)

        self.status = QtWidgets.QLabel("", self)
        self.layout.addWidget(self.status)

    def set_status(self, status: bool):
        """Change status text."""
        if (status):
            self.status.setText("Processed")
        else:
            self.status.setText("In Progress")