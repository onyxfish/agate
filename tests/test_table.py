#!/usr/bin/env python

try:
    from cdecimal import Decimal
except ImportError: #pragma: no cover
    from decimal import Decimal

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from journalism import Table
from journalism.columns import TextType, NumberType
from journalism.exceptions import ColumnDoesNotExistError, UnsupportedOperationError

class TestTable(unittest.TestCase):
    def setUp(self):
        self.rows = (
            (1, 4, 'a'),
            (2, 3, 'b'),
            (None, 2, 'c')
        )

        self.column_names = ('one', 'two', 'three')
        self.number_type = NumberType()
        self.text_type = TextType()
        self.column_types = (self.number_type, self.number_type, self.text_type)

    def test_create_table(self):
        table = Table(self.rows, self.column_types, self.column_names)

        self.assertEqual(len(table.rows), 3)

        self.assertSequenceEqual(table.rows[0], (1, 4, 'a'))
        self.assertSequenceEqual(table.rows[1], (2, 3, 'b'))
        self.assertSequenceEqual(table.rows[2], (None, 2, 'c'))

    def test_create_table_args(self):
        with self.assertRaises(ValueError):
            Table(self.rows, [self.number_type, self.number_type, self.text_type, self.text_type], self.column_names)

        with self.assertRaises(ValueError):
            Table(self.rows, self.column_types, ['one', 'two', 'three', 'four'])

        with self.assertRaises(ValueError):
            Table(self.rows, [self.number_type, self.number_type], ['one', 'two'])

    def test_create_duplicate_column_names(self):
        with self.assertRaises(ValueError):
            Table(self.rows, self.column_types, ['one', 'two', 'one'])

    def test_column_names_immutable(self):
        column_names = ['one', 'two', 'three']
        
        table = Table(self.rows, self.column_types, column_names)

        column_names[0] = 'five'

        self.assertEqual(table.get_column_names()[0], 'one')

    def test_get_column_types(self):
        table = Table(self.rows, self.column_types, self.column_names)

        self.assertEqual(table.get_column_types(), self.column_types)

    def test_get_column_names(self):
        table = Table(self.rows, self.column_types, self.column_names)

        self.assertSequenceEqual(table.get_column_names(), ('one', 'two', 'three'))

    def test_select(self):
        table = Table(self.rows, self.column_types, self.column_names)

        new_table = table.select(('three',))

        self.assertIsNot(new_table, table)
        
        self.assertEqual(len(new_table.rows), 3)
        self.assertSequenceEqual(new_table.rows[0], ('a',))
        self.assertSequenceEqual(new_table.rows[1], ('b',))
        self.assertSequenceEqual(new_table.rows[2], ('c',))
        
        self.assertEqual(len(new_table.columns), 1)
        self.assertSequenceEqual(new_table._column_types, (self.text_type,))
        self.assertSequenceEqual(new_table._column_names, ('three',))
        self.assertSequenceEqual(new_table.columns['three'], ('a', 'b', 'c'))

    def test_where(self):
        table = Table(self.rows, self.column_types, self.column_names)

        new_table = table.where(lambda r: r['one'] in (2, None))

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 2)
        self.assertSequenceEqual(new_table.rows[0], (2, 3, 'b'))
        self.assertSequenceEqual(new_table.columns['one'], (2, None))

    def test_find(self):
        table = Table(self.rows, self.column_types, self.column_names)

        row = table.find(lambda r: r['two'] - r['one'] == 1)

        self.assertIs(row, table.rows[1])

    def test_find_none(self):
        table = Table(self.rows, self.column_types, self.column_names)

        row = table.find(lambda r: r['one'] == 'FOO')

        self.assertIs(row, None)

    def test_stdev_outliers(self):
        rows = [ 
            (50, 4, 'a'),
        ] * 10
            
        rows.append((200, 1, 'b'))
        
        table = Table(rows, self.column_types, self.column_names)

        new_table = table.stdev_outliers('one')

        self.assertEqual(len(new_table.rows), 10)
        self.assertNotIn(200, new_table.columns['one'])

    def test_stdev_outliers_reject(self):
        rows = [ 
            (50, 4, 'a'),
        ] * 10
            
        rows.append((200, 1, 'b'))
        
        table = Table(rows, self.column_types, self.column_names)

        new_table = table.stdev_outliers('one', reject=True)

        self.assertEqual(len(new_table.rows), 1)
        self.assertSequenceEqual(new_table.columns['one'], (200,))

    def test_mad_outliers(self):
        rows = [ 
            (50, 4, 'a'),
        ] * 10
            
        rows.append((200, 1, 'b'))
        
        table = Table(rows, self.column_types, self.column_names)

        new_table = table.mad_outliers('one')

        self.assertEqual(len(new_table.rows), 10)
        self.assertNotIn(200, new_table.columns['one'])

    def test_mad_outliers_reject(self):
        rows = [ 
            (50, 4, 'a'),
        ] * 10
            
        rows.append((200, 1, 'b'))
        
        table = Table(rows, self.column_types, self.column_names)

        new_table = table.mad_outliers('one', reject=True)

        self.assertEqual(len(new_table.rows), 1)
        self.assertSequenceEqual(new_table.columns['one'], (200,))

    def test_pearson_correlation(self):
        rows = (
            (-1, 0, 'a'),
            (0, 0, 'b'),
            (1, 3, 'c')
        )

        table = Table(rows, self.column_types, self.column_names)

        self.assertEqual(table.pearson_correlation('one', 'one'), Decimal('1'))
        self.assertAlmostEqual(table.pearson_correlation('one', 'two'), Decimal('3').sqrt() * Decimal('0.5'))

    def test_pearson_correlation_zero(self):
        rows = (
            (-1, 3, 'a'),
            (0, 3, 'b'),
            (1, 3, 'c')
        )

        table = Table(rows, self.column_types, self.column_names)

        self.assertEqual(table.pearson_correlation('one', 'two'), Decimal('0'))

    def test_order_by(self):
        table = Table(self.rows, self.column_types, self.column_names)

        new_table = table.order_by('two')

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 3)
        self.assertSequenceEqual(new_table.rows[0], (None, 2, 'c'))
        self.assertSequenceEqual(new_table.rows[1], (2, 3, 'b'))
        self.assertSequenceEqual(new_table.rows[2], (1, 4, 'a'))

        # Verify old table not changed
        self.assertSequenceEqual(table.rows[0], (1, 4, 'a'))
        self.assertSequenceEqual(table.rows[1], (2, 3, 'b'))
        self.assertSequenceEqual(table.rows[2], (None, 2, 'c'))

    def test_order_by_func(self):
        rows = (
            (1, 2, 'a'),
            (2, 1, 'b'),
            (1, 1, 'c')
        )

        table = Table(rows, self.column_types, self.column_names)

        new_table = table.order_by(lambda r: (r['one'], r['two']))

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 3)
        self.assertSequenceEqual(new_table.rows[0], (1, 1, 'c'))
        self.assertSequenceEqual(new_table.rows[1], (1, 2, 'a'))
        self.assertSequenceEqual(new_table.rows[2], (2, 1, 'b'))

    def test_order_by_reverse(self):
        table = Table(self.rows, self.column_types, self.column_names)

        new_table = table.order_by(lambda r: r['two'], reverse=True)

        self.assertEqual(len(new_table.rows), 3)
        self.assertSequenceEqual(new_table.rows[0], (1, 4, 'a'))
        self.assertSequenceEqual(new_table.rows[1], (2, 3, 'b'))
        self.assertSequenceEqual(new_table.rows[2], (None, 2, 'c'))

    def test_order_by_nulls(self):
        rows = (
            (1, 2, None),
            (2, None, None),
            (1, 1, 'c'),
            (1, None, 'a')
        )

        table = Table(rows, self.column_types, self.column_names)

        new_table = table.order_by('two')

        self.assertSequenceEqual(new_table.columns['two'], (1, 2, None, None))

        new_table = table.order_by('three')

        self.assertSequenceEqual(new_table.columns['three'], ('a', 'c', None, None))

    def test_limit(self):
        table = Table(self.rows, self.column_types, self.column_names)

        new_table = table.limit(2)

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 2)
        self.assertSequenceEqual(new_table.rows[0], (1, 4, 'a'))
        self.assertSequenceEqual(new_table.columns['one'], (1, 2))

    def test_limit_slice(self):
        table = Table(self.rows, self.column_types, self.column_names)

        new_table = table.limit(0, 3, 2)

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 2)
        self.assertSequenceEqual(new_table.rows[0], (1, 4, 'a'))
        self.assertSequenceEqual(new_table.rows[1], (None, 2, 'c'))
        self.assertSequenceEqual(new_table.columns['one'], (1, None))

    def test_limit_slice_negative(self):
        table = Table(self.rows, self.column_types, self.column_names)

        new_table = table.limit(-2, step=-1)

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 2)
        self.assertSequenceEqual(new_table.rows[0], (2, 3, 'b'))
        self.assertSequenceEqual(new_table.rows[1], (1, 4, 'a'))
        self.assertSequenceEqual(new_table.columns['one'], (2, 1))

    def test_limit_step_only(self):
        table = Table(self.rows, self.column_types, self.column_names)

        new_table = table.limit(step=2)

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 2)
        self.assertSequenceEqual(new_table.rows[0], (1, 4, 'a'))
        self.assertSequenceEqual(new_table.rows[1], (None, 2, 'c'))
        self.assertSequenceEqual(new_table.columns['one'], (1, None))

    def test_distinct_column(self):
        rows = (
            (1, 2, 'a'),
            (2, None, None),
            (1, 1, 'c'),
            (1, None, None)
        )

        table = Table(rows, self.column_types, self.column_names)

        new_table = table.distinct('one')

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 2)
        self.assertSequenceEqual(new_table.rows[0], (1, 2, 'a'))
        self.assertSequenceEqual(new_table.rows[1], (2, None, None))
        self.assertSequenceEqual(new_table.columns['one'], (1, 2))

    def test_distinct_func(self):
        rows = (
            (1, 2, 'a'),
            (2, None, None),
            (1, 1, 'c'),
            (1, None, None)
        )

        table = Table(rows, self.column_types, self.column_names)

        new_table = table.distinct(lambda row: (row['two'], row['three']))

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 3)
        self.assertSequenceEqual(new_table.rows[0], (1, 2, 'a'))
        self.assertSequenceEqual(new_table.rows[1], (2, None, None))
        self.assertSequenceEqual(new_table.rows[2], (1, 1, 'c'))
        self.assertSequenceEqual(new_table.columns['one'], (1, 2, 1))

    def test_distinct_none(self):
        rows = (
            (1, 2, 'a'),
            (1, None, None),
            (1, 1, 'c'),
            (1, None, None)
        )

        table = Table(rows, self.column_types, self.column_names)

        new_table = table.distinct()

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 3)
        self.assertSequenceEqual(new_table.rows[0], (1, 2, 'a'))
        self.assertSequenceEqual(new_table.rows[1], (1, None, None))
        self.assertSequenceEqual(new_table.rows[2], (1, 1, 'c'))
        self.assertSequenceEqual(new_table.columns['one'], (1, 1, 1))

    def test_chain_select_where(self):
        table = Table(self.rows, self.column_types, self.column_names)

        new_table = table.select(('one', 'two')).where(lambda r: r['two'] == 3)

        self.assertEqual(len(new_table.rows), 1)
        self.assertSequenceEqual(new_table.rows[0], (2, 3))
        
        self.assertEqual(len(new_table.columns), 2)
        self.assertSequenceEqual(new_table._column_types, (self.number_type, self.number_type))
        self.assertEqual(new_table._column_names, ('one', 'two'))
        self.assertSequenceEqual(new_table.columns['one'], (2,))

