import unittest
import pathlib

import pytest
from ddt import ddt, data
from newick import loads, dumps, Node, read, write, parse_node


@pytest.fixture
def node():
    return Node()


def test_empty_node(node):
    assert node.name is None
    assert node.length == 0.0


def test_empty_node_newick_representation(node):
    assert "" == node.newick


def test_empty_node_as_descendants_list(node):
    assert [] == node.descendants


@ddt
class TestNodeBasicFunctionality(unittest.TestCase):
    @data({"name": "test_name"},
          {"name": "test_name", "length": "3"})
    def test_node_with_parameters(self, test_set):
        if "length" in test_set:
            proper_length = 3.0
        else:
            proper_length = 0.0
        test_obj = Node(**test_set)
        self.assertEqual(test_set["name"], test_obj.name)
        self.assertEqual(proper_length, test_obj.length)

    def test_node_newick_representation_without_length(self):
        test_obj = Node(name="A")
        self.assertEqual("A", test_obj.newick)

    def test_node_newick_representation_with_length(self):
        test_obj = Node(name="A", length="3")
        self.assertEqual("A:3", test_obj.newick)

    def test_node_parameters_changeability(self):
        test_obj = Node(name="A")
        self.assertEqual("A", test_obj.name)
        test_obj.name = "B"
        self.assertEqual("B", test_obj.name)

    def test_node_length_changeability(self):
        test_obj = Node(length="10")
        self.assertEqual(10, test_obj.length)
        test_obj.length = "12"
        self.assertEqual(12, test_obj.length)


@ddt
class TestNodeDescendantsFunctionality(unittest.TestCase):
    def setUp(self):
        self.test_obj = Node("A", "1.0")
        self.test_descendant = Node("D", "2.0")
        self.lengths = ["2.0", "3.0", "4.0"]

    @data(["D1.1", "D1.2", "D1.3"], ["D", "", ""], ["", "", ""])
    def test_node_representation_with_deeper_descendants(self, test_data):
        """
        :param test_data: names of descendants

        Procedure:
        1. Make simple tree with one descendant having two another descendants inside
        2. Verify if it's newick representation is correct in comparision to parsed
        "proper_result"

        :return:
        """
        single_nodes_reprs = [
            "{0}:{1}".format(name, length)
            for name, length in zip(test_data, self.lengths)]
        proper_result = "(({1},{2}){0})A:1.0".format(*single_nodes_reprs)

        d1, d2, d3 = [Node(name, length) for name, length in zip(test_data, self.lengths)]
        d1.add_descendant(d2)
        d1.add_descendant(d3)
        self.test_obj.add_descendant(d1)
        self.assertEqual(proper_result, self.test_obj.newick)

    def test_node_as_descendants_list(self):
        self.test_obj.add_descendant(self.test_descendant)
        self.assertListEqual([self.test_descendant], self.test_obj.descendants)


def test_read_write(tmpdir):
    trees = read(pathlib.Path(__file__).parent / 'fixtures' / 'tree-glottolog-newick.txt')
    descs = [len(tree.descendants) for tree in trees]
    # The bookkeeping family has 391 languages
    assert descs[0] == 391
    tmp = str(tmpdir.join('test.txt'))
    write(trees, tmp)
    assert pathlib.Path(tmp).exists()
    assert [len(tree.descendants) for tree in read(tmp)] == descs


def test_Node():
    with pytest.raises(ValueError):
        Node(name='A)')

    root = loads('(A,B,(C,D)E)F;')[0]
    assert [n.name for n in root.walk()] == ['F', 'A', 'B', 'E', 'C', 'D']
    assert [n.name for n in root.walk() if n.is_leaf] == ['A', 'B', 'C', 'D']
    assert [n.name for n in root.walk(mode='postorder')] == ['A', 'B', 'C', 'D', 'E', 'F']
    assert root.ancestor is None
    assert root.descendants[0].ancestor == root
    root = loads('(((a,b),(c,d)),e);')[0]
    assert [n.ancestor.newick for n in root.walk() if n.ancestor] == \
        [
            '(((a,b),(c,d)),e)',
            '((a,b),(c,d))',
            '(a,b)',
            '(a,b)',
            '((a,b),(c,d))',
            '(c,d)',
            '(c,d)',
            '(((a,b),(c,d)),e)']


def test_repr():
    n = Node(name="A")
    assert repr(n) == 'Node("A")'


def test_Node_custom_length():
    root = Node.create(length='1e2', length_parser=lambda l: l + 'i')
    assert root.length == '1e2i'
    root = Node.create(length_formatter=lambda l: 5)
    root.length = 10
    assert root.length == pytest.approx(5)


def test_Node_ascii_art():
    assert loads('(A,(B,C)D)Ex;')[0].ascii_art(strict=True) == """\
     /-A
--Ex-|
     |    /-B
     \\-D--|
          \\-C"""

    assert loads('(A,(B,C)D)Ex;')[0].ascii_art(strict=True, show_internal=False) == """\
    /-A
----|
    |   /-B
    \\---|
        \\-C"""

    assert loads('(A,B,C)D;')[0].ascii_art(strict=True, show_internal=False) == """\
    /-A
----+-B
    \\-C"""


def test_Node_ascii_art_singleton():
    assert loads('((A,B)C)Ex;')[0].ascii_art(strict=True) == """\
          /-A
--Ex --C--|
          \\-B"""


