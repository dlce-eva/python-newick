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

    n = Node("a'b", auto_quote=True)
    assert n.name == "'a''b'"
    assert n.unquoted_name == "a'b"
    n.name = ":"
    assert n.name == "':'"
    n.name = 'A'
    assert n.name == n.unquoted_name
    assert repr(n) == 'Node("A")'


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
