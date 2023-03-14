import pathlib

import pytest
from newick import loads, dumps, Node, read, write


@pytest.fixture
def fixture_dir():
   return pathlib.Path(__file__).parent / 'fixtures'


def test_empty_node():
    node = Node()
    assert node.name is None
    assert node.length == 0.0
    assert "" == node.newick
    assert [] == node.descendants


def test_Node_name():
    with pytest.raises(ValueError):
        Node("()")

    with pytest.raises(ValueError):
        Node(name='A)')

    n = Node()
    assert n.unquoted_name is None

    n = Node("a'b", auto_quote=True)
    assert n.name == "'a''b'"
    assert n.unquoted_name == "a'b"
    n.name = ":"
    assert n.name == "':'"
    n.name = 'A'
    assert n.name == n.unquoted_name
    assert repr(n) == 'Node("A")'
    assert Node("a b", auto_quote=True).name == "'a b'"


def test_Node_length():
    with pytest.raises(ValueError):
        Node(None, length=':')


def test_Node_comments():
    n = Node('A', comments=['first', 'second'])
    assert n.newick == "A[first|second]"

    n = Node('A', comment='first')
    n.comments.append('second')
    assert n.newick == "A[first|second]"


def test_node_newick_representation_without_length():
    test_obj = Node(name="A")
    assert test_obj.length == 0.0
    assert "A" == test_obj.newick


def test_node_newick_representation_with_length():
    test_obj = Node(name="A", length="3")
    assert pytest.approx(test_obj.length) == 3.0
    assert "A:3" == test_obj.newick


def test_node_parameters_changeability():
    test_obj = Node(name="A")
    assert "A" == test_obj.name
    test_obj.name = "B"
    assert "B" == test_obj.name


def test_node_length_changeability():
    test_obj = Node(length="10")
    assert 10 == test_obj.length
    test_obj.length = "12"
    assert 12 == test_obj.length


@pytest.mark.parametrize(
    'test_data',
    [["D1.1", "D1.2", "D1.3"], ["D", "", ""], ["", "", ""]]
)
def test_node_representation_with_deeper_descendants(test_data):
    """
    Procedure:
    1. Make simple tree with one descendant having two more descendants inside
    2. Verify if its newick representation is correct in comparison to parsed "proper_result"
    """
    single_nodes_reprs = [
        "{0}:{1}".format(name, length)
        for name, length in zip(test_data, ["2.0", "3.0", "4.0"])]
    proper_result = "(({1},{2}){0})A:1.0".format(*single_nodes_reprs)

    d1, d2, d3 = [Node(name, length) for name, length in zip(test_data, ["2.0", "3.0", "4.0"])]
    d1.add_descendant(d2)
    d1.add_descendant(d3)
    test_obj = Node("A", "1.0")
    test_obj.add_descendant(d1)
    assert proper_result == test_obj.newick


def test_node_as_descendants_list():
    test_obj = Node("A", "1.0")
    desc = Node("D", "2.0")
    test_obj.add_descendant(desc)
    assert [desc] == test_obj.descendants


@pytest.mark.slow
def test_read_write(tmp_path, fixture_dir):
    trees = read(fixture_dir / 'tree-glottolog-newick.txt')

    assert '[' in trees[0].descendants[0].name
    descs = [len(tree.descendants) for tree in trees]
    # The bookkeeping family has 391 languages
    assert descs[0] == 391
    tmp = tmp_path / 'test.txt'
    write(trees, tmp)
    assert tmp.exists()
    assert [len(tree.descendants) for tree in read(tmp)] == descs


def test_Node():
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


