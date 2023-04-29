from base import BaseDummyProtocol
import random
import re


class DeviceProtocol(BaseDummyProtocol):
    log_name = "Airvalve"
    delimiter = b"\n"

    def __init__(self):
        super().__init__()
        self.replies = {
        }