from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor
from twisted.logger import (textFileLogObserver, FilteringLogObserver, LogLevelFilterPredicate, LogLevel,
                            globalLogBeginner, Logger)
import sys
import importlib

log = Logger()
LOG_LEVEL = "info"
app_observer = textFileLogObserver(sys.stdout)
filter_predicate = LogLevelFilterPredicate(defaultLogLevel=LogLevel.levelWithName(LOG_LEVEL))

app_observer = FilteringLogObserver(app_observer, [filter_predicate])
globalLogBeginner.beginLoggingTo([app_observer])

if __name__ == "__main__":
    ports = {
        12344: "knauer_azura_vu_4_1",
        12345: "knauer_azura_vu_4_1",
        12346: "tdk_lambda_zplus",
        12347: "ismatec_reglo_icc",
        12348: "julabo_presto_a40",
        12349: "lambda_instruments_omnicoll",
        12350: "airvalve",
    }

    for port, device in ports.items():
        device_module = importlib.import_module(device)
        factory = ServerFactory.forProtocol(device_module.DeviceProtocol)
        reactor.listenTCP(port, factory)

    reactor.run()
