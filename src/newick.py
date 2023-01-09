"""
Functionality to read and write the Newick serialization format for trees.

.. seealso:: https://en.wikipedia.org/wiki/Newick_format
"""
import re
import typing
import pathlib
import itertools
import dataclasses

__version__ = "1.5.0"

RESERVED_PUNCTUATION = ':;,()'
QUOTE = "'"
ESCAPE = {"'", "\\"}
RP_PATTERN = re.compile('|'.join(re.escape(c) for c in RESERVED_PUNCTUATION))


def length_parser(x):
    return float(x or 0.0)


def length_formatter(x):
    return '%s' % x


def check_string(n, type_):
    if RP_PATTERN.search(n):
        raise ValueError('"{}" may not appear in {}'.format(RESERVED_PUNCTUATION, type_))
    if re.search(r'\s+', n):
        raise ValueError('Whitespace may not appear in {}'.format(type_))


class Node(object):
    """
    A Node may be a tree, a subtree or a leaf.

    :ivar typing.Optional[Node] ancestor: `None` if the node is the root node of a tree.
    :ivar typing.List[Node] descendants: List of immediate children of the node.
    """
    def __init__(self,
                 name: typing.Optional[str] = None,
                 length: typing.Optional[typing.Union[str, float]] = None,
                 comment: typing.Optional[str] = None,
                 comments: typing.Optional[list] = None,
                 descendants: typing.Optional[typing.Iterable] = None,
                 auto_quote: bool = False,
                 **kw):
        """
        :param name: Node label.
        :param length: Branch length from the new node to its parent.
        :param auto_quote: Optional flag specifying whether the node name should be quoted if \
        necessary.
        :param kw: Recognized keyword arguments:\
            `length_parser`: Custom parser for the `length` attribute of a Node.\
            `length_formatter`: Custom formatter for the branch length when formatting a\
            Node as Newick string.
        """
        self._auto_quote = auto_quote
        self.name = name
        self.comments = comments or ([comment] if comment else [])
        self.descendants = descendants or []
        self.ancestor = None
        self._length_parser = kw.pop('length_parser', length_parser)
        self._length_formatter = kw.pop('length_formatter', length_formatter)
        self._colon_before_comment = kw.pop('colon_before_comment', False)
        self.length = length

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n):
        quoted = n and n.startswith(QUOTE) and n.endswith(QUOTE)

        if (not quoted) and self._auto_quote and \
                any(char in n for char in RESERVED_PUNCTUATION + QUOTE):
            n = "{}{}{}".format(QUOTE, n.replace("'", "''"), QUOTE)
            quoted = True

        if n and not quoted:
            check_string(n, 'unquoted string')
        self._name = n

    def __repr__(self):
        return 'Node("%s")' % self.name

    @property
    def unquoted_name(self):
        n = self.name
        if n.startswith(QUOTE) and n.endswith(QUOTE):
            n = n[1:-1]
            for esc in ESCAPE:
                n = n.replace(esc + QUOTE, QUOTE)
        return n

    @property
    def length(self) -> float:
        return self._length_parser(self._length)

    @length.setter
    def length(self, length_: float):
        if length_ is None:
            self._length = length_
        else:
            if isinstance(length_, str):
                length_ = length_.strip()
                check_string(length_, 'branch length')
            self._length = self._length_formatter(length_)

    @property
    def comment(self):  # Backwards compatibility.
        return self.comments[0] if self.comments else None

    @classmethod
    def create(cls, **kw) -> 'Node':  # Backwards compatibility.
        return cls(**kw)

    @property
    def descendants(self):
        return self._descendants

    @descendants.setter
    def descendants(self, nodes: typing.Iterable):
        self._descendants = []
        for node in nodes:
            self.add_descendant(node)

    def add_descendant(self, node: 'Node'):
        node.ancestor = self
        self._descendants.append(node)

    @property
    def newick(self) -> str:
        """The representation of the Node in Newick format."""
        colon_done = False
        label = self.name or ''
        if self.comments:
            if self._length and self._colon_before_comment:
                label += ':'
                colon_done = True
            label += '[{}]'.format('|'.join(self.comments))
        if self._length:
            if not colon_done:
                label += ':'
            label += self._length
        descendants = ','.join([n.newick for n in self.descendants])
        if descendants:
            descendants = '(' + descendants + ')'
        return descendants + label

    def _ascii_art(self, char1='\u2500', show_internal=True, maxlen=None):
        if maxlen is None:
            maxlen = max(
                len(n.name) for n in self.walk()
                if n.name and (show_internal or n.is_leaf)) + 4
        pad = ' ' * (maxlen - 1)
        namestr = '\u2500' + (self.name or '')

        if self.descendants:
            mids = []
            result = []
            for i, c in enumerate(self.descendants):
                if len(self.descendants) == 1:
                    char2 = '\u2500'
                elif i == 0:
                    char2 = '\u250c'
                elif i == len(self.descendants) - 1:
                    char2 = '\u2514'
                else:
                    char2 = '\u2500'
                clines, mid = c._ascii_art(
                    char1=char2, show_internal=show_internal, maxlen=maxlen)
                mids.append(mid + len(result))
                result.extend(clines)
                result.append('')
            result.pop()
            lo, hi, end = mids[0], mids[-1], len(result)
            prefixes = [pad] * (lo + 1) +\
                       [pad + '\u2502'] * (hi - lo - 1) + \
                       [pad] * (end - hi)
            mid = (lo + hi) // 2
            prefixes[mid] = char1 + '\u2500' * (len(prefixes[mid]) - 2) + prefixes[mid][-1]
            result = [p + l for p, l in zip(prefixes, result)]
            if show_internal:
                stem = result[mid]
                result[mid] = stem[0] + namestr + stem[len(namestr) + 1:]
            return result, mid
        return [char1 + namestr], 0

    def ascii_art(self, strict: bool = False, show_internal: bool = True) -> str:
        r"""
        Return a unicode string representing a tree in ASCII art fashion.

        :param strict: Use ASCII characters strictly (for the tree symbols).
        :param show_internal: Show labels of internal nodes.
        :return: unicode string

        >>> node = loads('((A,B)C,((D,E)F,G,H)I)J;')[0]
        >>> print(node.ascii_art(show_internal=False, strict=True))
                /-A
            /---|
            |   \-B
        ----|       /-D
            |   /---|
            |   |   \-E
            \---|
                |-G
                \-H
        """
        cmap = {
            '\u2500': '-',
            '\u2502': '|',
            '\u250c': '/',
            '\u2514': '\\',
            '\u251c': '|',
            '\u2524': '|',
            '\u253c': '+',
        }

        def normalize(line):
            m = re.compile(r'(?<=\u2502)(?P<s>\s+)(?=[\u250c\u2514\u2502])')
            line = m.sub(lambda m: m.group('s')[1:], line)
            line = re.sub('\u2500\u2502', '\u2500\u2524', line)  # -|
            line = re.sub('\u2502\u2500', '\u251c', line)  # |-
            line = re.sub('\u2524\u2500', '\u253c', line)  # -|-
            if strict:
                for u, a in cmap.items():
                    line = line.replace(u, a)
            return line
        return '\n'.join(
            normalize(line) for line in self._ascii_art(show_internal=show_internal)[0]
            if set(line) != {' ', '\u2502'})  # remove lines of only spaces and pipes

    @property
    def is_leaf(self) -> bool:
        return not bool(self.descendants)

    @property
    def is_binary(self) -> bool:
        return all([len(n.descendants) in (0, 2) for n in self.walk()])

    def walk(self, mode=None) -> typing.Generator['Node', None, None]:
        """
        Traverses the (sub)tree rooted at self, yielding each visited Node.

        .. seealso:: https://en.wikipedia.org/wiki/Tree_traversal

        :param mode: Specifies the algorithm to use when traversing the subtree rooted \
        at self. `None` for breadth-first, `'postorder'` for post-order depth-first \
        search.
        :return: Generator of the visited Nodes.
        """
        if mode == 'postorder':
            for n in self._postorder():
                yield n
        else:  # default to a breadth-first search
            yield self
            for node in self.descendants:
                for n in node.walk():
                    yield n

    def visit(self,
              visitor: typing.Callable[['Node'], None],
              predicate: typing.Optional[typing.Callable[['Node'], bool]] = None,
              **kw):
        """
        Apply a function to matching nodes in the (sub)tree rooted at self.

        :param visitor: A callable accepting a Node object as single argument..
        :param predicate: A callable accepting a Node object as single argument and \
        returning a boolean signaling whether Node matches; if `None` all nodes match.
        :param kw: Addtional keyword arguments are passed through to self.walk.
        """
        predicate = predicate or bool

        for n in self.walk(**kw):
            if predicate(n):
                visitor(n)

    def _postorder(self):
        stack = [self]
        descendant_map = {id(node): [n for n in node.descendants] for node in self.walk()}

        while stack:
            node = stack[-1]
            descendants = descendant_map[id(node)]

            # if we are at a leave-node, we remove the item from the stack
            if not descendants:
                stack.pop()
                yield node
                if stack:
                    descendant_map[id(stack[-1])].pop(0)
            else:
                stack.append(descendants[0])

    def get_leaves(self) -> typing.List['Node']:
        """
        Get all the leaf nodes of the subtree descending from this node.

        :return: List of Nodes with no descendants.
        """
        return [n for n in self.walk() if n.is_leaf]

    def get_node(self, label: str) -> 'Node':
        """
        Gets the specified node by name.

        :return: Node or None if name does not exist in tree
        """
        for n in self.walk():
            if n.name == label:
                return n

    def get_leaf_names(self) -> typing.List[str]:
        """
        Get the names of all the leaf nodes of the subtree descending from
        this node.

        :return: List of names of Nodes with no descendants.
        """
        return [n.name for n in self.get_leaves()]

    def prune(self, nodes: typing.List['Node'], inverse: bool = False):
        """
        Remove all those nodes in the specified list, or if inverse=True,
        remove all those nodes not in the specified list. The specified nodes
        must be distinct from the root node.

        :param nodes: A list of Node objects
        :param inverse: Specifies whether to remove nodes in the list or not in the list.
        """
        self.visit(
            lambda n: n.ancestor.descendants.remove(n),
            # We won't prune the root node, even if it is a leave and requested to
            # be pruned!
            lambda n: ((not inverse and n in nodes) or  # noqa: W504
                       (inverse and n.is_leaf and n not in nodes)) and n.ancestor,
            mode="postorder")

    def prune_by_names(self, node_names: typing.List[str], inverse: bool = False):
        """
        Perform an (inverse) prune, with leaves specified by name.
        :param node_names: A list of Node names (strings)
        :param inverse: Specifies whether to remove nodes in the list or not in the list.
        """
        self.prune([n for n in self.walk() if n.name in node_names], inverse)

    def remove_redundant_nodes(self, preserve_lengths: bool = True, keep_leaf_name: bool = False):
        """
        Remove all nodes which have only a single child, and attach their
        grandchildren to their parent.  The resulting tree has the minimum
        number of internal nodes required for the number of leaves.

        :param preserve_lengths: If `True`, branch lengths of removed nodes are \
        added to those of their children.
        :param keep_leave_name: If `True`, the name of the leaf on a branch with redundant \
        nodes will be kept; otherwise, the name of the node closest to the root will be used.
        """
        for n in self.walk(mode='postorder'):
            while n.ancestor and len(n.ancestor.descendants) == 1:
                grandfather = n.ancestor.ancestor
                father = n.ancestor
                if preserve_lengths:
                    n.length += father.length
                if keep_leaf_name:
                    father.name = n.name

                if grandfather:
                    for i, child in enumerate(grandfather.descendants):
                        if child is father:
                            del grandfather.descendants[i]
                    grandfather.add_descendant(n)
                    father.ancestor = None
                else:
                    self.descendants = n.descendants
                    if preserve_lengths:
                        self.length = n.length

    def resolve_polytomies(self):
        """
        Insert additional nodes with length=0 into the subtree in such a way
        that all non-leaf nodes have only 2 descendants, i.e. the tree becomes
        a fully resolved binary tree.
        """
        def _resolve_polytomies(n):
            new = Node(length=self._length_formatter(self._length_parser('0')))
            while len(n.descendants) > 1:
                new.add_descendant(n.descendants.pop())
            n.descendants.append(new)

        self.visit(_resolve_polytomies, lambda n: len(n.descendants) > 2)

    def remove_names(self):
        """
        Set the name of all nodes in the subtree to None.
        """
        self.visit(lambda n: setattr(n, 'name', None))

    def remove_internal_names(self):
        """
        Set the name of all non-leaf nodes in the subtree to None.
        """
        self.visit(lambda n: setattr(n, 'name', None), lambda n: not n.is_leaf)

    def remove_leaf_names(self):
        """
        Set the name of all leaf nodes in the subtree to None.
        """
        self.visit(lambda n: setattr(n, 'name', None), lambda n: n.is_leaf)

    def remove_lengths(self):
        """
        Set the length of all nodes in the subtree to None.
        """
        self.visit(lambda n: setattr(n, 'length', None))


