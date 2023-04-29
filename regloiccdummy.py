import re

from base import BaseDummyProtocol
from twisted.internet import reactor, error


EVENT_INTERVAL = .25


def discrete2(number):
    assert number < 10
    s = f"{number:.2f}"
    whole, decimals = s.split(".")
    return f"{int(whole + decimals):0>4}"


def discrete4(number):
    assert number < 4294967295
    return f"{int(number):0>10}"


def volume2(number):
    number = f"{abs(number):.3e}"
    number = number[0] + number[2:5] + number[-3] + number[-1]
    return number


def volume2_to_float(string):
    base_int, base_dec, exp = int(string[:1]), int(string[1:-2]), int(string[-2:])
    base = float(f"{base_int}.{base_dec}")
    return base*10**exp


def volume1(number):
    number = f"{abs(number):.3e}"
    number = number[0] + number[2:5] + "E" + number[-3] + number[-1]
    return number


class Channel:

    def __init__(self, channelnumber):
        self.number = channelnumber
        self.state = "C"  # A: pumping, B: pause between cycles, C: stopped, D: calibrationpumping, E: waiting for input
        self._remaining_time = 0  # time in seconds
        self._dosed_volume = 0  # volume in ml
        self._remaining_cycles = 0  # remaining cycles
        self._vol_rate = 0  # rate in ml/min
        self._target_vol = 0  # target volume in ml
        self.event_string = None
        self._delayed_call = None

    def run(self):
        self.state = "A"
        reactor.callLater(EVENT_INTERVAL, self._increase_counts)

    def stop(self):
        if self.state != "C":
            self.state = "C"    
            self.event_string = f"^X{self.number}|A"
            self._remaining_time = 0
            self._dosed_volume = 0
            try:
                self._delayed_call.cancel()
            except AttributeError:
                pass
            except error.AlreadyCalled:
                pass
            except error.AlreadyCancelled:
                pass

    def _increase_counts(self):
        self._dosed_volume += EVENT_INTERVAL*self._vol_rate/60
        remaining_vol = self._target_vol - self._dosed_volume
        if remaining_vol <= 0:
            self.stop()
        else:
            self._remaining_time = 60*remaining_vol/self._vol_rate
            self.event_string = f"^U{self.number}|{self.state}|{self.remaining_time}|{self.dosed_volume}|{self.remaining_cycles}"
            self._delayed_call = reactor.callLater(EVENT_INTERVAL, self._increase_counts)

    @property
    def remaining_time(self):
        return discrete4(self._remaining_time)

    @remaining_time.setter
    def remaining_time(self, time):
        self._remaining_time = time

    @property
    def dosed_volume(self):
        return discrete4(self._dosed_volume*1000)  # actual device gives this in microliter

    @dosed_volume.setter
    def dosed_volume(self, volume):
        self._dosed_volume = volume

    @property
    def remaining_cycles(self):
        return discrete2(self._remaining_cycles)

    @remaining_cycles.setter
    def remaining_cycles(self, cycles):
        self._remaining_cycles = cycles

    @property
    def vol_rate(self):
        return volume1(self._vol_rate)

    @vol_rate.setter
    def vol_rate(self, rate):
        self._vol_rate = volume2_to_float(rate)

    @property
    def target_vol(self):
        return volume1(self._target_vol)

    @target_vol.setter
    def target_vol(self, vol):
        self._target_vol = volume2_to_float(vol)


class DeviceProtocol(BaseDummyProtocol):
    delimiter = b"\r\n"
    log_name = "Reglo ICC"

    def __init__(self):
        super().__init__()
        self._channel: list[Channel] = []
        self.channelcount = 4
        self.sends_events = False
        self.non_delimited_replies = {
            r"(?P<channel>.*)H": (self.start_channel, "*"),
            r"(?P<channel>.*)I": (self.stop_channel, "*"),
            r"(?P<channel>.*)J": "*",
            r"(?P<channel>.*)K": "*",
            r"@(?P<address>.*)": "*",
            r"(?P<channel>.*)~(?P<value>.*)": "*",
            r"(?P<channel>.*)xE(?P<value>.*)": (self.event_on_off, "*"),
            r"(?P<channel>.*)O": "*",
            r"(?P<channel>.*)M": "*",
        }
        self.replies = {
            r"(?P<channel>.*)xA": f"{self.channelcount}",
            r"(?P<channel>.*)f(?P<vol_rate>.*)": (self.return_vol_rate, ""),
            r"(?P<channel>.*)v(?P<target_vol>.*)": (self.return_target_vol, ""),
            r"(?P<channel>.*)\(": "1234",
        }

    @property
    def channelcount(self):
        return len(self._channel)

    @channelcount.setter
    def channelcount(self, value: int):
        self._channel = [Channel(i+1) for i in range(value)]

    def get_channel_from_match(self, match):
        return self._channel[int(match.group("channel"))-1]

    def return_vol_rate(self, match: re.Match):
        channel = self.get_channel_from_match(match)
        channel.vol_rate = match.group("vol_rate")
        return channel.vol_rate

    def return_target_vol(self, match: re.Match):
        channel = self.get_channel_from_match(match)
        channel.target_vol = match.group("target_vol")
        return channel.target_vol

    def _run_channel_method(self, match: re.Match, method: str):
        channelnumber = int(match.group("channel"))
        if channelnumber == 0:
            channels = self._channel
        else:
            channels = [self.get_channel_from_match(match)]
        for channel in channels:
            getattr(channel, method)()

    def start_channel(self, match: re.Match):
        self._run_channel_method(match, "run")

    def stop_channel(self, match: re.Match):
        self._run_channel_method(match, "stop")

    def event_on_off(self, match: re.Match):
        value = match.group("value")
        if value == "1":
            self.sends_events = True
            self.send_event_string()
        elif value == "0":
            self.sends_events = False

    def send_event_string(self):
        if self.sends_events:
            encoded_event_string = b""
            for channel in self._channel:
                if channel.event_string:
                    channel_event_string, channel.event_string = channel.event_string, None
                    encoded_event_string += channel_event_string.encode() + self.delimiter
            if len(encoded_event_string) > 0:
                self.log.info(f"sending event: {encoded_event_string}")
                self.transport.write(encoded_event_string)
            reactor.callLater(EVENT_INTERVAL, self.send_event_string)
