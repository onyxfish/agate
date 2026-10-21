import io
import os
import sys
import warnings
from unittest.mock import patch

from agate import Table
from agate.data_types import Boolean, Date, DateTime, Number, Text, TimeDelta
from agate.testcase import AgateTestCase
from agate.type_tester import TypeTester


class TestFromCSV(AgateTestCase):
    def setUp(self):
        self.rows = (
            (1, 'a', True, '11/4/2015', '11/4/2015 12:22 PM', '4:15'),
            (2, '👍', False, '11/5/2015', '11/4/2015 12:45 PM', '6:18'),
            (None, 'b', None, None, None, None)
        )

        self.column_names = [
            'number', 'text', 'boolean', 'date', 'datetime', 'timedelta'
        ]

        self.column_types = [
            Number(), Text(), Boolean(), Date(), DateTime(), TimeDelta()
        ]

    def test_from_csv(self):
        table1 = Table(self.rows, self.column_names, self.column_types)
        table2 = Table.from_csv('examples/test.csv')

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def test_from_csv_crlf(self):
        table1 = Table(self.rows, self.column_names, self.column_types)
        table2 = Table.from_csv('examples/test_crlf.csv')

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def test_from_csv_cr(self):
        table1 = Table(self.rows, self.column_names, self.column_types)
        table2 = Table.from_csv('examples/test_cr.csv')

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def test_from_csv_file_like_object(self):
        table1 = Table(self.rows, self.column_names, self.column_types)

        f = open('examples/test.csv', encoding='utf-8')

        table2 = Table.from_csv(f)
        f.close()

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def test_from_csv_type_tester(self):
        tester = TypeTester(force={
            'number': Text()
        })

        table = Table.from_csv('examples/test.csv', column_types=tester)

        self.assertColumnTypes(table, [Text, Text, Boolean, Date, DateTime, TimeDelta])

    def test_from_csv_no_type_tester(self):
        tester = TypeTester(limit=0)

        table = Table.from_csv('examples/test.csv', column_types=tester)

        self.assertColumnTypes(table, [Text, Text, Text, Text, Text, Text])

    def test_from_csv_no_header(self):
        warnings.simplefilter('ignore')

        try:
            table = Table.from_csv('examples/test_no_header.csv', header=False)
        finally:
            warnings.resetwarnings()

        self.assertColumnNames(table, ['a', 'b', 'c', 'd', 'e', 'f'])
        self.assertColumnTypes(table, [Number, Text, Boolean, Date, DateTime, TimeDelta])

    def test_from_csv_no_header_columns(self):
        table = Table.from_csv('examples/test_no_header.csv', self.column_names, header=False)

        self.assertColumnNames(table, self.column_names)
        self.assertColumnTypes(table, [Number, Text, Boolean, Date, DateTime, TimeDelta])

    def test_from_csv_sniff_limit_0(self):
        table2 = Table.from_csv('examples/test_csv_sniff.csv', sniff_limit=0)

        self.assertColumnNames(table2, ['number|text|boolean|date|datetime|timedelta'])
        self.assertColumnTypes(table2, [Text])

    def test_from_csv_sniff_limit_200(self):
        table1 = Table(self.rows, self.column_names, self.column_types)
        table2 = Table.from_csv('examples/test_csv_sniff.csv', sniff_limit=200)

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def test_from_csv_sniff_limit_none(self):
        table1 = Table(self.rows, self.column_names, self.column_types)
        table2 = Table.from_csv('examples/test_csv_sniff.csv', sniff_limit=None)

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def from_piped_stdin(self, data, newline=None, **kwargs):
        # Pass the data through a real pipe, which, like piped standard input, is not seekable.
        r, w = os.pipe()
        with open(w, 'wb') as f:
            f.write(data)
        with open(r, encoding='utf-8', newline=newline) as stdin, patch('sys.stdin', stdin):
            return Table.from_csv(sys.stdin, **kwargs)

    def test_from_csv_sniff_limit_stdin(self):
        table1 = Table(self.rows, self.column_names, self.column_types)
        with open('examples/test_csv_sniff.csv', 'rb') as f:
            table2 = self.from_piped_stdin(f.read(), sniff_limit=200)

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def test_from_csv_sniff_limit_stdin_skip_lines(self):
        table1 = Table(self.rows, self.column_names, self.column_types)
        with open('examples/test_csv_sniff.csv', 'rb') as f:
            table2 = self.from_piped_stdin(b'skipped line\n' + f.read(), skip_lines=1, sniff_limit=200)

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def test_from_csv_sniff_limit_stdin_skip_lines_untranslated_newlines(self):
        # Standard input that doesn't translate line endings, with \r line endings.
        table = self.from_piped_stdin(b'skipped line\ra;b\r1;2\r3;4\r', newline='', skip_lines=1, sniff_limit=1024)

        self.assertColumnNames(table, ['a', 'b'])
        self.assertRows(table, [(1, 2), (3, 4)])

    def test_from_csv_sniff_limit_stdin_skip_lines_row_limit(self):
        # More than a pipe holds, so use a buffered stream like sys.stdin. The sample ends partway through a row, and
        # standard input must be read no further than row_limit requires (e.g. csvlook --max-rows).
        data = b'skipped line\na;b\n' + b'3;4\n' * 100000
        stdin = io.TextIOWrapper(io.BufferedReader(io.BytesIO(data)), encoding='utf-8')
        with stdin, patch('sys.stdin', stdin):
            table = Table.from_csv(sys.stdin, skip_lines=1, sniff_limit=10, row_limit=3)

            self.assertNotEqual(sys.stdin.read(), '')

        self.assertColumnNames(table, ['a', 'b'])
        self.assertColumnTypes(table, [Number, Number])

        self.assertRows(table, [(3, 4)] * 3)

    def test_from_csv_skip_lines(self):
        warnings.simplefilter('ignore')

        try:
            table1 = Table(self.rows[1:], column_types=self.column_types)
            table2 = Table.from_csv('examples/test.csv', header=False, skip_lines=2)
        finally:
            warnings.resetwarnings()

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def test_from_csv_skip_lines_crlf(self):
        warnings.simplefilter('ignore')

        try:
            table1 = Table(self.rows[1:], column_types=self.column_types)
            table2 = Table.from_csv('examples/test_crlf.csv', header=False, skip_lines=2)
        finally:
            warnings.resetwarnings()

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def test_from_csv_skip_lines_cr(self):
        warnings.simplefilter('ignore')

        try:
            table1 = Table(self.rows[1:], column_types=self.column_types)
            table2 = Table.from_csv('examples/test_cr.csv', header=False, skip_lines=2)
        finally:
            warnings.resetwarnings()

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def test_from_csv_row_limit(self):
        table1 = Table(self.rows[:2], self.column_names, self.column_types)
        table2 = Table.from_csv('examples/test.csv', row_limit=2)

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def test_from_csv_row_limit_no_header_columns(self):
        table1 = Table(self.rows[:2], self.column_names, self.column_types)
        table2 = Table.from_csv('examples/test_no_header.csv', self.column_names, header=False, row_limit=2)

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def test_from_csv_row_limit_too_high(self):
        table1 = Table(self.rows, self.column_names, self.column_types)
        table2 = Table.from_csv('examples/test.csv', row_limit=200)

        self.assertColumnNames(table2, table1.column_names)
        self.assertColumnTypes(table2, [Number, Text, Boolean, Date, DateTime, TimeDelta])

        self.assertRows(table2, table1.rows)

    def test_from_csv_empty(self):
        table = Table.from_csv('examples/empty.csv')

        self.assertColumnNames(table, [])
        self.assertColumnTypes(table, [])

        self.assertRows(table, [])

    def test_from_csv_empty_input(self):
        import io

        table = Table.from_csv(io.StringIO(''))

        self.assertColumnNames(table, [])
        self.assertColumnTypes(table, [])
        self.assertRows(table, [])

    def test_from_csv_empty_input_with_column_names(self):
        import io

        table = Table.from_csv(io.StringIO(''), column_names=['a', 'b'])

        self.assertColumnNames(table, ['a', 'b'])
        self.assertRows(table, [])
