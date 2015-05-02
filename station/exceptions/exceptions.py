"""
Custom exception classes for pigeon.
"""

class DataValidationException(BaseException):
    """
    Exception raised on received or generated data that is out of range or clearly incorrect.
    """
    def __init__(self, user_message):
        self.message = "Data invalid: " + user_message
