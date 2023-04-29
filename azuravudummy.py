import re

from base import BaseDummyProtocol


class DeviceProtocol(BaseDummyProtocol):
    delimiter = b"\r"
    log_name = "Azura VU"

    def __init__(self):
        super().__init__()
        self.position = 1
        self.replies = {
            r"IDENTIFY\?": "IDENTIFY:dummy_azura,Mo,Model1,12345,1.2.3.4.5,6,6",
            r"POSITION:(?P<position>.*)": (self.set_position, "OK"),
            r"POSITION\?": (self.get_position, ""),
            r"STATUS\?": f"STATUS:1234,just_being_me,never_heard_of_that,you_better_leave,{self.position},123457809473590,1,1,1,1,1,1,1,1,too_many_fields,djs,over_9000",
            r"VALVE\?": f"VALVE:43dfhg0782345,9,6,8,7,6,5,4,3,2,1,0,hjkh,none"
        }

    def set_position(self, match: re.Match):
        self.position = int(match.group("position"))

    def get_position(self, _):
        return f"POSITION:{self.position}"
