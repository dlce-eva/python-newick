import pytest
from newick import loads

# Run tests from NESCENT wiki:
# http://informatics.nescent.org/wiki/Supporting_NEXUS#Test_files_for_NEXUS_parsers

testdata = [
    ('basal_trifurcation',
     '(((A:1,B:1):1,(C:1,D:1):1):1,(E:1,F:1):2,(G:1,H:1):2)'),
    ('bush',
     '(((A:1,B:1):1,(C:1,D:1):1):1,((E:1,F:1):1,(G:1,H:1):1):1)'),
    ('bush_branchlength_negative',
     '(((A:1,B:1):1,(C:1,D:1):_0.25):1,((E:1,F:1):1,(G:1,H:1):1):1)'),
    ('bush_branchlength_scientific',
     '(((A:1,B:2e+01):1,(C:9e_01,D:1):1):1,((E:1,F:9E_01):1,(G:2E+01,H:1):1):1)'),
    ('bush_branchlength_zero',
     '(((A:1,B:1):1,(C:0,D:1):1):1,((E:1,F:1):1,(G:1,H:1):1):1)'),
    ('bush_cladogram',
     '(((A,B),(C,D)),((E,F),(G,H)))'),
    ('bush_extended_root_branch',
     '(((A:1,B:1):1,(C:1,D:1):1):1,((E:1,F:1):1,(G:1,H:1):1):1):1'),
    ('bush_inode_labels',
     '(((A:1,B:1)AB:1,(C:1,D:1)CD:1)ABCD:1,((E:1,F:1)EF:1,(G:1,H:1)GH:1)EFGH:1)'),
    ('bush_inode_labels_partial',
     '(((A:1,B:1):1,(C:1,D:1):1):1,((E:1,F:1)EF:1,(G:1,H:1)GH:1)EFGH:1)'),
    ('bush_inode_labels_quoted2',
     "(((A:1,B:1)'inode AB':1,(C:1,D:1)'inode CD':1)'inode ABCD':1,((E:1,F:1)'inode EF':1,"
     "(G:1,H:1)'inode GH':1)'inode EFGH':1)"),
    ('bush quoted string name2',
     '(((A:1,B:1):1,(C:1,D:1):1):1,((E:1,F:1):1,(G:1,H:1):1):1)'),
    ('bush_uneven',
     '(((A:1,B:2):1,(C:1,D:2):1):1,((E:1,F:2):1,(G:1,H:2):1):1)'),
    ('ladder',
     '(((((((A:1,B:1):1,C:2):1,D:3):1,E:4):1,F:5):1,G:6):1,H:7)'),
    ('ladder_cladogram',
     '(((((((A,B),C),D),E),F),G),H)'),
    ('ladder_uneven',
     '(((((((A:1,B:2):1,C:2):1,D:4):1,E:4):1,F:6):1,G:6):1,H:8)'),
    ('rake',
     '(A:1,B:1,C:1,D:1,E:1,F:1,G:1,H:1)'),
    ('rake_cladogram',
     '(A,B,C,D,E,F,G,H)'),
]


@pytest.mark.parametrize("id,nwk", testdata)
def test_nescent(id, nwk):
    tree = loads(nwk)[0]
    assert tree.newick == nwk, "%s\n%s\n%s\n" % (id, nwk, tree.newick)
