import logging

class FileError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message