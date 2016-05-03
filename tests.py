# coding: utf8
from __future__ import unicode_literals
from unittest import TestCase
import os
from tempfile import mktemp

from newick import loads, dumps, Node, read, write, parse_node


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
        self.assertEqual(root.ancestor, None)
        self.assertEqual(root.descendants[0].ancestor, root)
        root = loads('(((a,b),(c,d)),e);')[0]
        self.assertEqual(
            [n.ancestor.newick for n in root.walk() if n.ancestor],
            [
                '(((a,b),(c,d)),e)',
                '((a,b),(c,d))',
                '(a,b)',
                '(a,b)',
                '((a,b),(c,d))',
                '(c,d)',
                '(c,d)',
                '(((a,b),(c,d)),e)'])

    def test_Node_custom_length(self):
        root = Node.create(length='1e2', length_parser=lambda l: l + 'i')
        self.assertEqual(root.length, '1e2i')
        root = Node.create(length_formatter=lambda l: 5)
        root.length = 10
        self.assertAlmostEqual(root.length, 5)

    def test_loads(self):
        """parse examples from https://en.wikipedia.org/wiki/Newick_format"""

        with self.assertRaises(ValueError):
            loads('(),;')

        with self.assertRaises(ValueError):
            loads(');')

        root = loads('(,,(,));')[0]
        self.assertIsNone(root.name)
        self.assertEqual(root.descendants[0].length, 0.0)
        self.assertEqual(len(root.descendants), 3)

        root = loads('(A,B,(C,D));')[0]
        self.assertIsNone(root.name)
        self.assertEqual(len(root.descendants), 3)

        root = loads('(A,B,(C,D)E)Fäß;')[0]
        self.assertEqual(root.name, 'Fäß')
        self.assertEqual(len(root.descendants), 3)

        root = loads('(:0.1,:0.2,(:0.3,:0.4):0.5);')[0]
        self.assertIsNone(root.name)
        self.assertEqual(root.descendants[0].length, 0.1)
        self.assertEqual(len(root.descendants), 3)

        root = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
        self.assertEqual(root.name, 'A')
        self.assertEqual(root.descendants[-1].length, 0.1)
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

    def test_clone(self):
        """
        This test illustrates how a tree can be assembled programmatically.
        """
        newick = '(A,B,(C,D)E)F'
        tree1 = parse_node(newick)

        def clone_node(n):
            c = Node(name=n.name)
            for nn in n.descendants:
                c.add_descendant(clone_node(nn))
            return c

        self.assertEqual(clone_node(tree1).newick, newick)

    def test_leaf_functions(self):
        tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
        leaf_names = set(tree.get_leaf_names())
        true_names = set(["B", "C", "D"])
        self.assertEqual(leaf_names, true_names)

    def test_prune(self):
        tree = loads('(A,((B,C),(D,E)))')[0]
        leaves = set(tree.get_leaf_names())
        prune_nodes = set(["A", "C", "E"])
        tree.prune_by_names(prune_nodes)
        self.assertEqual(set(tree.get_leaf_names()), leaves - prune_nodes)
        tree = loads('((A,B),((C,D),(E,F)))')[0]
        tree.prune_by_names(prune_nodes, inverse=True)
        self.assertEqual(set(tree.get_leaf_names()), prune_nodes)

    def test_prune_single_node_tree(self):
        tree = loads('A')[0]
        tree.prune(tree.get_leaves())
        self.assertEqual(tree.newick, 'A')

    def test_bad_prune(self):
        tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
        self.assertRaises(ValueError, tree.prune_by_names, ['E'])

    def test_redundant_node_removal(self):
        tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
        self.assertEqual(len(tree.descendants), 1)
        tree.remove_redundant_nodes()
        self.assertFalse(any([len(n.descendants) == 1 for n in tree.walk()]))

    def test_prune_and_node_removal(self):
        tree2 = loads("((A:1,B:1):1,C:1)")[0]
        tree2.prune_by_names(['A'])
        self.assertEqual(tree2.newick, '((B:1):1,C:1)')
        tree2.remove_redundant_nodes()
        self.assertEqual(tree2.newick, '(C:1,B:2.0)')

    def test_stacked_redundant_node_removal(self):
        tree = loads("(((((A,B))),C))")[0]
        tree.remove_redundant_nodes(preserve_lengths=False)
        self.assertEqual(tree.newick, "(C,(A,B))")

        tree = loads("(((A,B):1):2)")[0]
        tree.remove_redundant_nodes()
        self.assertEqual(tree.newick, '(A,B):3.0')

    def test_polytomy_resolution(self):
        tree = loads('(A,B,(C,D,(E,F)))')[0]
        self.assertFalse(tree.is_binary)
        tree.resolve_polytomies()
        self.assertEqual(tree.newick, '(A,((C,((E,F),D):0.0),B):0.0)')
        self.assertTrue(tree.is_binary)

        tree = loads('(A,B,C,D,E,F)')[0]
        self.assertFalse(tree.is_binary)
        tree.resolve_polytomies()
        self.assertEqual(tree.newick, '(A,(F,(B,(E,(C,D):0.0):0.0):0.0):0.0)')
        self.assertTrue(tree.is_binary)

    def test_name_removal(self):
        tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
        tree.remove_names()
        nameless = dumps(tree)
        self.assertEqual(nameless, '((:0.2,(:0.3,:0.4):0.5):0.1);')

    def test_internal_name_removal(self):
        tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
        tree.remove_internal_names()
        nameless = dumps(tree)
        self.assertEqual(nameless, '((B:0.2,(C:0.3,D:0.4):0.5):0.1);')

    def test_leaf_name_removal(self):
        tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
        tree.remove_leaf_names()
        nameless = dumps(tree)
        self.assertEqual(nameless, '((:0.2,(:0.3,:0.4)E:0.5)F:0.1)A;')

    def test_length_removal(self):
        tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
        tree.remove_lengths()
        nameless = dumps(tree)
        self.assertEqual(nameless, '((B,(C,D)E)F)A;')

    def test_all_removal(self):
        tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
        tree.remove_names()
        tree.remove_lengths()
        topology_only = dumps(tree)
        self.assertEqual(topology_only, '((,(,)));')

    def test_singletons(self):
        tree = loads('(((((A), B), (C, D))), E);')[0]
        self.assertEqual(len(list(tree.walk())), 11)
        tree.remove_redundant_nodes()
        self.assertEqual(len(list(tree.walk())), 9)

    def test_comments(self):
        t = '[&R] (A,B)C [% ] [% ] [%  setBetweenBits = selected ];'
        with self.assertRaises(ValueError):
            loads(t)
        tree = loads(t, strip_comments=True)[0]
        self.assertEqual(len(list(tree.walk())), 3)
