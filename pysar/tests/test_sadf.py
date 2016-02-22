import unittest
from unittest.mock import patch

from ddt import data, unpack, ddt as DDT

from pysar import sadf


SAMPLE_DISKIO_STATS = """
foohost;-1;2016-02-20 08:37:26 UTC;LINUX-RESTART	(4 CPU)
# hostname;interval;timestamp;DEV;tps;rd_sec/s;wr_sec/s;avgrq-sz;avgqu-sz;await;svctm;%util
foohost;600;2016-02-20 08:55:01 UTC;dev8-0;0.35;5.88;5.17;31.73;0.00;0.36;0.34;0.01
foohost;600;2016-02-20 08:55:01 UTC;dev8-16;0.28;2.59;4.56;25.37;0.00;4.19;4.14;0.12
foohost;600;2016-02-20 08:55:01 UTC;dev8-32;0.00;0.00;0.00;0.00;0.00;0.00;0.00;0.00
foohost;600;2016-02-20 09:05:01 UTC;dev8-0;0.06;1.79;0.64;38.32;0.00;0.42;0.32;0.00
""".strip().encode('ascii')


@DDT
class TestSADFWrapper(unittest.TestCase):

    @data(
        (['-d'], ['-dp'], 'datafile', 'sadf -d -- -dp datafile'),
        (['-h'], [], '-1', 'sadf -h -1'),
    )
    @unpack
    def test_popen_args(self, opts, saropts, target, cmd_string):
        """Check arg list represents a coherent command string.

        This test checks that the arg list can be joined and look like
        the command string supplied.
        """
        wrapper = sadf.SADFWrapper()
        args = wrapper.popen_args(opts, saropts, target)
        self.assertEqual(' '.join(args), cmd_string)

    @patch('pysar.sadf.SADFWrapper.popen_args')
    def test__run(self, mock_popen_args):
        """Check that run invokes Popen correctly.

        Run returns a generator for stdout; test mocks the popen_args
        method to invoke `echo hello world` and checks that generator
        returns this.
        """
        wrapper = sadf.SADFWrapper()
        mock_popen_args.return_value = ['echo', 'hello world']
        generator = wrapper._run(1, 2, 3)
        self.assertIn(b'hello world', list(generator)[0])

    # parse_line is a no-op in the base class, just returns the line.


@DDT
class TestDevIOReader(unittest.TestCase):
    """DevIOReader generators `sadf -d -- -d` records.

    DevIOReader parses 3 known types of records:

      - header rows
      - restart rows
      - iostats record
    """

    @data(*zip(
        SAMPLE_DISKIO_STATS.split(b'\n')[:4],
        (sadf.DevIORestartRecord, sadf.DevIOHeaderRecord,
         sadf.DevIORecord, sadf.DevIORecord)
    ))
    @unpack
    def test_record_factory(self, byte_string, expected_record_type):
        """Tests that lines are converted to the correct record type.

        Record factory is a static method that takes a byte string as
        input and returns the appropriate Record type (or raising an
        exception if it fails to identify the line).
        """
        # TODO: Check exception raising behaviour.
        record = sadf.DevIOReader.record_factory(byte_string)
        self.assertIsInstance(record, expected_record_type)

    @data(*zip(
        SAMPLE_DISKIO_STATS.split(b'\n')[:4],
        (None, None, sadf.DevIORecord, sadf.DevIORecord)
    ))
    @unpack
    def test_parse_line(self, byte_string, return_type):
        """Tests that lines are parsed correctly.

        Current implementation wraps record_factory and discards
        return values that are not DevIORecord (we don't care about
        headers or restart notifications at this point).
        """
        record = sadf.DevIOReader().parse_line(byte_string)
        if return_type is None:
            self.assertIs(record, None)
        else:
            self.assertIsInstance(record, return_type)

    @patch('pysar.sadf.SADFWrapper.__call__')
    def test___call__(self, mock_super_call):
        def test_generator():
            yield 1
            yield 2
            yield None
            yield 3

        mock_super_call.return_value = test_generator()
        reader = sadf.DevIOReader()
        generator = reader('/test/path')

        mock_super_call.assert_called_with('/test/path')
        self.assertEqual(list(generator), [1, 2, 3])


# DevIOHeaderRecord is essentially a "dummy" record.

@DDT
class TestDevIORestartRecord(unittest.TestCase):
    """Encapsulates kernel restart notifications in source data."""

    @data(*zip(SAMPLE_DISKIO_STATS.split(b'\n')[:3],
               (False, True, True)))
    @unpack
    def test_from_byte_string(self, byte_string, raise_exc):

        if raise_exc:
            self.assertRaises(
                sadf.RecordTypeError,
                sadf.DevIORestartRecord.from_byte_string,
                byte_string
            )
        else:
            r = sadf.DevIORestartRecord.from_byte_string(byte_string)
            self.assertEqual(r.timestamp, '2016-02-20 08:37:26 UTC')


@DDT
class TestDevIORecord(unittest.TestCase):
    """Encapsulates data, stripping redundant fields."""

    @data(*zip(SAMPLE_DISKIO_STATS.split(b'\n')[:4],
               (True, True, False, False)))
    @unpack
    def test_from_byte_string(self, byte_string, raise_exc):

        if raise_exc:
            self.assertRaises(
                sadf.RecordTypeError,
                sadf.DevIORecord.from_byte_string,
                byte_string
            )
        else:
            r = sadf.DevIORecord.from_byte_string(byte_string)
            self.assertEqual(r.timestamp, '2016-02-20 08:55:01 UTC')


if __name__ == '__main__':
    unittest.main()