class TestTableGrouping(unittest.TestCase):
    def setUp(self):
        self.rows = (
            ('a', 2, 3, 4),
            (None, 3, 5, None),
            ('a', 2, 4, None),
            ('b', 3, 4, None)
        )

        self.number_type = NumberType()
        self.text_type = TextType()
        self.column_types = (self.text_type, self.number_type, self.number_type, self.number_type)
        self.column_names = ('one', 'two', 'three', 'four')

    def test_group_by(self):
        table = Table(self.rows, self.column_types, self.column_names)

        new_tables = table.group_by('one')

        self.assertEqual(len(new_tables), 3)

        self.assertIn('a', new_tables.keys())
        self.assertIn('b', new_tables.keys())
        self.assertIn(None, new_tables.keys())

        self.assertSequenceEqual(new_tables['a'].columns['one'], ('a', 'a'))
        self.assertSequenceEqual(new_tables['b'].columns['one'], ('b',))
        self.assertSequenceEqual(new_tables[None].columns['one'], (None,))

    def test_group_by_bad_column(self):
        table = Table(self.rows, self.column_types, self.column_names)

        with self.assertRaises(ColumnDoesNotExistError):
            table.group_by('bad')

    def test_aggregate_sum(self):
        table = Table(self.rows, self.column_types, self.column_names)

        new_table = table.aggregate('one', (('two', 'sum'), ))

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 3)
        self.assertEqual(len(new_table.columns), 3)
        self.assertSequenceEqual(new_table._column_names, ('one', 'one_count', 'two_sum'))
        self.assertSequenceEqual(new_table.rows[0], ('a', 2, 4))
        self.assertSequenceEqual(new_table.rows[1], (None, 1, 3))
        self.assertSequenceEqual(new_table.rows[2], ('b', 1, 3))

    def test_aggregate_sum_two_columns(self):
        table = Table(self.rows, self.column_types, self.column_names)

        new_table = table.aggregate('one', (('two', 'sum'), ('four', 'sum')))

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 3)
        self.assertEqual(len(new_table.columns), 4)
        self.assertSequenceEqual(new_table._column_names, ('one', 'one_count', 'two_sum', 'four_sum'))
        self.assertSequenceEqual(new_table.rows[0], ('a', 2, 4, 4))
        self.assertSequenceEqual(new_table.rows[1], (None, 1, 3, 0))
        self.assertSequenceEqual(new_table.rows[2], ('b', 1, 3, 0))

    def test_aggregate_two_ops(self):
        table = Table(self.rows, self.column_types, self.column_names)

        new_table = table.aggregate('one', (('two', 'sum'), ('two', 'mean')))

        self.assertIsNot(new_table, table)
        self.assertEqual(len(new_table.rows), 3)
        self.assertEqual(len(new_table.columns), 4)
        self.assertSequenceEqual(new_table._column_names, ('one', 'one_count', 'two_sum', 'two_mean'))
        self.assertSequenceEqual(new_table.rows[0], ('a', 2, 4, 2))
        self.assertSequenceEqual(new_table.rows[1], (None, 1, 3, 3))
        self.assertSequenceEqual(new_table.rows[2], ('b', 1, 3, 3))

    def test_aggregate_sum_invalid(self):
        table = Table(self.rows, self.column_types, self.column_names)

        with self.assertRaises(UnsupportedOperationError):
            table.aggregate('two', (('one', 'sum'), ))

    def test_aggregeate_bad_column(self):
        table = Table(self.rows, self.column_types, self.column_names)

        with self.assertRaises(ColumnDoesNotExistError):
            table.aggregate('bad', (('one', 'sum'), ))

        with self.assertRaises(ColumnDoesNotExistError):
            table.aggregate('two', (('bad', 'sum'), ))

