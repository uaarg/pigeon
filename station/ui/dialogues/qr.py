from PyQt5.QtWidgets import QDialog
from PyQt5 import QtWidgets, QtGui

import misc.qr as qr

class QrDiag(QDialog):
    """Dialogue Class for QR code processing."""

    def __init__(self, parent, image_path) -> None:
        """Init layout of this diag, then display."""
        super().__init__(parent)

        processed_image, qr_data = qr.get_qr_data(image_path)

        # Need to convert PIL image to pixmap
        pixmap = QtGui.QPixmap.fromImage(processed_image)

        dialog_layout = QtWidgets.QVBoxLayout()

        # QR Code Data
        qr_result_label = QtWidgets.QLineEdit()
        qr_result_label.setText(qr_data)
        qr_result_label.setReadOnly(True)
        dialog_layout.addWidget(qr_result_label)

        # QR Code Image
        qr_image_label = QtWidgets.QLabel()
        qr_image_label.setPixmap(pixmap)
        dialog_layout.addWidget(qr_image_label)

        self.setLayout(dialog_layout)
        self.setWindowTitle("QR Code Data")

        self.show()