@pytest.mark.parametrize(
    's,assertion',
    [
        ("", lambda r: r == []),
        ("A", lambda r: r[0].name == 'A'),
        ("A;", lambda r: r[-1].name == 'A'),
        ("A-B.C;", lambda r: r[-1].name == 'A-B.C'),
        ("'A\\'C';", lambda r: r[-1].name == "'A\\'C'"),
        ("A  ;", lambda r: r[-1].name == 'A'),
        ("'A[noc]'", lambda r: r[0].name == "'A[noc]'"),
        ("'A(B'", lambda r: r[0].name == "'A(B'"),
        ("'A[noc'[c]", lambda r: r[0].comment == "c"),
        ("'A[noc]'[c(a)]", lambda r: r[0].comment == "c(a)"),
        (r"(A,B)'C ,\':''D':1.3;", lambda r: r[0].unquoted_name == "C ,':'D"),
        (
            '[&R] (A,B)C [% ] [% ] [%  setBetweenBits = selected ];',
            lambda r: r[0].name == 'C' and r[0].comment == '% '),
        (
            '[&R] (A,B)C [% ] [% ] [%  setBetweenBits = selected ];',
            lambda r: r[0].comments == ['% ', '% ', '%  setBetweenBits = selected ']),
        (
            "(A,B)C[&k1=v1]:[&k2=v2]2.0;",
            lambda r: r[0].comments == ['&k1=v1', '&k2=v2'] and r[0].length == 2.0),
        (
            "(A,B)C[&k1=v1]:[&k2=v2]2.0;",
            lambda r: r[0].properties == dict(k1='v1', k2='v2')),
        ("('A;B',C)D;", lambda r: len(r) == 1),
        ("('A:B':2,C:3)D:4;", lambda r: r[0].descendants[0].unquoted_name == 'A:B'),
        ("('A:B':2,C:3)D:4;", lambda r: pytest.approx(r[0].descendants[0].length) == 2.0),
        # parse examples from https://en.wikipedia.org/wiki/Newick_format
        ('(,,(,));', lambda r: r[0].name is None),
        ('(,,(,));', lambda r: r[0].descendants[0].length == 0.0),
        ('(,,(,));', lambda r: len(r[0].descendants) == 3),
        ('(A,B,(C,D));', lambda r: r[0].name is None),
        ('(A,B,(C,D));', lambda r: len(r[0].descendants) == 3),
        ('(A,B,(C,D)E)Fäß;', lambda r: r[0].name == 'Fäß'),
        ('(:0.1,:0.2,(:0.3,:0.4):0.5);', lambda r: r[0].descendants[0].length == 0.1),
        ('(:0.1,:0.2,(:0.3,:0.4):0.5);', lambda r: len(r[0].descendants) == 3),
        ('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;', lambda r: r[0].name == 'A'),
        ('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;', lambda r: r[0].descendants[-1].length == 0.1),
        ('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;', lambda r: r[0].name == 'A'),
        ('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;', lambda r: len(r[0].descendants) == 1),
        # http://marvin.cs.uidaho.edu/Teaching/CS515/newickFormat.html
        (
            "(ant:17, (bat:31, cow:22):7, dog:22, (elk:33, fox:12):40);",
            lambda r: set(r[0].get_leaf_names()) == {'ant', 'bat', 'cow', 'dog', 'elk', 'fox'}),
        (
            """\
(
    (raccoon:19.19959,bear:6.80041):0.84600,
    (
        (sea_lion:11.99700, seal:12.00300):7.52973,
        (
            (monkey:100.85930,cat:47.14069):20.59201, 
            weasel:18.87953
        ):2.09460
    ):3.87382,
    dog:25.46154
);""",
            lambda r: set(r[0].get_leaf_names()) ==
                      {'raccoon', 'bear', 'sea_lion', 'seal', 'monkey', 'cat', 'weasel', 'dog'}),
        # https://evolution.genetics.washington.edu/phylip/newicktree.html
        (
            "(,(,,),);",
            lambda r: len(r[0].get_leaves()) == 5),
        (
            "((a:3[&&NHX:name=a:support=100],b:2[&&NHX:name=b:support=100]):4[&&NHX:name=ab:support=60],c:5[&&NHX:name=c:support=100]);",
            lambda r: r[0].get_leaves()[0].properties['support'] == '100')
    ]
)
def test_quoting_and_comments(s, assertion):
    assert assertion(loads(s))


def test_comments():
    t = '[&R] (A,B)C [% ] [% ] [%  setBetweenBits = selected ];'
    tree = loads(t, strip_comments=True)[0]
    assert len(list(tree.walk())) == 3 and tree.comment is None


@pytest.mark.parametrize(
    's',
    [
        '((A)C;',
        "(A,B,C),D);",
        '((A)C;D)',
        '(),;',
        ');',
        '(A,B)C[abc',
        '(A,B)C[abc]]',
        "(A,B)'C",
        "(A B)C;"
        "('AB'G,D)C;"
    ]
)
def test_invalid(s):
    with pytest.raises(ValueError):
        loads(s)


