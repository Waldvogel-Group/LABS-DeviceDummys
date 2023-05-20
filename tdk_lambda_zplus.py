from base import BaseDummyProtocol
import random
import re


class DeviceProtocol(BaseDummyProtocol):
    delimiter = b"\r\n"
    log_name = "Z plus"

    def __init__(self):
        super().__init__()
        self.current = None
        self.voltage = 1
        # self.position = 1
        self.replies = {
            r"\*OPC\?": "1",
            r"\*IDN\?": "Manufacturer,zplus_dummy,1234,4.30.10.98",
            r"MEAS:CURR\?": (self.get_current, ""),
            r"MEAS:VOLT\?": (self.get_voltage, ""),
            r"CURR (?P<current>.*)": (self.set_current, None),
            r"VOLT (?P<voltage>.*)": (self.set_voltage, None),
        }

    def get_current(self, _):
        return str(self.current + (random.random()-0.5)*0.05)

    def set_current(self, match: re.Match):
        self.current = float(match.group("current"))

    def get_voltage(self, _):
        # self.voltage += 1.5
        return str(self.voltage)
    
    def set_voltage(self, match: re.Match):
        voltage = match.group("voltage")
        self.voltage = 60 if voltage == "MAX" else float(voltage)