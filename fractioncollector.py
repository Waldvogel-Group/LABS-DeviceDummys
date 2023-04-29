from base import BaseDummyProtocol
import random
import re


class DeviceProtocol(BaseDummyProtocol):
    log_name = "omnicoll"

    def __init__(self):
        super().__init__()
        self.replies = {
        }