def test_loads():
    """parse examples from https://en.wikipedia.org/wiki/Newick_format"""

    with pytest.raises(ValueError):
        loads('(),;')

    with pytest.raises(ValueError):
        loads(');')

    root = loads('(,,(,));')[0]
    assert root.name is None
    assert root.descendants[0].length == 0.0
    assert len(root.descendants) == 3

    root = loads('(A,B,(C,D));')[0]
    assert root.name is None
    assert len(root.descendants) == 3

    root = loads('(A,B,(C,D)E)Fäß;')[0]
    assert root.name == 'Fäß'
    assert len(root.descendants) == 3

    root = loads('(:0.1,:0.2,(:0.3,:0.4):0.5);')[0]
    assert root.name is None
    assert root.descendants[0].length == 0.1
    assert len(root.descendants) == 3

    root = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
    assert root.name == 'A'
    assert root.descendants[-1].length == 0.1
    assert len(root.descendants) == 1


def test_dumps(*trees):
    for ex in [
        '(,,(,));',
        '(A,B,(C,D));',
        '(A,B,(C,D)E)F;',
        '(:0.1,:0.2,(:0.3,:0.4):0.5);',
        '((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;',
    ]:
        assert ex == dumps(loads(ex)[0])


def test_clone():
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

    assert clone_node(tree1).newick == newick


def test_leaf_functions():
    tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
    leaf_names = set(tree.get_leaf_names())
    true_names = set(["B", "C", "D"])
    assert leaf_names == true_names


def test_prune():
    tree = loads('(A,((B,C),(D,E)))')[0]
    leaves = set(tree.get_leaf_names())
    prune_nodes = set(["A", "C", "E"])
    tree.prune_by_names(prune_nodes)
    assert set(tree.get_leaf_names()) == leaves - prune_nodes
    tree = loads('((A,B),((C,D),(E,F)))')[0]
    tree.prune_by_names(prune_nodes, inverse=True)
    assert set(tree.get_leaf_names()) == prune_nodes


def test_prune_single_node_tree():
    tree = loads('A')[0]
    tree.prune(tree.get_leaves())
    assert tree.newick == 'A'


def test_redundant_node_removal():
    tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
    assert len(tree.descendants) == 1
    tree.remove_redundant_nodes()
    assert not any([len(n.descendants) == 1 for n in tree.walk()])


def test_prune_and_node_removal():
    tree2 = loads("((A:1,B:1):1,C:1)")[0]
    tree2.prune_by_names(['A'])
    assert tree2.newick == '((B:1):1,C:1)'
    tree2.remove_redundant_nodes()
    assert tree2.newick == '(C:1,B:2.0)'


def test_stacked_redundant_node_removal():
    tree = loads("(((((A,B))),C))")[0]
    tree.remove_redundant_nodes(preserve_lengths=False)
    assert tree.newick == "(C,(A,B))"

    tree = loads("(((A,B):1):2)")[0]
    tree.remove_redundant_nodes()
    assert tree.newick == '(A,B):3.0'


def test_polytomy_resolution():
    tree = loads('(A,B,(C,D,(E,F)))')[0]
    assert not tree.is_binary
    tree.resolve_polytomies()
    assert tree.newick == '(A,((C,((E,F),D):0.0),B):0.0)'
    assert tree.is_binary

    tree = loads('(A,B,C,D,E,F)')[0]
    assert not tree.is_binary
    tree.resolve_polytomies()
    assert tree.newick == '(A,(F,(B,(E,(C,D):0.0):0.0):0.0):0.0)'
    assert tree.is_binary


def test_name_removal():
    tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
    tree.remove_names()
    assert dumps(tree) == '((:0.2,(:0.3,:0.4):0.5):0.1);'


def test_internal_name_removal():
    tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
    tree.remove_internal_names()
    assert dumps(tree) == '((B:0.2,(C:0.3,D:0.4):0.5):0.1);'


def test_leaf_name_removal():
    tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
    tree.remove_leaf_names()
    assert dumps(tree) == '((:0.2,(:0.3,:0.4)E:0.5)F:0.1)A;'


def test_length_removal():
    tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
    tree.remove_lengths()
    assert dumps(tree) == '((B,(C,D)E)F)A;'


def test_all_removal():
    tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
    tree.remove_names()
    tree.remove_lengths()
    topology_only = dumps(tree)
    assert topology_only == '((,(,)));'


def test_singletons():
    tree = loads('(((((A), B), (C, D))), E);')[0]
    assert len(list(tree.walk())) == 11
    tree.remove_redundant_nodes()
    assert len(list(tree.walk())) == 9


def test_comments():
    t = '[&R] (A,B)C [% ] [% ] [%  setBetweenBits = selected ];'
    with pytest.raises(ValueError):
        loads(t)
    tree = loads(t, strip_comments=True)[0]
    assert len(list(tree.walk())) == 3


def test_get_node():
    tree = loads('(A,B,(C,D)E)F;')[0]
    assert tree.get_node("A").name == 'A'
    assert len(tree.get_node('E').get_leaves()) == 2

    # rename
    tree.get_node('E').name = 'G'
    assert tree.newick == '(A,B,(C,D)G)F'


def test_prune_node():
    tree = '(A,(B,(C,D)E)F)G;'
    t1 = loads(tree)[0]
    t1.prune_by_names(["C", "D", "E"])
    t2 = loads(tree)[0]
    t2.prune_by_names(["E"])
    assert t1.newick == t2.newick
