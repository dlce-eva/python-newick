# coding: utf8
from __future__ import unicode_literals
from unittest import TestCase
import os
from tempfile import mktemp

from newick import loads, dumps, Node, read, write


class Tests(TestCase):
    def test_read_write(self):
        trees = read(os.path.join(
            os.path.dirname(__file__), 'fixtures', 'tree-glottolog-newick.txt'))
        descs = [len(tree.descendants) for tree in trees]
        # The bookkeeping family has 391 languages
        self.assertEqual(descs[0], 391)
        tmp = mktemp()
        write(trees, tmp)
        assert os.path.exists(tmp)
        self.assertEqual([len(tree.descendants) for tree in read(tmp)], descs)
        os.remove(tmp)

    def test_Node(self):
        with self.assertRaises(ValueError):
            Node(name='A)')

        root = loads('(A,B,(C,D)E)F;')[0]
        self.assertEqual(
            [n.name for n in root.walk()],
            ['F', 'A', 'B', 'E', 'C', 'D'])
        self.assertEqual(
            [n.name for n in root.walk() if n.is_leaf],
            ['A', 'B', 'C', 'D'])
        self.assertEqual(
            [n.name for n in root.walk(mode='postorder')],
            ['A', 'B', 'C', 'D', 'E', 'F'])

    def test_loads(self):
        """parse examples from https://en.wikipedia.org/wiki/Newick_format"""

        with self.assertRaises(ValueError):
            loads('(),;')

        with self.assertRaises(ValueError):
            loads(');')

        root = loads('(,,(,));')[0]
        self.assertIsNone(root.name)
        self.assertIsNone(root.descendants[0].length)
        self.assertEqual(len(root.descendants), 3)

        root = loads('(A,B,(C,D));')[0]
        self.assertIsNone(root.name)
        self.assertEqual(len(root.descendants), 3)

        root = loads('(A,B,(C,D)E)Fäß;')[0]
        self.assertEqual(root.name, 'Fäß')
        self.assertEqual(len(root.descendants), 3)

        root = loads('(:0.1,:0.2,(:0.3,:0.4):0.5);')[0]
        self.assertIsNone(root.name)
        self.assertEqual(root.descendants[0].length, '0.1')
        self.assertEqual(len(root.descendants), 3)

        root = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
        self.assertEqual(root.name, 'A')
        self.assertEqual(root.descendants[-1].length, '0.1')
        self.assertEqual(len(root.descendants), 1)

    def test_dumps(self, *trees):
        for ex in [
            '(,,(,));',
            '(A,B,(C,D));',
            '(A,B,(C,D)E)F;',
            '(:0.1,:0.2,(:0.3,:0.4):0.5);',
            '((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;',
        ]:
            self.assertEqual(ex, dumps(loads(ex)[0]))