def test_Node_custom_length():
    root = Node.create(length='1e2', length_parser=lambda l: l + 'i')
    assert root.length == '1e2i'
    root = Node.create(length_formatter=lambda l: 5)
    root.length = 10
    assert root.length == pytest.approx(5)

    root = Node.create(length=100., length_formatter="{:0.1e}".format)
    assert root.newick == ':1.0e+02'

    weird_numbers_tree = "((a:1.e2,b:3j),(c:0x0BEFD6B0,d:003))"
    root = loads(weird_numbers_tree, length_parser=None)[0]
    assert weird_numbers_tree == root.newick


def test_rename():
    n = loads("('a 1',b)c;")[0]
    with pytest.raises(ValueError):
        n.rename(**{'a 1': 'x y'})
    assert n.rename(**{'a 1': "'x y'", 'c': 'z'}).newick == "('x y',b)z"
    assert n.rename(auto_quote=True, **{'x y': "a b"}).newick == "('a b',b)z"


def test_strip_comments():
    n = loads("(a[c1]:2.0,b:[c2]1.0)c;")[0]
    assert '[c1]' in n.newick and ('[c2]' in n.newick)
    n.strip_comments()
    assert n.newick == '(a:2.0,b:1.0)c'


@pytest.mark.parametrize(
    'nwk,kw,art',
    [
        ("(A,(B,C)D)Ex;",
         {},
         """\
     /-A
--Ex-|
     |    /-B
     \\-D--|
          \\-C"""),
        ("(A,(B,C)D)Ex;",
         dict(show_internal=False),
         """\
    /-A
----|
    |   /-B
    \\---|
        \\-C"""),
        ("(A,B,C)D;",
         dict(show_internal=False),
         """\
    /-A
----+-B
    \\-C"""),
        ("((A,B)C)Ex;",
         {},
         """\
          /-A
--Ex --C--|
          \\-B"""),
        ("(,(,,),);",
         {},
         "   /-\n   |  /-\n---+--+-\n   |  \\-\n   \\-"),
        ("(((((A),B),(C,D))),E);",
         {'strict': False},
         """\
                ┌── ──A
            ┌───┤
            │   └─B
    ┌── ────┤
    │       │   ┌─C
────┤       └───┤
    │           └─D
    └─E""")
    ]
)
def test_Node_ascii_art(nwk, kw, art):
    kw.setdefault('strict', True)
    assert loads(nwk)[0].ascii_art(**kw) == art


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
    tree1 = loads(newick)[0]

    def clone_node(n):
        c = Node(name=n.name)
        for nn in n.descendants:
            c.add_descendant(clone_node(nn))
        return c

    assert clone_node(tree1).newick == newick


def test_leaf_functions():
    tree = loads('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;')[0]
    assert set(tree.get_leaf_names()) == {"B", "C", "D"}


@pytest.mark.parametrize(
    'tree,nodes,inverse, result',
    [
        ('(A,((B,C),(D,E)))', 'A C E', False, '(B,D)'),
        ('((A,B),((C,D),(E,F)))', 'A C E', True, '((C,E),A)'),
        ('(b,(c,(d,(e,(f,g))h)i)a)', 'b c i', True, '(b,(c,i)a)'),
        ('(b,(c,(d,(e,(f,g))h)i)a)', 'b c i', False, ''),
        ('(b,(c,(d,(e,(f,g))h)i)a)', 'c i', False, '(b,a)'),
    ]
)
def test_prune(tree, nodes, inverse, result):
    tree = loads(tree)[0]
    tree.prune_by_names(nodes.split(), inverse=inverse)
    tree.remove_redundant_nodes(preserve_lengths=False)
    assert tree.newick == result


def test_prune_single_node_tree():
    tree = loads('A')[0]
    tree.prune(tree.get_leaves())
    assert tree.newick == 'A'


