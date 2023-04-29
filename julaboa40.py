from base import BaseDummyProtocol

from twisted.internet import reactor

import random
import re


class DeviceProtocol(BaseDummyProtocol):
    delimiter = b"\r\n"
    log_name = "Presto A40"

    def __init__(self):
        super().__init__()
        self.ambient = 21.45
        self.temp = 21.45
        self.running = False
        self.status = "00 MANUAL STOP"
        self.working_temps = [0, 0, 0]
        self.current_working_temp = 0
        self.replies = {
            r"out_mode_05 (?P<on_off>[01])": (self.set_running, None),
            r"out_mode_01 (?P<working_temp>[012])": (self.set_current_workingtemp, None),
            r"out_sp_0(?P<index>[012]) (?P<temp>.*)": (self.set_workingtemp, None),
            r"in_pv_00": (self.get_temp, ""),
            r"status": (self.get_status, ""),
        }
        self.one_degree_step()

    def set_running(self, match: re.Match):
        self.running = bool(match.group("on_off"))
        if self.running:
            self.status = "03 MANUAL START"
        else:
            self.status = "02 MANUAL STOP"

    def one_degree_step(self):
        if self.running:
            goal = self.working_temps[self.current_working_temp]
        else:
            goal = self.ambient
        if self.temp > goal:
            self.temp -= 1
        elif self.temp < goal:
            self.temp += 1
        reactor.callLater(1, self.one_degree_step)

    def set_current_workingtemp(self, match: re.Match):
        self.current_working_temp = int(match.group("working_temp"))

    def set_workingtemp(self, match: re.Match):
        self.working_temps[int(match.group("index"))] = float(match.group("temp"))

    def get_temp(self, _):
        return str(self.temp + (random.random()-0.5)*2)
    
    def get_status(self, _):
        return self.status