def loads(s: str, strip_comments: bool = False, **kw) -> typing.List[Node]:
    """
    Load a list of trees from a Newick formatted string.

    :param s: Newick formatted string.
    :param strip_comments: Flag signaling whether to strip comments enclosed in square \
    brackets.
    :param kw: Keyword arguments are passed through to `Node.create`.
    :return: List of Node objects.
    """
    return [ns.to_node() for ns in NewickString(s).iter_subtrees(strip_comments=strip_comments)]


def dumps(trees: typing.Union[Node, typing.Iterable[Node]]) -> str:
    """
    Serialize a list of trees in Newick format.

    :param trees: List of Node objects or a single Node object.
    :return: Newick formatted string.
    """
    if isinstance(trees, Node):
        trees = [trees]
    return ';\n'.join([tree.newick for tree in trees]) + ';'


def load(fp, strip_comments=False, **kw) -> typing.List[Node]:
    """
    Load a list of trees from an open Newick formatted file.

    :param fp: open file handle.
    :param strip_comments: Flag signaling whether to strip comments enclosed in square \
    brackets.
    :param kw: Keyword arguments are passed through to `Node.create`.
    :return: List of Node objects.
    """
    kw['strip_comments'] = strip_comments
    return loads(fp.read(), **kw)


def dump(tree: typing.Union[Node, typing.Iterable[Node]], fp):
    fp.write(dumps(tree))


