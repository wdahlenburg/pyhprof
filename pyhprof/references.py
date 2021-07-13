"""Utilities for finding the connections between different objects.
Primarily for computing the deep (i.e. retained) size of objects, which includes the
size of objects they reference.
"""

import struct
from collections import deque
from hexdump import hexdump
import re

from .constants import ARRAY_OVERHEAD, TYPE_SIZES
from .parsers import HProfParser, HeapDumpParser
from .heap_blocks import ClassDump, InstanceDump, ObjectArrayDump, PrimitiveArrayDump


# TODO: Make this code worth with either id sizes of 4 or 8
ID_SIZE = 8


class BaseReference(object):
    def __init__(self, base_size, children=None):
        self.base_size = base_size
        self.children = children or {}

    def resolve_children(self, references):
        for k in self.children.keys():
            self.children[k] = references.get(self.children[k])

    def bfs_transverse(self):
        seen = {self}
        queue = deque([self])
        while queue:
            n = queue.popleft()
            yield n
            for child in n.children.values():
                if child is not None and child not in seen:
                    seen.add(n)
                    queue.append(child)

    def count_deep_children(self):
        return sum(1 for _ in self.bfs_transverse())

    def compute_deep_size(self):
        return sum(n.base_size for n in self.bfs_transverse())


class JavaClass(object):

    parent_class = None

    def __init__(self, id, name, parent_class_id, instance_fields, static_fields, constants):
        self.id = id
        self.name = name
        self.parent_class_id = parent_class_id
        self.instance_fields = instance_fields
        self.static_fields = static_fields
        self.constants = constants

    def __str__(self):
        return 'Class<%s>' % self.name

    def simple_name(self):
        return self.name.rsplit('/', 1)[-1]


class InstanceReference(BaseReference):
    def __init__(self, id, cls, base_size, fields, bytes):
        super(InstanceReference, self).__init__(base_size, fields)
        self.id = id
        self.cls = cls
        self.bytes = bytes

    @classmethod
    def build_from_instance_dump(cls, strings, instance_cls, instance):
        id = ''
        try:
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
            return cls(id, instance_cls, len(instance.bytes), fields, instance.bytes)
        except:
            pass

    def __str__(self):
        return 'Instance<%s>' % self.cls.name

    def simple_name(self):
        return self.cls.simple_name()


class ObjectArrayReference(BaseReference):
    def __init__(self, id, elements):
        super(ObjectArrayReference, self).__init__(
            ARRAY_OVERHEAD + len(elements) * ID_SIZE,
            {i: el for i, el in enumerate(elements)}
        )
        self.id = id

    def __str__(self):
        return 'Object Array Length %d' % len(self.children)

    def simple_name(self):
        child_names = {c.simple_name() for c in self.children.values() if c is not None}
        return 'Array{%s} len=%d' % (','.join(sorted(child_names)), len(self.children))


class PrimitiveArrayReference(BaseReference):
    def __init__(self, id, element_type, element_size, number_of_elements, data):
        super(PrimitiveArrayReference, self).__init__(
            ARRAY_OVERHEAD + element_size * number_of_elements
        )
        self.id = id
        self.element_type = element_type
        self.element_size = element_size
        self.number_of_elements = number_of_elements
        self.data = data

    def __str__(self):
        return '%s Array Length %d' % (self.element_type, self.number_of_elements)

    def simple_name(self):
        return 'PArray{%s} len=%d' % (self.element_type, self.number_of_elements)

    def raw_data(self):
        return self.data

    def hexdump_data(self):
        hexdump(self.data)

    def ascii_data(self):
        # Ascii is [^\x00-\x7f], but printable is 0x20-0x7e
        ascii_str = re.sub(b'[^\x0a\x0d\x20-\x7e]',b'',bytes(self.data))
        return ascii_str


