import io
import os
import uuid

import qrcode
from django.utils.translation import gettext_lazy as _
from qrcode.image.pil import PilImage

from .exceptions import QRCodeCharLimitException


def generate_qrcode(path, value):
    filename = f"{uuid.uuid4().hex}-qrcode.png"
    with open(os.path.join(path, filename), "wb") as f:
        f.write(create_qrcode_content(value))
    return filename


def create_qrcode_content(value, error_correction=qrcode.constants.ERROR_CORRECT_Q):
    """
    :param value: value of the qrcode
    :param error_correction: error correction int
    """
    qr = qrcode.QRCode(
        error_correction=error_correction,
        image_factory=PilImage,
        box_size=100,
        border=0,
    )
    qr.add_data(value)
    try:
        img = qr.make_image()
    except qrcode.exceptions.DataOverflowError:
        raise QRCodeCharLimitException(_("QR code value exceed limit."))
    output = io.BytesIO()
    img.save(output, "PNG")
    contents = output.getvalue()
    output.close()
    return contents
