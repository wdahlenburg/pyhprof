"""Utilities for finding the connections between different objects.
Primarily for computing the deep (i.e. retained) size of objects, which includes the
size of objects they reference.
"""

import struct
from collections import deque

from .constants import ARRAY_OVERHEAD, TYPE_SIZES
from .parsers import HProfParser, HeapDumpParser
from .heap_blocks import ClassDump, InstanceDump, ObjectArrayDump, PrimitiveArrayDump



# TODO: Make this code worth with either id sizes of 4 or 8
ID_SIZE = 8


class BaseReference(object):
    def __init__(self, base_size, children={}):
        self.base_size = base_size
        self.children = children

    def resolve_children(self, references):
        for k, c in self.children.iteritems():
            self.children[k] = references.get(c)

    def bfs_children(self):
        seen = {self}
        queue = deque([self])
        while queue:
            n = queue.popleft()
            yield n
            for child in n.children.itervalues():
                if child is not None and child not in seen:
                    seen.add(n)
                    queue.append(child)

    def count_deep_children(self):
        return sum(1 for _ in self.bfs_children())

    def compute_deep_size(self):
        return sum(n.base_size for n in self.bfs_children())


class JavaClass(object):
    def __init__(self, name, parent_class_id, instance_fields):
        self.name = name
        self.parent_class_id = parent_class_id
        self.instance_fields = instance_fields

    def __str__(self):
        return 'Class<%s>' % self.name


class InstanceReference(BaseReference):
    def __init__(self, cls, base_size, fields):
        super(InstanceReference, self).__init__(base_size, fields)
        self.cls = cls

    @classmethod
    def build_from_instance_dump(cls, strings, instance_cls, instance):
        offset = 0
        fields = {}
        for name_id, tp in instance_cls.instance_fields:
            if tp == 'OBJECT':
                id = struct.unpack('>Q', instance.bytes[offset:offset + ID_SIZE])[0]
                name = strings[name_id]
                fields[name] = id
                offset += ID_SIZE
            else:
                offset += TYPE_SIZES[tp]
        return cls(instance_cls, len(instance.bytes), fields)

    def __str__(self):
        return 'Instance<%s>' % self.cls.name


class ObjectArrayReference(BaseReference):
    def __init__(self, elements):
        super(ObjectArrayReference, self).__init__(
            ARRAY_OVERHEAD + len(elements) * ID_SIZE,
            {i: el for i, el in enumerate(elements)}
        )

    def __str__(self):
        return 'Object Array Length %d' % len(self.children)


class PrimitiveArrayReference(BaseReference):
    def __init__(self, element_type, element_size, number_of_elements):
        super(PrimitiveArrayReference, self).__init__(
            ARRAY_OVERHEAD + element_size * number_of_elements
        )
        self.element_type = element_type
        self.element_size = element_size
        self.number_of_elements = number_of_elements

    def __str__(self):
        return '%s Array Length %d' % (self.element_type, self.number_of_elements)


class ReferenceBuilder(object):
    def __init__(self, f):
        self.f = f
        self.strings = {}
        self.class_name_ids = {}
        self.classes = {}
        self.references = {}

    def build(self):
        heap_dump = self.read_hprof()
        self.read_references(heap_dump)
        for c in self.classes.values():
            c.parent_class = self.references.get(c.parent_class_id)
        for r in self.references.values():
            r.resolve_children(self.references)
        return self.references.values()

    def read_hprof(self):
        p = HProfParser(self.f)
        while True:
            try:
                b = p.read_next_block()
            except EOFError:
                break
            if not b:
                break
            if b.tag_name == 'HEAP_DUMP':
                return b
            elif b.tag_name == 'STRING':
                self.strings[b.id] = b.contents
            elif b.tag_name == 'LOAD_CLASS':
                self.class_name_ids[b.class_id] = b.class_name_id
        assert 0

    def read_references(self, heap_dump):
        self.f.seek(heap_dump.start)
        p = HeapDumpParser(self.f, ID_SIZE)

        for i, el in enumerate(p):
            if not i % 200000:
                print i
            if isinstance(el, ClassDump):
                self.classes[el.id] = JavaClass(self.strings[self.class_name_ids[el.id]],
                                                el.super_class_id,
                                                el.instance_fields)
            elif isinstance(el, InstanceDump):
                self.references[el.id] = InstanceReference.build_from_instance_dump(
                    self.strings,
                    self.classes[el.class_object_id],
                    el
                )
            elif isinstance(el, ObjectArrayDump):
                self.references[el.id] = ObjectArrayReference(el.elements)
            elif isinstance(el, PrimitiveArrayDump):
                self.references[el.id] = PrimitiveArrayReference(el.element_type, p.type_size(el.element_type), el.size)