def read(fname, encoding='utf8', strip_comments=False, **kw) -> typing.List[Node]:
    """
    Load a list of trees from a Newick formatted file.

    :param fname: file path.
    :param strip_comments: Flag signaling whether to strip comments enclosed in square \
    brackets.
    :param kw: Keyword arguments are passed through to `Node.create`.
    :return: List of Node objects.
    """
    kw['strip_comments'] = strip_comments
    with pathlib.Path(fname).open(encoding=encoding) as fp:
        return load(fp, **kw)


def write(tree: typing.Union[Node, typing.Iterable[Node]], fname, encoding='utf8'):
    with pathlib.Path(fname).open(encoding=encoding, mode='w') as fp:
        dump(tree, fp)


@dataclasses.dataclass
class Token:
    """
    We parse Newick in one pass, storing the data as list of tokens with enough
    information to extract relevant parts from this list lateron.
    """
    __slots__ = [
        'char',
        'inquote',
        'commentlevel',
        'level',
        'regular',
        'is_comma',
        'is_colon',
        'is_semicolon']
    char: str  # The character, i.e. string of length 1.
    inquote: bool  # Whether the character is inside a quoted string.
    commentlevel: int  # Whether the character is inside a (nested) comment.
    level: int  # How deep the character is nested in the tree.
    regular: bool  # Whether the character is outside quotes or comments, i.e. may convey syntax.
    is_comma: bool  # Whether the token is a "Newick-comma", i.e. separates sibling nodes.
    is_colon: bool  # Whether the token is a "Newick-colon", i.e. separates label and length.
    is_semicolon: bool  # Whether the token is a "Newick-semicolon", i.e. separates subtrees.