@pytest.mark.parametrize(
    'newick,kw,result',
    [
        ('((B:0.2,(C:0.3,D:0.4)E:0.5)F:0.1)A;', dict(), '(B:0.2,(C:0.3,D:0.4)E:0.5)A:0.1'),
        ('((C)B)A', dict(preserve_lengths=False), 'A'),
        ('((C)B)A', dict(preserve_lengths=False, keep_leaf_name=True), 'C'),
        (
            '((aiw),((aas,(kbt)),((abg),abf)))',
            dict(preserve_lengths=False, keep_leaf_name=True),
            '(((aas,kbt),(abf,abg)),aiw)'),
    ]
)
def test_redundant_node_removal(newick, kw, result):
    tree = loads(newick)[0]
    tree.remove_redundant_nodes(**kw)
    assert tree.newick == result


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


def test_with_comments():
    nwk = "(1[x&dmv={1},dmv1=0.260,dmv1_95%_hpd={0.003,0.625},dmv1_median=0.216,dmv1_range=" \
          "{0.001,1.336},height=1.310e-15,height_95%_hpd={0.0,3.552e-15},height_median=0.0," \
          "height_range={0.0,7.105e-15},length=2.188,length_95%_hpd={1.725,2.634}," \
          "length_median=2.182,length_range={1.307,3.236}]:1.14538397925438," \
          "2[&dmv={1},dmv1=0.260,dmv1_95%_hpd={0.003,0.625},dmv1_median=0.216,dmv1_range=" \
          "{0.001,1.336},height=1.310e-15,height_95%_hpd={0.0,3.552e-15},height_median=0.0," \
          "height_range={0.0,7.105e-15},length=2.188,length_95%_hpd={1.725,2.634}," \
          "length_median=2.182,length_range={1.307,3.236}]:1.14538397925438)[y&dmv={1}," \
          "dmv1=0.260,dmv1_95%_hpd={0.003,0.625},dmv1_median=0.216,dmv1_range={0.001,1.336}," \
          "height=1.310e-15,height_95%_hpd={0.0,3.552e-15},height_median=0.0," \
          "height_range={0.0,7.105e-15},length=2.188,length_95%_hpd={1.725,2.634}," \
          "length_median=2.182,length_range={1.307,3.236}]"
    tree = loads(nwk)[0]
    assert tree.comment.startswith('y')
    assert tree.descendants[0].name == '1'
    assert tree.descendants[0].comment[:47] == 'x&dmv={1},dmv1=0.260,dmv1_95%_hpd={0.003,0.625}'
    assert tree.newick == nwk


