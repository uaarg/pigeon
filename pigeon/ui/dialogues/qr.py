from PyQt6.QtWidgets import QDialog
from PyQt6 import QtWidgets, QtGui

import pigeon.misc.qr as qr


class QrDiag(QDialog):
    """Dialogue Class for QR code processing."""

    def __init__(self, parent, image_path) -> None:
        """Init layout of this diag, then display."""
        super().__init__(parent)

        qr_datas, processed_image = qr.get_qr_data(image_path)

        # Need to convert PIL image to pixmap
        pixmap = QtGui.QPixmap.fromImage(processed_image)

        dialog_layout = QtWidgets.QVBoxLayout()

        # QR Code Data
        # Add a new line for each QR code
        for qr_data in qr_datas:
            qr_result_label = QtWidgets.QLineEdit()
            qr_result_label.setText(qr_data)
            qr_result_label.setReadOnly(True)
            dialog_layout.addWidget(qr_result_label)

        # QR Code Image
        qr_image_label = QtWidgets.QLabel()
        # Scale the image to 512px in height to fit on screen
        qr_image_label.setPixmap(pixmap.scaledToHeight(512))
        dialog_layout.addWidget(qr_image_label)

        self.setLayout(dialog_layout)
        self.setWindowTitle("QR Code Data")

        self.show()
