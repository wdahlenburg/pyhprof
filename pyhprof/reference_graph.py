"""Create graphviz specification for rendering object graph
"""

from __future__ import division

from collections import Counter

from .references import ObjectArrayReference, InstanceReference


def generic_get_elements(r):
    return []


def hash_map_get_elements(r):
    try:
        table = r.children['table']
    except KeyError:
        return generic_get_elements(r)
    acc = []
    for e in table.children.itervalues():
        if e is None:
            continue
        try:
            k = e.children['key']
            v = e.children['value']
        except KeyError:
            continue
        acc.append((k, v))
    return acc


def hash_set_get_elements(r):
    try:
        m = r.children['map']
    except KeyError:
        return generic_get_elements(r)
    return [k for k, v in hash_map_get_elements(m)]


COLLECTION_ELEMENT_ACCESSORS = {
    'java/util/HashMap': hash_map_get_elements,
    'java/util/HashSet': hash_set_get_elements
}


class ReferenceGraphBuilder(object):
    def __init__(self, root_reference, max_depth=6, collection_element_accessors=COLLECTION_ELEMENT_ACCESSORS,
                 min_size=1e5, max_name_characters=16):
        self.root_reference = root_reference
        self.max_depth = max_depth
        self.collection_element_accessors = collection_element_accessors
        self.min_size = min_size
        self.max_name_characters = max_name_characters
        self.sizes = {}
        self.lines = []
        self.visited = set()

    def build(self):
        del self.lines[::]
        self.visited.clear()
        self.rec(self.root_reference, 0)
        return self.create_graphviz()

    def create_graphviz(self):
        return 'digraph G {%s}' % '\n'.join(self.lines)

    @staticmethod
    def ref_name(r):
        return abs(id(r))

    @staticmethod
    def mem_str(n):
        if n < 1000:
            return '%dB' % (n,)
        elif n < 1000 ** 2:
            return '%dK' % (n / 1000,)
        elif n < 1000 ** 3:
            return '%dM' % (n / 1000 ** 2,)
        else:
            return '%dG' % (n / 1000 ** 3,)

    def split_name(self, n):
        acc = []
        line_length = 0
        for c in n:
            if line_length > self.max_name_characters and (c.isupper() or c == '<'):
                acc.append('-\n')
                line_length = 0
            acc.append(c)
            line_length += 1
        return ''.join(acc)

    def get_size(self, r):
        try:
            return self.sizes[r]
        except KeyError:
            self.sizes[r] = s = r.compute_deep_size()
            return s

    def make_arc(self, parent, child, label):
        self.lines.append('%d -> %d [label="%s"];' % (self.ref_name(parent), self.ref_name(child), label))

    def make_node(self, node, label, shape='oval'):
        f = self.get_size(node) / self.get_size(self.root_reference)
        r = 255 * f
        g = 255 * (1 - f)
        b = 20
        a = 0xff * 0.5
        color = '#%02X%02X%02X%02X' % (r, g, b, a)
        self.lines.append('%d [label="%s (%s)" shape=%s style=filled color="%s"];' % (self.ref_name(node), label,
                                                                                      self.mem_str(self.get_size(node)),
                                                                                      shape, color))

    def process_collection(self, r):
        elements = self.collection_element_accessors[r.cls.name](r)
        if elements is not None:
            if len(elements) == 0:
                element_type = 'Object'
            else:
                element_types = Counter(el for el in elements)
                element_type = max(element_types, key=lambda et: element_types[et])
                if isinstance(element_type, tuple):
                    element_type = ','.join(el.simple_name() for el in element_type)
                else:
                    element_type = element_type.simple_name()
            name = '%s<%s>' % (r.simple_name(), element_type)
        else:
            name = r.simple_name()
        name = self.split_name(name)
        self.make_node(r, name, shape='box')

    def rec(self, r, depth, parent=None, parent_label=None):
        if r is None or depth > self.max_depth or self.get_size(r) < self.min_size:
            return

        if parent is not None:
            self.make_arc(parent, r, self.split_name(parent_label))

        if r in self.visited:
            return
        self.visited.add(r)

        if isinstance(r, InstanceReference) and r.cls.name in self.collection_element_accessors:
            self.process_collection(r)
            return

        name = r.simple_name()
        if 'Array' in name:
            a, b = name.split('len=')
            name = a + '\nlen=' + b
        else:
            name = name.rsplit('$', 1)[-1]
        name = self.split_name(name)
        self.make_node(r, name)

        if not isinstance(r, ObjectArrayReference) and depth < self.max_depth:
            for n, c in sorted(r.children.iteritems()):
                self.rec(c, depth + 1, r, n)