class TestTableCompute(unittest.TestCase):
    def setUp(self):
        self.rows = (
            ('a', 2, 3, 4),
            (None, 3, 5, None),
            ('a', 2, 4, None),
            ('b', 3, 4, None)
        )

        self.number_type = NumberType()
        self.text_type = TextType()
        self.column_types = (self.text_type, self.number_type, self.number_type, self.number_type)
        self.column_names = ('one', 'two', 'three', 'four')

        self.table = Table(self.rows, self.column_types, self.column_names)

    def test_compute(self):
        new_table = self.table.compute('test', self.number_type, lambda r: r['two'] + r['three'])

        self.assertIsNot(new_table, self.table)
        self.assertEqual(len(new_table.rows), 4) 
        self.assertEqual(len(new_table.columns), 5) 

        self.assertSequenceEqual(new_table.rows[0], ('a', 2, 3, 4, 5))
        self.assertSequenceEqual(new_table.columns['test'], (5, 8, 6, 7))

    def test_percent_change(self):
        new_table = self.table.percent_change('two', 'three', 'test')

        self.assertIsNot(new_table, self.table)
        self.assertEqual(len(new_table.rows), 4) 
        self.assertEqual(len(new_table.columns), 5) 

        to_one_place = lambda d: d.quantize(Decimal('0.1'))

        self.assertSequenceEqual(new_table.rows[0], ('a', Decimal('2'), Decimal('3'), Decimal('4'), Decimal('50.0')))
        self.assertEqual(to_one_place(new_table.columns['test'][0]), Decimal('50.0'))
        self.assertEqual(to_one_place(new_table.columns['test'][1]), Decimal('66.7'))
        self.assertEqual(to_one_place(new_table.columns['test'][2]), Decimal('100.0'))
        self.assertEqual(to_one_place(new_table.columns['test'][3]), Decimal('33.3'))

    def test_rank(self):
        new_table = self.table.rank(lambda r: r['two'], 'rank')

        self.assertEqual(len(new_table.rows), 4)
        self.assertEqual(len(new_table.columns), 5)

        self.assertSequenceEqual(new_table.rows[0], ('a', 2, 3, 4, 1))
        self.assertSequenceEqual(new_table.rows[1], (None, 3, 5, None, 3))
        self.assertSequenceEqual(new_table.rows[2], ('a', 2, 4, None, 1))
        self.assertSequenceEqual(new_table.rows[3], ('b', 3, 4, None, 3))

        self.assertSequenceEqual(new_table.columns['rank'], (1, 3, 1, 3))

    def test_rank2(self):
        new_table = self.table.rank(lambda r: r['one'], 'rank')

        self.assertEqual(len(new_table.rows), 4)
        self.assertEqual(len(new_table.columns), 5)

        self.assertSequenceEqual(new_table.rows[0], ('a', 2, 3, 4, 1))
        self.assertSequenceEqual(new_table.rows[1], (None, 3, 5, None, 4))
        self.assertSequenceEqual(new_table.rows[2], ('a', 2, 4, None, 1))
        self.assertSequenceEqual(new_table.rows[3], ('b', 3, 4, None, 3))

        self.assertSequenceEqual(new_table.columns['rank'], (1, 4, 1, 3))

    def test_rank_column_name(self):
        new_table = self.table.rank('two', 'rank')

        self.assertEqual(len(new_table.rows), 4)
        self.assertEqual(len(new_table.columns), 5)

        self.assertSequenceEqual(new_table.rows[0], ('a', 2, 3, 4, 1))
        self.assertSequenceEqual(new_table.rows[1], (None, 3, 5, None, 3))
        self.assertSequenceEqual(new_table.rows[2], ('a', 2, 4, None, 1))
        self.assertSequenceEqual(new_table.rows[3], ('b', 3, 4, None, 3))

        self.assertSequenceEqual(new_table.columns['rank'], (1, 3, 1, 3))

    def test_z_scores(self):
        new_table = self.table.z_scores('two','z-scores')

        self.assertEqual(len(new_table.rows), 4)
        self.assertEqual(len(new_table.columns), 5)

        self.assertSequenceEqual(new_table.rows[0], ('a', 2, 3, 4, -1))
        self.assertSequenceEqual(new_table.rows[1], (None, 3, 5, None, 1))
        self.assertSequenceEqual(new_table.rows[2], ('a', 2, 4, None, -1))
        self.assertSequenceEqual(new_table.rows[3], ('b', 3, 4, None, 1))

        self.assertSequenceEqual(new_table.columns['z-scores'],(-1,1,-1,1))