def test_with_comments_beast():
    nwk = "((((20:[&rate=9.363171791537587E-5]1320.9341043566992,(21:[&rate=9.363171791537587E-5]" \
          "1225.8822690335624,(((((15:[&rate=9.363171791537587E-5]638.1949811891477,16:[&rate=" \
          "9.363171791537587E-5]638.1949811891477):[&rate=9.363171791537587E-5]257.76795318129564" \
          ",8:[&rate=9.363171791537587E-5]895.9629343704433):[&rate=9.363171791537587E-5]" \
          "41.795862802882425,12:[&rate=9.363171791537587E-5]937.7587971733258):" \
          "[&rate=9.363171791537587E-5]95.6952785114238,14:[&rate=9.363171791537587E-5]" \
          "1033.4540756847496):[&rate=9.363171791537587E-5]59.28887326566064,((25:" \
          "[&rate=9.363171791537587E-5]368.1724945784702,28:[&rate=9.363171791537587E-" \
          "5]368.1724945784702):[&rate=9.363171791537587E-5]618.1292632448451,(13:[&rate=" \
          "9.363171791537587E-5]894.6169275367406,((22:[&rate=9.363171791537587E-5]532." \
          "4463352965287,33:[&rate=9.363171791537587E-5]532.4463352965287):[&rate=9." \
          "363171791537587E-5]124.75991679524702,19:[&rate=9.363171791537587E-5]657." \
          "2062520917757):[&rate=9.363171791537587E-5]237.4106754449649):[&rate=9." \
          "363171791537587E-5]91.68483028657465):[&rate=9.363171791537587E-5]106.44119112709495):" \
          "[&rate=9.363171791537587E-5]133.13932008315214):[&rate=9.363171791537587E-5]95." \
          "05183532313686):[&rate=9.363171791537587E-5]239.53051384576952,((23:[&rate=9." \
          "363171791537587E-5]886.6590941437129,2:[&rate=9.363171791537587E-5]886.6590941437129):" \
          "[&rate=9.363171791537587E-5]318.065540579532,((6:[&rate=9.363171791537587E-5]1128." \
          "8289029154403,37:[&rate=9.363171791537587E-5]1128.8289029154403):[&rate=9." \
          "363171791537587E-5]17.349382774569676,((((((3:[&rate=9.363171791537587E-5]459." \
          "5487115479798,36:[&rate=9.363171791537587E-5]459.5487115479798):[&rate=9." \
          "363171791537587E-5]306.57918484718175,(31:[&rate=9.363171791537587E-5]485." \
          "4575256190764,34:[&rate=9.363171791537587E-5]485.4575256190764):[&rate=9." \
          "363171791537587E-5]280.6703707760851):[&rate=9.363171791537587E-5]15.246829791795335," \
          "(30:[&rate=9.363171791537587E-5]543.1657161064542,1:[&rate=9.363171791537587E-5]543." \
          "1657161064542):[&rate=9.363171791537587E-5]238.2090100805027):[&rate=9." \
          "363171791537587E-5]118.69392508203657,((7:[&rate=9.363171791537587E-5]520." \
          "3998734304117,35:[&rate=9.363171791537587E-5]520.3998734304117):[&rate=9." \
          "363171791537587E-5]238.7668559806733,(32:[&rate=9.363171791537587E-5]720." \
          "2892667226898,17:[&rate=9.363171791537587E-5]720.2892667226898):[&rate=9." \
          "363171791537587E-5]38.87746268839521):[&rate=9.363171791537587E-5]140.9019218579084)" \
          ":[&rate=9.363171791537587E-5]52.21797041264119,26:[&rate=9.363171791537587E-5]" \
          "952.2866216816346):[&rate=9.363171791537587E-5]163.25701515522496,((18:[&rate=9." \
          "363171791537587E-5]720.6233628054213,10:[&rate=9.363171791537587E-5]720.6233628054213):"\
          "[&rate=9.363171791537587E-5]119.64362661776931,(29:[&rate=9.363171791537587E-5]617." \
          "5158316030422,(9:[&rate=9.363171791537587E-5]593.9192324440043,(11:[&rate=9." \
          "363171791537587E-5]472.3642192781455,27:[&rate=9.363171791537587E-5]472.3642192781455)" \
          ":[&rate=9.363171791537587E-5]121.55501316585872):[&rate=9.363171791537587E-5]23." \
          "596599159037964):[&rate=9.363171791537587E-5]222.75115782014836):[&rate=9." \
          "363171791537587E-5]275.276647413669):[&rate=9.363171791537587E-5]30.63464885315034):" \
          "[&rate=9.363171791537587E-5]58.54634903323495):[&rate=9.363171791537587E-5]355." \
          "73998347922384):[&rate=9.363171791537587E-5]1186.6682306101936,24:[&rate=9." \
          "363171791537587E-5]2747.1328488126624):[&rate=9.363171791537587E-5]301.4581721015056," \
          "(38:[&rate=9.363171791537587E-5]963.0459960655501,(5:[&rate=9.363171791537587E-5]500." \
          "66376645282014,4:[&rate=9.363171791537587E-5]500.66376645282014):[&rate=9." \
          "363171791537587E-5]462.38222961272993):[&rate=9.363171791537587E-5]2085.5450248486177)"
    tree = loads(nwk)[0]
    assert tree.descendants[0].comment == '&rate=9.363171791537587E-5'
    assert tree.descendants[0].name is None
    assert tree.descendants[0].length == pytest.approx(301.4581721015056)
    assert tree.newick == nwk


