import re
import itertools
import functools
from subprocess import Popen, PIPE
from collections import namedtuple


class SADFWrapper(object):
    """Wrapper for the `sadf` system utility.

    This class is intended to be subclassed for specific sadf recipes.
    """

    def __init__(self, fmt='', saropts=''):
        # Define the command string head/tail, leaving the path /
        # offset to be defined on call.
        # Create the exec method pre-loaded with these components
        self.run = functools.partial(self._run, [fmt], [saropts])

    def __call__(self, target=None):
        """Invoke `sadf` for the file paths / offsets provided.

            target: string | int (<= 0)
                Path to saXX binary file, or relative offset (e.g. -1
                for yesterday).
        """

        # Integers are acceptable but need to be converted explicitly.
        # We trust they are valid (i.e. negative).
        target = str(target)
        return self.run(target)

    @staticmethod
    def popen_args(opts=[], saropts=[], target=None):
        """Return a list of Popen arguments."""
        if saropts: saropts = ['--'] + saropts
        if not target:
            target = '-0'
            # Default target -0 prevents an empty arg being passed to
            # Popen, causing a usage error. -0 is a valid equivalent
            # to leaving the target empty (e.g. `sadf`)
        return ['sadf'] + opts + saropts + [target]

    def _run(self, opts, saropts, target):
        # generator, construct the command line and call sadf
        args = self.popen_args(opts, saropts, target)
        process = Popen(args, stdout=PIPE)
        parse = self.parse_line
        for line in iter(process.stdout.readline, b''):
            yield parse(line)

    @staticmethod
    def parse_line(line):
        return line


class DevIOReader(SADFWrapper):
    """Device IO stats reader.

    Callable returns a generator yielding DevIORecord; reads and
    parses output of `sadf -d -- -d ...`.
    """

    def __init__(self):
        super().__init__('-d', '-dp')

    def __call__(self, target=None):
        """Invoke `sadf -- -dp` for the saXX/offset specified.

        Parses program output into, and returns, DevIORecords.

            target: string | int (<=0)
                Path to saXX binary file, or a relative offset (e.g.
                -1 for yesterday)
        """
        generator = super().__call__(target)
        return (retval for retval in generator if retval is not None)

    def parse_line(self, line):
        record = self.record_factory(line)
        if isinstance(record, DevIORecord):
            return record
        else:
            return None

    @staticmethod
    def record_factory(byte_string):
        """Returns the correct record type for a given byte string
        """
        try:
            return DevIORecord.from_byte_string(byte_string)

        except RecordTypeError as e:
            # This is one of the few lines that isn't valid IO data.
            # We might as well inspect the string in advance.
            try:
                if re.match(b'# host', byte_string):
                    parse = DevIOHeaderRecord
                elif re.match(b'^[^;]+;-1', byte_string):
                    parse = DevIORestartRecord.from_byte_string
                else:
                    raise e("Unrecognised source line.")
                return parse(byte_string)
            except RecordTypeError as e:
                raise e("Ambiguous source line.")


# --------------------------------------------------------------------
# Records
# --------------------------------------------------------------------
DevIOHeaderRecord = namedtuple('DevIOHeader', 'columns')


class DevIORestartRecord(namedtuple('Restart', ('hostname',
                                                'timestamp'))):
    __slots__ = ()

    @classmethod
    def from_byte_string(cls, byte_string):
        elements = byte_string.decode('ascii').split(';')
        if len(elements) != 4 or 'RESTART' not in elements[3]:
            raise RecordTypeError
        return cls(elements[0], elements[2])


class DevIORecord(namedtuple('DevIORecord', ('hostname',
                                             'timestamp',
                                             'dev',
                                             'tps',
                                             'read_freq',
                                             'write_freq',
                                             'avg_req_size',
                                             'avg_que_size',
                                             'await',
                                             'cpu_util'))):
    __slots__ = ()

    @classmethod
    def from_byte_string(cls, byte_string):
        fields = byte_string.decode('ascii').split(';')
        keys = fields[0:1] + fields[2:4]
        values = map(float, fields[4:11] + fields[12:])
        try:
            return cls(*itertools.chain(keys, values))
        except (TypeError, ValueError) as e:
            raise RecordTypeError
class RecordTypeError(Exception): pass


# --------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------
class RecordTypeError(Exception):
    """Flags a problem parsing a string into a specific record type"""
