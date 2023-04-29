import re

from twisted.protocols.basic import LineOnlyReceiver
from twisted.logger import Logger


class BaseDummyProtocol(LineOnlyReceiver):
    replies = {}
    non_delimited_replies = {}
    delimiter = b"\r"
    log_name = "don't use me directly"

    def __init__(self, *args, **kwargs):
        self.log = Logger(namespace=self.log_name)
        super().__init__(*args, **kwargs)

    def lineReceived(self, line):
        self.log.info(f"received: {line}")

        def get_match(data, dictionary):
            for key, value in dictionary.items():
                match = re.match(key, data)
                if match:
                    return match, value
            return None, None

        line = line.decode()
        send_function = self.sendLine
        match, reply = get_match(line, self.replies)
        if match is None and reply is None:
            match, reply = get_match(line, self.non_delimited_replies)
            send_function = self.transport.write
        if match is None and reply is None:
            return
        if not isinstance(reply, str):
            f, reply = reply
            reply = f(match) or reply
        try:
            send_function(reply.encode())
            self.log.info(f"answered: {reply}")
        except AttributeError:
            pass