def test_roundtrip_two_comments():
    nwk = "((1[&height=9.687616008832612E-12,height_95%_HPD={0.0,2.9103830456733704E-11}," \
          "height_median=0.0,height_range={0.0,3.725290298461914E-9},length=107922.03600478375," \
          "length_95%_HPD={474.13147831140884,255028.5553480226},length_median=16766.239568341443," \
          "length_range={474.13147831140884,3.1088350108564742E7}]:[&rate=0.10061354528306601]" \
          "14581.043598225671,(7[&height=9.309604621069004E-12,height_95%_HPD=" \
          "{0.0,2.9103830456733704E-11},height_median=0.0,height_range={0.0,3.725290298461914E-9}," \
          "length=65008.773722909886,length_95%_HPD={232.35151363136288,185443.9546690862}," \
          "length_median=11647.615898062268,length_range={232.35151363136288,1.150899255812396E7}]:" \
          "[&rate=0.14084529313827582]10185.506184914375,(9[&height=9.127260087722948E-12," \
          "height_95%_HPD={0.0,2.9103830456733704E-11},height_median=0.0," \
          "height_range={0.0,3.725290298461914E-9},length=25379.761049583933,length_95%_HPD=" \
          "{56.592660460186835,58976.07308471651},length_median=3942.1518558536773,length_range=" \
          "{56.592660460186835,6951356.4983186275}]:[&rate=0.22402647395508335]3942.1518558536773,12" \
          "[&height=9.127260087722948E-12,height_95%_HPD={0.0,2.9103830456733704E-11},height_median=" \
          "0.0,height_range={0.0,3.725290298461914E-9},length=25379.761049583933,length_95%_HPD=" \
          "{56.592660460186835,58976.07308471651},length_median=3942.1518558536773,length_range=" \
          "{56.592660460186835,6951356.4983186275}]:[&rate=0.22402647395508335]3942.1518558536773)" \
          "[&height=25379.76104958394,height_95%_HPD={56.59266046018695,58976.07308471651}," \
          "height_median=3942.1518558536773,height_range={56.59266046018695,6951356.498318631}," \
          "length=38091.50530423341,length_95%_HPD={46.39747042888712,111881.67133971374}," \
          "length_median=6404.173915508887,length_range={46.39747042888712,5175584.190381359}," \
          "posterior=1.0]:[&rate=0.1764340946476647]6243.354329060698)[&height=63964.7133354256," \
          "height_95%_HPD={232.35151363136288,174173.2306986642},height_median=10185.506184914375," \
          "height_range={232.35151363136288,1.150899255812396E7},length=35902.53304149997," \
          "length_95%_HPD={14.560332318756082,95384.63040570999},length_median=4975.027852972411," \
          "length_range={14.560332318756082,7445332.392798465},posterior=0.8589521397147047]:" \
          "[&rate=0.07923911606477686]4395.537413311296)[&height=80767.98182026888,height_95%_HPD=" \
          "{529.6147479238796,233688.59740367957},height_median=14581.043598225671,height_range=" \
          "{529.6147479238796,1.4524763136448236E7},length=31190.19922532072,length_95%_HPD=" \
          "{3.6537288492327207,79714.48294750144},length_median=4454.437543634325,length_range=" \
          "{3.6537288492327207,1.1428212448711276E7},posterior=0.5345953872816958]:[&rate=" \
          "0.15749022880313052]9820.657628578989,(((2[&height=7.737585890856534E-12,height_95%_HPD=" \
          "{0.0,2.9103830456733704E-11},height_median=0.0,height_range={0.0,3.725290298461914E-9}," \
          "length=45609.46047931727,length_95%_HPD={206.83939466644824,123542.2654486959}," \
          "length_median=8434.012912102502,length_range={206.83939466644824,1.6023311824151885E7}]:" \
          "[&rate=0.3421656699625563]8434.18109992326,(3[&height=9.379050440351825E-12," \
          "height_95%_HPD={0.0,2.9103830456733704E-11},height_median=0.0,height_range=" \
          "{0.0,3.725290298461914E-9},length=29034.80730007669,length_95%_HPD={173.60894978441502," \
          "80127.43307802954},length_median=5408.332869562197,length_range={173.60894978441502," \
          "7565197.594627727}]:[&rate=0.40878488857536766]5408.332869562197,(((4[&height=" \
          "9.533674239636711E-12,height_95%_HPD={0.0,2.9103830456733704E-11},height_median=0.0," \
          "height_range={0.0,3.725290298461914E-9},length=12414.863740264116,length_95%_HPD=" \
          "{66.08153995214036,31146.118985240348},length_median=2052.7139045146614,length_range=" \
          "{66.08153995214036,4162747.7669137157}]:[&rate=0.40878488857536766]2052.713904514665," \
          "(8[&height=8.76596601525156E-12,height_95%_HPD={0.0,2.9103830456733704E-11},height_median=" \
          "0.0,height_range={0.0,3.725290298461914E-9},length=7495.104386864869,length_95%_HPD=" \
          "{33.229724377705,18284.937529115006},length_median=1238.5410223305225,length_range=" \
          "{33.229724377705,2652538.9755849764}]:[&rate=1.1616489920397255]1238.5410223305262,10" \
          "[&height=8.76596601525156E-12,height_95%_HPD={0.0,2.9103830456733704E-11},height_median=" \
          "0.0,height_range={0.0,3.725290298461914E-9},length=7495.104386864869,length_95%_HPD={" \
          "33.229724377705,18284.937529115006},length_median=1238.5410223305225,length_range={" \
          "33.229724377705,2652538.9755849764}]:[&rate=0.6807065555747316]1238.5410223305262)[" \
          "&height=7495.104386864877,height_95%_HPD={33.229724377705,18284.937529115006}," \
          "height_median=1238.5410223305262,height_range={33.229724377705,2652538.97558498}," \
          "length=4919.759353399242,length_95%_HPD={11.135741831899963,13615.173191136855}," \
          "length_median=727.9975598861292,length_range={11.135741831899963,1806011.4114757068}," \
          "posterior=1.0]:[&rate=0.6807065555747316]814.1728821841389)[&height=12414.863740264125," \
          "height_95%_HPD={66.08153995214036,31146.118985240348},height_median=2052.713904514665," \
          "height_range={66.08153995214036,4162747.7669137195},length=4494.749985367252," \
          "length_95%_HPD={7.997119765025445,13544.827830110327},length_median=743.8499422922905," \
          "length_range={7.997119765025445,1079092.8689759858},posterior=1.0]:[&rate=1.1616489920397255" \
          "]556.5552100585955,11[&height=8.828667314765534E-12,height_95%_HPD={" \
          "0.0,2.9103830456733704E-11},height_median=0.0,height_range={0.0,3.725290298461914E-9}," \
          "length=14628.206134120901,length_95%_HPD={94.62325431555337,39330.92845327759}," \
          "length_median=2698.76238812456,length_range={84.29227912953411,3969567.691730257}]:" \
          "[&rate=1.1616489920397255]2609.2691145732606)[&height=11972.847735373902,height_95%_HPD=" \
          "{84.29227912953411,37091.0728580773},height_median=2609.2691145732606,height_range=" \
          "{84.29227912953411,1575701.7833227757},length=2532.3352144701103,length_95%_HPD={" \
          "0.004421725508564123,7620.200479995983},length_median=483.3085065544801,length_range={" \
          "0.004421725508564123,488670.1513605751},posterior=0.674310091987735]:[&rate=" \
          "0.14084529313827582]843.471284182473,13[&height=9.62737001763898E-12,height_95%_HPD={" \
          "0.0,2.9103830456733704E-11},height_median=0.0,height_range={0.0,3.725290298461914E-9}," \
          "length=16098.152887077857,length_95%_HPD={101.12152367712349,43253.00278986094}," \
          "length_median=3021.1956203544178,length_range={87.52788789503245,3969567.691730257}]:" \
          "[&rate=0.015281431734503132]3452.7403987557336)[&height=18854.825355500612,height_95%_HPD=" \
          "{117.06952824319609,50863.21772980399},height_median=3452.7403987557336,height_range=" \
          "{117.06952824319609,5241840.635889705},length=10179.981944576117,length_95%_HPD=" \
          "{21.621494899670324,27419.87806782825},length_median=1701.737850154088,length_range=" \
          "{21.621494899670324,2891063.76993455},posterior=1.0]:[&rate=0.22402647395508335]" \
          "1955.592470806463)[&height=29034.807300076696,height_95%_HPD={173.60894978441502," \
          "80127.4330780296},height_median=5408.332869562197,height_range={173.60894978441502," \
          "7565197.594627731},length=16575.3792990243,length_95%_HPD={33.23044488203345,42503.93157259235}," \
          "length_median=2600.4791495973714,length_range={33.23044488203345,9106986.442180987}," \
          "posterior=1.0]:[&rate=0.40878488857536766]3025.8482303610635)[&height=45684.27028379785," \
          "height_95%_HPD={206.83939466644847,123833.12145059655},height_median=8434.18109992326," \
          "height_range={206.83939466644847,1.6023311824151888E7},length=18834.009102754226," \
          "length_95%_HPD={12.551497256452194,44713.49388946092},length_median=2723.4761572134503," \
          "length_range={12.551497256452194,8370840.365275718},posterior=0.9980002666311159]:[" \
          "&rate=0.1260365850769451]3483.6026288094054,6[&height=8.559841366136245E-12," \
          "height_95%_HPD={0.0,2.9103830456733704E-11},height_median=0.0,height_range={0.0," \
          "3.725290298461914E-9},length=64263.38390382354,length_95%_HPD={242.88760407354857," \
          "168923.3746203835},length_median=11621.922183927634,length_range={242.88760407354857," \
          "2.4394152189427603E7}]:[&rate=0.15749022880313052]11917.783728732666)[&height=" \
          "66462.97722328358,height_95%_HPD={242.8876040735488,172328.18950797373},height_median=" \
          "11917.783728732666,height_range={242.8876040735488,2.4394152189427607E7},length=" \
          "21074.24071127439,length_95%_HPD={9.33738591016754,65106.83779065257},length_median=" \
          "3497.449465911657,length_range={9.33738591016754,3253753.156094387},posterior=" \
          "0.9266764431409146]:[&rate=0.15749022880313052]1863.0826187841885,5[&height=" \
          "8.909222646386704E-12,height_95%_HPD={0.0,2.9103830456733704E-11},height_median=0.0," \
          "height_range={0.0,3.725290298461914E-9},length=86228.77947668775,length_95%_HPD={" \
          "320.8279037754549,250680.98349718086},length_median=16191.236491985874,length_range={" \
          "320.8279037754549,2.5385363199801262E7}]:[&rate=0.1764340946476647]13780.866347516854)[" \
          "&height=68851.55714103008,height_95%_HPD={332.8967971018673,208360.19528088247}," \
          "height_median=13780.866347516854,height_range={332.8967971018673,1.3209839631035523E7}," \
          "length=36292.10334947041,length_95%_HPD={6.842269636452329,77005.81130131785}," \
          "length_median=3986.097675025603,length_range={6.842269636452329,7690578.10700983}," \
          "posterior=0.6665777896280496]:[&rate=0.06963566760197197]10620.834879287806)[&height=" \
          "138844.64905308632,height_95%_HPD={474.13147831140884,367996.7683084475},height_median=" \
          "24401.70122680466,height_range={474.13147831140884,3.1088350108564746E7},length=0.0,posterior=1.0]:0.0"
    tree = loads(nwk)[0]
    leafs = [n for n in tree.walk() if n.is_leaf]
    assert len(leafs[0].comments) == 2
    assert 'rate' in leafs[0].properties
    assert tree.newick == nwk