class NewickString(list):
    """
    A list of tokens with methods to access newick constituents.
    """
    def __init__(self, s: typing.Union[str, typing.List[Token]]):
        list.__init__(self, s if not isinstance(s, str) else [])

        if isinstance(s, str):
            # An unparsed string. We must convert it to a list of tokens.
            i, inquote, commentlevel, doublequote, bracketlevel = -1, False, 0, False, 0
            for i, c in enumerate(s):
                if c == QUOTE and not inquote:  # Start of quoted string
                    inquote = True
                elif c == QUOTE and inquote and not doublequote:  # End of quoted string
                    inquote = False
                elif c in ESCAPE:
                    if c == QUOTE and doublequote:  # The "escaped" single quote
                        doublequote = False
                    elif i < len(s) - 1 and s[i + 1] == QUOTE:
                        # The escape character for the following single quote
                        doublequote = True

                if not inquote:  # Outside of quoted strings we keep track of comment nesting.
                    if c == '[':
                        commentlevel += 1

                if (not inquote) and commentlevel == 0:
                    # Outside of quoted strings and comments we keep track of node nesting.
                    # Note: The enclosing brackets have lower bracketlevel than the content.
                    if c == ')':
                        bracketlevel -= 1
                        if bracketlevel < 0:
                            raise ValueError('invalid brace nesting')

                iq = True if c == QUOTE else inquote
                reg = (not iq) and (not bool(commentlevel))
                self.append(Token(
                    c, iq, commentlevel, bracketlevel, reg,
                    reg and c == ',',
                    reg and c == ':',
                    reg and c == ';',
                ))

                if not inquote:  # Outside of quoted strings we keep track of comment nesting.
                    if c == ']':
                        commentlevel -= 1
                        if commentlevel < 0:
                            raise ValueError('invalid comment nesting')

                if (not inquote) and commentlevel == 0:
                    # Outside of quoted strings and comments we keep track of node nesting.
                    if c == '(':
                        bracketlevel += 1
        # The minimal bracket level of the list of tokens:
        self.minlevel = self[-1].level if self else 0

    def to_node(self) -> Node:
        # Parse label and length of the root node:
        tokens = list(
            itertools.takewhile(lambda t: t.level == self.minlevel, reversed(self)))
        if tokens and tokens[-1].char == ')':
            tokens = tokens[:-1]
        tokens.reverse()

        name, length, comment, comments = [], [], [], []
        # We store the index of the colon and of the first comment:
        icolon, icomment = -1, -1

        for i, t in enumerate(tokens):
            if t.is_colon:
                icolon = i
            else:
                if t.commentlevel:
                    if icomment == -1:
                        icomment = i
                    comment.append(t.char)
                else:
                    if comment:
                        comments.append(''.join(comment))
                        comment = []

                    if icolon == -1:
                        name.append(t.char)
                    else:
                        length.append(t.char)

        if comment:
            comments.append(''.join(comment))

        return Node.create(
            name=''.join(name).strip() or None,
            length=''.join(length) or None,
            comments=[c[1:-1] for c in comments],
            colon_before_comment=icolon < icomment,
            descendants=[d.to_node() for d in self.iter_descendants()])

    def iter_descendants(self) -> typing.Generator['NewickString', None, None]:
        tokens, comma = [], False
        for t in self:
            if t.is_comma and t.level == self.minlevel + 1:
                comma = True
                yield NewickString(tokens)
                tokens = []
            elif t.level > self.minlevel:
                tokens.append(t)
        if comma or tokens:
            yield NewickString(tokens)

    def iter_subtrees(self, strip_comments=False) -> typing.Generator['NewickString', None, None]:
        def checked(t):
            if t:
                if t[0].level != t[-1].level:
                    raise ValueError('different number of opening and closing braces')
                if t[-1].commentlevel > 1 or \
                        (t[-1].commentlevel == 1 and not t[-1].char == ']'):
                    raise ValueError('invalid comment nesting')
                if t[-1].inquote and not t[-1].char == QUOTE:
                    raise ValueError('invalid quoting')
            return NewickString(t)

        tokens = []
        for t in self:
            if t.is_semicolon:
                yield checked(tokens)
                tokens = []
                continue
            if not (strip_comments and t.commentlevel):
                tokens.append(t)

        if tokens:
            yield checked(tokens)
