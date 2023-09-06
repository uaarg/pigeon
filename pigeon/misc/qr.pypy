from typing import List, Tuple

from pyzbar.pyzbar import Decoded, decode, ZBarSymbol
from PIL import Image, ImageDraw, ImageQt, ImageFont


def get_qr_box_bounds(qr_data) -> Tuple[tuple, tuple]:
    """Gets the bounds of the box surrounding a QR Code.

    Arguments:
        qr_data: Named Tuple containing data on QR code.
                 Assumed not NULL.
    Returns:
        (top_left_rect_point, bottom_right_rect_point)
    """

    r = qr_data.rect
    return ((r.left, r.top), (r.left + r.width, r.top + r.height))


def get_qr_text_location(qr_data):
    """Get location to place enumeration text for QR code."""
    r = qr_data.rect
    return (r.left + r.width / 2, r.top + r.height / 2)


def get_font_for_qr():
    """The ImageFont Class for use in drawing the text."""
    # First try a standard font.
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf", size=20)

    except OSError:
        # If failed, just use default
        return ImageFont.load_default()


def get_qr_data(filename):
    """
    Gets the QR code data of the QR code in an image

    Arguments:
        filename: The filename of the image to process

    Returns:
        Tuple containing: (QR Code Strings, Anotated Image as QImage)
            The QR Code Strings are enumerated. e.g. "1. <QR-DATA>"
    """
    qr_data = ""

    # First get Black and White Image
    image = Image.open(filename)
    image = image.convert("L")

    # Threshold the image such that pixels are either black or white
    image = image.point(lambda x: 0 if x < 128 else 255)

    # Decode returns an array of named tuples
    # Note that the data field in the named tuple is binary
    qr_codes_found: List[Decoded] = decode(image, symbols=[ZBarSymbol.QRCODE])

    if len(qr_codes_found) == 0:
        return (["No QR Code found."], image)

    qr_code_strings = []
    image = image.convert("RGB")  # Return to RGB mode

    for i, qr_code in enumerate(qr_codes_found):
        qr_data = "{}. {}".format(i, qr_code.data.decode('ascii'))

        # Draw bounding box on the QR code
        drawer = ImageDraw.Draw(image)
        drawer.rectangle(get_qr_box_bounds(qr_code), outline="red", width=3)

        # Draw a number representing the QR code
        drawer.text(get_qr_text_location(qr_code),
                    str(i),
                    fill="red",
                    stroke_width=3,
                    stroke_fill="white",
                    font=get_font_for_qr())

        qr_code_strings.append((qr_data))

    return (qr_code_strings, ImageQt.ImageQt(image))