class TestTableJoin(unittest.TestCase):
    def setUp(self):
        self.left_rows = (
            (1, 4, 'a'),
            (2, 3, 'b'),
            (None, 2, 'c')
        )

        self.right_rows = (
            (1, 4, 'a'),
            (2, 3, 'b'),
            (None, 2, 'c')
        )

        self.number_type = NumberType()
        self.text_type = TextType()
        self.column_types = (self.number_type, self.number_type, self.text_type)

        self.left = Table(self.left_rows, self.column_types, ('one', 'two', 'three'))
        self.right = Table(self.right_rows, self.column_types, ('four', 'five', 'six'))

    def test_inner_join(self):
        new_table = self.left.inner_join('one', self.right, 'four')

        self.assertEqual(len(new_table.rows), 3)
        self.assertEqual(len(new_table.columns), 6)

        self.assertSequenceEqual(new_table.rows[0], (1, 4, 'a', 1, 4, 'a'))
        self.assertSequenceEqual(new_table.rows[1], (2, 3, 'b', 2, 3, 'b'))
        self.assertSequenceEqual(new_table.rows[2], (None, 2, 'c', None, 2, 'c'))

    def test_inner_join2(self):
        new_table = self.left.inner_join('one', self.right, 'five')

        self.assertEqual(len(new_table.rows), 1)
        self.assertEqual(len(new_table.columns), 6)

        self.assertSequenceEqual(new_table.rows[0], (2, 3, 'b', None, 2, 'c'))

    def test_inner_join_func(self):
        new_table = self.left.inner_join(
            lambda left: '%i%s' % (left['two'], left['three']),
            self.right,
            lambda right: '%i%s' % (right['five'], right['six'])
        )

        self.assertEqual(len(new_table.rows), 3)
        self.assertEqual(len(new_table.columns), 6)

    def test_left_outer_join(self):
        new_table = self.left.left_outer_join('one', self.right, 'four')

        self.assertEqual(len(new_table.rows), 3)
        self.assertEqual(len(new_table.columns), 6)

        self.assertSequenceEqual(new_table.rows[0], (1, 4, 'a', 1, 4, 'a'))
        self.assertSequenceEqual(new_table.rows[1], (2, 3, 'b', 2, 3, 'b'))
        self.assertSequenceEqual(new_table.rows[2], (None, 2, 'c', None, 2, 'c'))

    def test_left_outer_join2(self):
        new_table = self.left.left_outer_join('one', self.right, 'five')

        self.assertEqual(len(new_table.rows), 3)
        self.assertEqual(len(new_table.columns), 6)

        self.assertSequenceEqual(new_table.rows[0], (1, 4, 'a', None, None, None))
        self.assertSequenceEqual(new_table.rows[1], (2, 3, 'b', None, 2, 'c'))
        self.assertSequenceEqual(new_table.rows[2], (None, 2, 'c', None, None, None))

    def test_left_outer_func(self):
        new_table = self.left.left_outer_join(
            lambda left: '%i%s' % (left['two'], left['three']),
            self.right,
            lambda right: '%i%s' % (right['five'], right['six'])
        )

        self.assertEqual(len(new_table.rows), 3)
        self.assertEqual(len(new_table.columns), 6)

        self.assertSequenceEqual(new_table.rows[0], (1, 4, 'a', 1, 4, 'a'))
        self.assertSequenceEqual(new_table.rows[1], (2, 3, 'b', 2, 3, 'b'))
        self.assertSequenceEqual(new_table.rows[2], (None, 2, 'c', None, 2, 'c'))

