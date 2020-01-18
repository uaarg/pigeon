from pyzbar.pyzbar import decode, ZBarSymbol
from PIL import Image, ImageFilter, ImageDraw

def get_qr_data(filename):
    """
    Gets the QR code data of the QR code in an image

    Arguments:
        filename: The filename of the image to process

    Note:
    Assumes only 1 QR code per image
    """

    # First get Black and White Image
    image = Image.open(filename).convert("L")

    data = decode(image, symbols=[ZBarSymbol.QRCODE])

    # Decode return an array of named tuples
    # Note that the data field in the named tuple is binary
    if (len(data) == 0):
        return "NO QR CODE"

    return data[0].data.decode('ascii')

