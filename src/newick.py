# coding: utf8
"""
Functionality to read and write the Newick serialization format for trees.

.. seealso:: https://en.wikipedia.org/wiki/Newick_format
"""
from __future__ import unicode_literals
import io
import re

__version__ = "0.9.3.dev0"

RESERVED_PUNCTUATION = ':;,()'
COMMENT = re.compile('\[[^\]]*\]')


def length_parser(x):
    return float(x or 0.0)


def length_formatter(x):
    return '%s' % x


class Node(object):
    """
    A Node may be a tree, a subtree or a leaf.

    A Node has optional name and length (from parent) and a (possibly empty) list of
    descendants. It further has an ancestor, which is *None* if the node is the
    root node of a tree.
    """
    def __init__(self, name=None, length=None, **kw):
        """
        :param name: Node label.
        :param length: Branch length from the new node to its parent.
        :param kw: Recognized keyword arguments:\
            `length_parser`: Custom parser for the `length` attribute of a Node.\
            `length_formatter`: Custom formatter for the branch length when formatting a\
            Node as Newick string.
        """
        for char in RESERVED_PUNCTUATION:
            if (name and char in name) or (length and char in length):
                raise ValueError(
                    'Node names or branch lengths (%r) must not contain "%s"' % (name, char))
        self.name = name
        self._length = length
        self.descendants = []
        self.ancestor = None
        self._length_parser = kw.pop('length_parser', length_parser)
        self._length_formatter = kw.pop('length_formatter', length_formatter)

    def __repr__(self):
        return 'Node("%s")' % self.name

    @property
    def length(self):
        return self._length_parser(self._length)

    @length.setter
    def length(self, l):
        if l is None:
            self._length = l
        else:
            self._length = self._length_formatter(l)

    @classmethod
    def create(cls, name=None, length=None, descendants=None, **kw):
        """
        Create a new `Node` object.

        :param name: Node label.
        :param length: Branch length from the new node to its parent.
        :param descendants: list of descendants or `None`.
        :param kw: Additonal keyword arguments are passed through to `Node.__init__`.
        :return: `Node` instance.
        """
        node = cls(name=name, length=length, **kw)
        for descendant in descendants or []:
            node.add_descendant(descendant)
        return node

    def add_descendant(self, node):
        node.ancestor = self
        self.descendants.append(node)

    @property
    def newick(self):
        """The representation of the Node in Newick format."""
        label = self.name or ''
        if self._length:
            label += ':' + self._length
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

    def ascii_art(self, strict=False, show_internal=True):
        """
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
            m = re.compile('(?<=\u2502)(?P<s>\s+)(?=[\u250c\u2514\u2502])')
            line = m.sub(lambda m: m.group('s')[1:], line)
            line = re.sub('\u2500\u2502', '\u2500\u2524', line)  # -|
            line = re.sub('\u2502\u2500', '\u251c', line)  # |-
            line = re.sub('\u2524\u2500', '\u253c', line)  # -|-
            if strict:
                for u, a in cmap.items():
                    line = line.replace(u, a)
            return line
        return '\n'.join(
            normalize(l) for l in self._ascii_art(show_internal=show_internal)[0]
            if set(l) != {' ', '\u2502'})  # remove lines of only spaces and pipes

    @property
    def is_leaf(self):
        return not bool(self.descendants)

    @property
    def is_binary(self):
        return all([len(n.descendants) in (0, 2) for n in self.walk()])

    def walk(self, mode=None):
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

    def visit(self, visitor, predicate=None, **kw):
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

    def get_leaves(self):
        """
        Get all the leaf nodes of the subtree descending from this node.

        :return: List of Nodes with no descendants.
        """
        return [n for n in self.walk() if n.is_leaf]

    def get_node(self, label):
        """
        Gets the specified node by name.

        :return: Node or None if name does not exist in tree
        """
        for n in self.walk():
            if n.name == label:
                return n

    def get_leaf_names(self):
        """
        Get the names of all the leaf nodes of the subtree descending from
        this node.

        :return: List of names of Nodes with no descendants.
        """
        return [n.name for n in self.get_leaves()]

    def prune(self, leaves, inverse=False):
        """
        Remove all those nodes in the specified list, or if inverse=True,
        remove all those nodes not in the specified list.  The specified nodes
        must be leaves and distinct from the root node.

        :param nodes: A list of Node objects
        :param inverse: Specifies whether to remove nodes in the list or not\
                in the list.
        """
        self.visit(
            lambda n: n.ancestor.descendants.remove(n),
            # We won't prune the root node, even if it is a leave and requested to
            # be pruned!
            lambda n: ((not inverse and n in leaves) or
                       (inverse and n.is_leaf and n not in leaves)) and n.ancestor,
            mode="postorder")

    def prune_by_names(self, leaf_names, inverse=False):
        """
        Perform an (inverse) prune, with leaves specified by name.
        :param node_names: A list of leaaf Node names (strings)
        :param inverse: Specifies whether to remove nodes in the list or not\
                in the list.
        """
        self.prune([l for l in self.walk() if l.name in leaf_names], inverse)

    def remove_redundant_nodes(self, preserve_lengths=True):
        """
        Remove all nodes which have only a single child, and attach their
        grandchildren to their parent.  The resulting tree has the minimum
        number of internal nodes required for the number of leaves.
        :param preserve_lengths: If true, branch lengths of removed nodes are \
        added to those of their children.
        """
        for n in self.walk(mode='postorder'):
            while n.ancestor and len(n.ancestor.descendants) == 1:
                grandfather = n.ancestor.ancestor
                father = n.ancestor
                if preserve_lengths:
                    n.length += father.length

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


def loads(s, strip_comments=False, **kw):
    """
    Load a list of trees from a Newick formatted string.

    :param s: Newick formatted string.
    :param strip_comments: Flag signaling whether to strip comments enclosed in square \
    brackets.
    :param kw: Keyword arguments are passed through to `Node.create`.
    :return: List of Node objects.
    """
    kw['strip_comments'] = strip_comments
    return [parse_node(ss.strip(), **kw) for ss in s.split(';') if ss.strip()]


def dumps(trees):
    """
    Serialize a list of trees in Newick format.

    :param trees: List of Node objects or a single Node object.
    :return: Newick formatted string.
    """
    if isinstance(trees, Node):
        trees = [trees]
    return ';\n'.join([tree.newick for tree in trees]) + ';'


def load(fp, strip_comments=False, **kw):
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


def dump(tree, fp):
    fp.write(dumps(tree))


def read(fname, encoding='utf8', strip_comments=False, **kw):
    """
    Load a list of trees from a Newick formatted file.

    :param fname: file path.
    :param strip_comments: Flag signaling whether to strip comments enclosed in square \
    brackets.
    :param kw: Keyword arguments are passed through to `Node.create`.
    :return: List of Node objects.
    """
    kw['strip_comments'] = strip_comments
    with io.open(fname, encoding=encoding) as fp:
        return load(fp, **kw)


def write(tree, fname, encoding='utf8'):
    with io.open(fname, encoding=encoding, mode='w') as fp:
        dump(tree, fp)


def _parse_name(s, offset, node):
    count = _count_spaces(s, offset)
    match = COMMENT.search(s, offset + count)
    if match:
        name = s[offset + count:match.start()]
        node.comment = comment = match.group(0)
        count = len(name) + len(comment)
        name = name.strip()
    else:
        letters = []
        count = 0
        while True:
            try:
                c = s[offset + count]
            except IndexError:
                break
            else:
                if c in RESERVED_PUNCTUATION:
                    break
                else:
                    letters.append(c)
                    count += 1
        name = ''.join(letters).strip() or None
        node.comment = None

    return name, count


def _count_spaces(s, offset):
    count = 0
    while True:
        try:
            c = s[offset]
        except IndexError:
            return count
        else:
            if c.isspace():
                offset += 1
                count += 1
            else:
                return count


def _parse_length(s, offset):
    count = _count_spaces(s, offset)

    try:
        c = s[offset + count]
    except IndexError:
        return None, count
    else:
        if c == ':':
            digits = []
            seenDot = False
            while True:
                count += 1
                try:
                    c = s[offset + count]
                except IndexError:
                    break
                else:
                    if c.isdigit():
                        digits.append(c)
                    elif c == '.' and not seenDot:
                        seenDot = True
                        digits.append(c)
                    else:
                        break
            return ''.join(digits), count
        else:
            return None, count


def _parse_node(s, offset, strip_comments=False, **kw):
    """
    Parse a Newick formatted string into a `Node` object.

    :param s: Newick formatted string to parse.
    :param offset: a 0-based int index into s, indicating where to start parsing.
    :param strip_comments: Flag signaling whether to strip comments enclosed in square \
    brackets.
    :param kw: Keyword arguments are passed through to `Node.create`.
    :return: `Node` instance.
    """
    count = _count_spaces(s, offset)
    node = Node(**kw)

    if s[offset + count] == '(':
        # The node has a list of descendents.
        count += 1
        while True:
            child, subcount = _parse_node(s, offset + count,
                                          strip_comments=strip_comments, **kw)
            count += subcount
            node.add_descendant(child)

            count += _count_spaces(s, offset + count)

            try:
                c = s[offset + count]
            except IndexError:
                break
            else:
                if c == ',':
                    count += 1
                    continue
                elif c == ')':
                    count += 1
                    break
                else:
                    raise SyntaxError('In descendants, could not parse %r' %
                                      s[offset + count:offset + count + 100])

    name, subcount = _parse_name(s, offset + count, node)
    count += subcount
    length, subcount = _parse_length(s, offset + count)
    count += subcount

    node.name = name
    node.length = length

    return node, count


def parse_node(s, strip_comments=False, **kw):
    """
    Parse a Newick formatted string into a `Node` object.

    :param s: Newick formatted string to parse.
    :param strip_comments: Flag signaling whether to strip comments enclosed in square \
    brackets.
    :param kw: Keyword arguments are passed through to `Node.create`.
    :return: `Node` instance.
    """

    node, count = _parse_node(s, 0, strip_comments=strip_comments, **kw)
    count += _count_spaces(s, count)

    try:
        c = s[count]
    except IndexError:
        if count != len(s):
            raise ValueError('Newick unexpected count!')
    else:
        if c == ';':
            count += 1
            count += _count_spaces(s, count)
            if count != len(s):
                print('%d chars unread from input: %r' % (len(s) - count, s[count:]))
        else:
            raise ValueError('Newick could not be parsed from %r.' % s[count:])

    return node