@pytest.mark.slow
def test_gtdb_tree(fixture_dir):
    tree = read(fixture_dir / 'ar53_r207.tree')[0]
    nodes = [node.name for node in tree.walk() if node.name]
    assert nodes[-9] == "'100.0:p__Undinarchaeota; c__Undinarchaeia; o__Undinarchaeales'"


def test_mrbayes_tree(fixture_dir):
    tree = read(fixture_dir / 'mrbayes.nwk')[0]
    nodes = {node.name: node.properties for node in tree.walk() if node.name}
    assert nodes['1'] == {
        'prob': '1.00000000e+00',
        'prob_stddev': '0.00000000e+00',
        'prob_range': '{1.00000000e+00,1.00000000e+00}',
        'prob(percent)': '"100"',
        'prob+-sd': '"100+-0"',
        'length_mean': '1.32336084e-02',
        'length_median': '1.32257600e-02',
        'length_95%HPD': '{1.25875600e-02,1.38462600e-02}',
    }


def test_mesquite():
    tree = loads('((1:15.3,4:15.3):4.5,(3:12.7,(2:8.2,5:8.2):4.5):7.1)[%selected = on ] [% ] [%  setBetweenBits = selected ];')[0];
    assert {'1', '2', '3', '4', '5'} == {n.name for n in tree.walk() if n.name}