class ReferenceBuilder(object):
    def __init__(self, f, flags={}):
        self.f = f
        self.strings = {}
        self.class_name_ids = {}
        self.classes = {}
        self.references = {}
        self.variables = {}
        self.variable_type = 0
        if flags['type_one']:
            self.variable_type = 1
        elif flags['type_two']:
            self.variable_type = 2

    def build(self, mx=None):
        heap_dump = self.read_hprof()
        self.read_references(heap_dump, mx)
        for c in self.classes.values():
            c.parent_class = self.references.get(c.parent_class_id)
        for r in self.references.values():
            r.resolve_children(self.references)
        return self.references.values()

    def read_hprof(self):
        self.p = HProfParser(self.f)
        for b in self.p:
            if b.tag_name == 'HEAP_DUMP' or b.tag_name == 'HEAP_DUMP_SEGMENT':
                return b
            elif b.tag_name == 'STRING':
                self.strings[b.id] = b.contents
            elif b.tag_name == 'LOAD_CLASS':
                self.class_name_ids[b.class_id] = b.class_name_id
        raise RuntimeError("No HEAP_DUMP block")

    def read_references(self, heap_dump, mx=None):
        self.f.seek(heap_dump.start)
        p = HeapDumpParser(self.f, ID_SIZE)

        references = []
        for i, el in enumerate(p):
            references.append(el)

        if self.variable_type == 0:
            if b'1.0.2' in self.p.format:
                self.parse_type_two_references(heap_dump, mx, p, references)
            elif b'1.0.1' in self.p.format:
                self.parse_type_one_references(heap_dump, mx, p, references)
            else:
                raise ValueError("Error: Unhandled HPROF format: " + self.p.format)
        elif self.variable_type == 1:
            self.parse_type_one_references(heap_dump, mx, p, references)
        elif self.variable_type == 2:
            self.parse_type_two_references(heap_dump, mx, p, references)

    '''
    
    Type 1

    The block structure is the following for variables:

    InstanceDump -> Key as PrimitiveArrayDump -> InstanceDump -> Value as PrimitiveArrayDump
    or
    Key as PrimitiveArrayDump -> InstanceDump -> Value as PrimitiveArrayDump

    '''
    def parse_type_one_references(self, heap_dump, mx, p, references):
        last_item = None
        for i in range(len(references)):
            el = references[i]

            if mx is not None and i > mx:
                break
            if isinstance(el, ClassDump):
                self.classes[el.id] = JavaClass(el.id, self.strings[self.class_name_ids[el.id]],
                                                el.super_class_id,
                                                el.instance_fields, el.static_fields, el.constants_pool)
            elif isinstance(el, InstanceDump):
                self.references[el.id] = InstanceReference.build_from_instance_dump(
                    self.strings,
                    self.classes[el.class_object_id],
                    el
                )
            elif isinstance(el, ObjectArrayDump):
                self.references[el.id] = ObjectArrayReference(el.id, el.elements)
            elif isinstance(el, PrimitiveArrayDump):
                self.references[el.id] = PrimitiveArrayReference(el.id, el.element_type, p.type_size(el.element_type), el.size, el.data)
                if (type(references[i-2]) == PrimitiveArrayDump and
                    type(references[i-1]) == InstanceDump):

                    key = self.references[references[i-2].id].ascii_data()
                    value = self.references[references[i].id].ascii_data()

                    if key.strip() != b'' and value.strip() != b'':
                        if last_item == None or last_item != key:
                            last_item = value
                            if key not in self.variables.keys():
                                self.variables[key] = [value]
                            else:
                                self.variables[key].append(value)

    '''
    
    Type 2

    The block structure is the following for variables:

    Key as PrimitiveArrayDump (bytes) -> Key as PrimitiveArrayDump (string) -> InstanceDump -> InstanceDump -> Value as PrimitiveArrayDump (bytes) -> Value as PrimitiveArrayDump (string)

    '''
    def parse_type_two_references(self, heap_dump, mx, p, references):
        for i in range(len(references)):
            el = references[i]
            if mx is not None and i > mx:
                break
            if isinstance(el, ClassDump):
                self.classes[el.id] = JavaClass(el.id, self.strings[self.class_name_ids[el.id]],
                                                el.super_class_id,
                                                el.instance_fields, el.static_fields, el.constants_pool)
            elif isinstance(el, InstanceDump):
                self.references[el.id] = InstanceReference.build_from_instance_dump(
                    self.strings,
                    self.classes[el.class_object_id],
                    el
                )
            elif isinstance(el, ObjectArrayDump):
                self.references[el.id] = ObjectArrayReference(el.id, el.elements)
            elif isinstance(el, PrimitiveArrayDump):
                self.references[el.id] = PrimitiveArrayReference(el.id, el.element_type, p.type_size(el.element_type), el.size, el.data)
                if (type(references[i-1]) == PrimitiveArrayDump and
                    type(references[i-2]) == InstanceDump and
                    type(references[i-3]) == InstanceDump and
                    type(references[i-4]) == PrimitiveArrayDump):

                    key = self.references[references[i-4].id].ascii_data()
                    value = self.references[references[i].id].ascii_data()

                    if key.strip() != b'' and value.strip() != b'':
                        if key not in self.variables.keys():
                            self.variables[key] = [value]
                        else:
                            self.variables[key].append(value)