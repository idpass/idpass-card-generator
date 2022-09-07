class QRCodeCharLimitException(Exception):
    """
    Raise this exception if qrcode lib raise
    DataOverflowError to know that we have reach the char limit
    """

    pass