class TestTableData(unittest.TestCase):
    def setUp(self):
        self.rows = ( 
            (1, 4, 'a'),
            (2, 3, 'b'),
            (None, 2, 'c')
        )

        self.number_type = NumberType()
        self.text_type = TextType()
        self.column_names = ['one', 'two', 'three']
        self.column_types = [self.number_type, self.number_type, self.text_type]

    def test_data_immutable(self):
        rows = [ 
            [1, 4, 'a'],
            [2, 3, 'b'],
            [None, 2, 'c']
        ]

        table = Table(rows, self.column_types, self.column_names)
        rows[0] = [2, 2, 2]
        self.assertSequenceEqual(table.rows[0], [1, 4, 'a'])

    def test_fork_preserves_data(self):
        table = Table(self.rows, self.column_types, self.column_names)
        table2 = table._fork(table.rows)

        self.assertIs(table.rows[0], table2._data[0])
        self.assertIs(table.rows[1], table2._data[1])
        self.assertIs(table.rows[2], table2._data[2])

        self.assertIs(table.rows[0], table2.rows[0])
        self.assertIs(table.rows[1], table2.rows[1])
        self.assertIs(table.rows[2], table2.rows[2])

    def test_where_preserves_rows(self):
        table = Table(self.rows, self.column_types, self.column_names)
        table2 = table.where(lambda r: r['one'] == 1)
        table3 = table2.where(lambda r: r['one'] == 1)

        self.assertIsNot(table._data[0], table2._data[0])
        self.assertIs(table2._data[0], table3._data[0])

    def test_order_by_preserves_rows(self):
        table = Table(self.rows, self.column_types, self.column_names)
        table2 = table.order_by(lambda r: r['one'])
        table3 = table2.order_by(lambda r: r['one'])

        self.assertIsNot(table._data[0], table2._data[0])
        self.assertIs(table2._data[0], table3._data[0])

    def test_limit_preserves_rows(self):
        table = Table(self.rows, self.column_types, self.column_names)
        table2 = table.limit(2)
        table3 = table2.limit(2)

        self.assertIsNot(table._data[0], table2._data[0])
        self.assertIs(table2._data[0], table3._data[0])

    def test_compute_creates_rows(self):
        table = Table(self.rows, self.column_types, self.column_names)
        table2 = table.compute('new2', self.number_type, lambda r: r['one'])
        table3 = table2.compute('new3', self.number_type, lambda r: r['one'])

        self.assertIsNot(table._data[0], table2._data[0])
        self.assertNotEqual(table._data[0], table2._data[0])
        self.assertIsNot(table2._data[0], table3._data[0])
        self.assertNotEqual(table2._data[0], table3._data[0])
        self.assertSequenceEqual(table._data[0], (1, 4, 'a'))

