import os
from glob import glob

from multicorn import ForeignDataWrapper

from pysar import sadf


class DevIOStats(ForeignDataWrapper):

    reader = sadf.DevIOReader()

    def __init__(self, options, columns):
        super().__init__(options, columns)

    def file_list(self):
        return sorted(glob('/var/log/sysstat/sa[0-3][0-9]'),
                      key=lambda f: os.stat(f).st_mtime)

    def execute(self, qual, columns):
        for f in self.file_list():
            for record in self.reader(f):
                # sadf.DevIORecord
                yield record._asdict()
