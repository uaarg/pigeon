from typing import Tuple

from pyzbar.pyzbar import decode, ZBarSymbol
from PIL import Image, ImageDraw, ImageQt

def get_qr_box_bounds(qr_data) -> Tuple[tuple, tuple]:
    """Gets the bounds of the box surrounding a QR Code.

    Arguments:
        qr_data: Named Tuple containing data on QR code. 
                 Assumed not NULL.
    Returns:
        (top_left_rect_point, bottom_right_rect_point)
    """

    r = qr_data.rect
    return (
        (r.left, r.top),
        (r.left + r.width, r.top + r.height)
    )

def get_qr_data(filename):
    """
    Gets the QR code data of the QR code in an image

    Note:
        Assumes only 1 QR code per image

    Arguments:
        filename: The filename of the image to process

    Returns:
        Tuple containing: (QImage of processed data, QR Code data string)

    """
    qr_data = ""

    # First get Black and White Image
    image = Image.open(filename).convert("L")

    # Threshold the image such that pixels are either black or white
    image = image.point(lambda x: 0 if x < 128 else 255)

    data = decode(image, symbols=[ZBarSymbol.QRCODE])

    # Decode returns an array of named tuples
    # Note that the data field in the named tuple is binary
    if (len(data) == 0):
        qr_data = "No QR Code found."
    else:
        # Index 0 since we assume 1 QR code
        qr_data = data[0].data.decode('ascii')

        # Draw bounding box on the QR code
        image = image.convert("RGB") # Return to RGB mode
        ImageDraw.Draw(image).rectangle(
            get_qr_box_bounds(data[0]), outline="red", width=3)

    return (ImageQt.ImageQt(image), qr_data)

