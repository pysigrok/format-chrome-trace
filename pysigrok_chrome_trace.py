"""PySigrok driver for chrome trace"""

__version__ = "0.0.1"

import io
from operator import itemgetter
import json

from sigrokdecode.output import Output


class ChromeTraceOutput(Output):
    name = "chrometrace"
    desc = "Chrome Trace Format json"

    def __init__(self, openfile, driver, logic_channels=[], analog_channels=[], decoders=[]):
        self.logic_waves = []
        self.last_bit = []
        self.openfile = openfile
        driver_signals = [driver.name]
        self.signals = [driver_signals]
        self.logic_channels = logic_channels

        self.annotation_pids = []
        self.annotation_tids = {}

        self.all_events = []
        self.all_events.append({
                    "pid": 0,
                    "tid": 0,
                    "name": "process_name",
                    "ph": "M",
                    "args": {"name": "Logic"}
                    })

    def output(self, source, startsample, endsample, data):
        ptype = data[0]
        if ptype == "logic":
            for bitpos, channel in enumerate(self.logic_channels):
                bit = 0 if (data[1] & (1 << bitpos)) == 0 else 1
                self.all_events.append({
                    "pid": 0,
                    "tid": bitpos,
                    "name": channel,
                    "ph": "C",
                    "ts": startsample,
                    "args": {"bit": bit}
                    })


        elif ptype == "analog":

            pass
        else:
            if source not in self.annotation_pids:
                self.annotation_tids[source] = {}
                self.annotation_pids.append(source)
                for i, row in enumerate(source.annotation_rows):
                    row_id, label, annotations = row
                    print(row_id, label, annotations)
                    for annotation in annotations:
                        self.annotation_tids[source][annotation] = i
                    self.all_events.append({
                                "pid": len(self.annotation_pids),
                                "tid": i,
                                "name": "thread_name",
                                "ph": "M",
                                "args": {"name": label}
                                })
                self.all_events.append({
                            "pid": len(self.annotation_pids),
                            "tid": 0,
                            "name": "process_name",
                            "ph": "M",
                            "args": {"name": source.name}
                            })

            self.all_events.append({
                "pid": self.annotation_pids.index(source) + 1,
                "tid": self.annotation_tids[source][ptype],
                "name": data[1][0],
                "ph": "X",
                "ts": startsample,
                "dur": endsample - startsample
                })

    def stop(self):
        json.dump(self.all_events, io.TextIOWrapper(self.openfile), indent=1)
