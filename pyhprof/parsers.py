"""Parsers for the contents of a binary Java hprof file.
Specification in: https://java.net/downloads/heap-snapshot/hprof-binary-format.html
"""

from __future__ import division

import os
import struct
from contextlib import contextmanager

from .constants import TAGS, HEAP_DUMP_SUB_TAGS, OBJECT_TYPES, TYPE_SIZES
from .blocks import BLOCK_CLASSES_BY_TAG, GenericBlock
from .heap_blocks import HEAP_BLOCK_CLASSES_BY_TAG

class BaseParser(object):

    def __init__(self, f):
        self.f = f

    def close(self):
        self.f.close()
        self.f = None

    def read(self, n):
        b = self.f.read(n)
        if len(b) != n:
            raise EOFError()
        return b

    def seek(self, n):
        self.f.seek(n, os.SEEK_CUR)

    def u1(self):
        return self.read(1)

    def i1(self):
        return ord(self.u1())

    def read_struct(self, f, n=None):
        if n is None:
            n = struct.calcsize(f)
        return struct.unpack(f, self.read(n))[0]

    def i2(self):
        return self.read_struct('>H', 2)

    def i4(self):
        return self.read_struct('>I', 4)

    def i8(self):
        return self.read_struct('>Q', 8)

    def set_id_size(self, id_size):
        self.id_size = id_size
        self.read_id = self.i4 if self.id_size == 4 else self.i8

    def read_value_type(self):
        return OBJECT_TYPES[self.i1()]

    def read_bool(self):
        return self.i1()

    def read_char(self):
        return self.i2()

    def read_float(self):
        return self.read_struct('f', 4)

    def read_double(self):
        return self.read_struct('d', 8)

    def read_value(self, tp):
        if tp == 'OBJECT':
            return self.read_id()
        elif tp == 'BOOLEAN':
            return self.read_bool()
        elif tp == 'CHAR':
            return self.read_char()
        elif tp == 'FLOAT':
            return self.read_float()
        elif tp == 'DOUBLE':
            return self.read_double()
        elif tp == 'BYTE':
            return self.i1()
        elif tp == 'SHORT':
            return self.i2()
        elif tp == 'INT':
            return self.i4()
        elif tp == 'LONG':
            return self.i8()
        else:
            raise ValueError("Unkown tp %r" % (tp,))

    def type_size(self, tp):
        if tp == 'OBJECT':
            return self.id_size
        else:
            return TYPE_SIZES[tp]

    def __iter__(self):
        while True:
            try:
                b = self.read_next_block()
            except EOFError:
                break
            if b is None:
                break
            yield b


class HProfParser(BaseParser):

    def __init__(self, f):
        super(HProfParser, self).__init__(f)
        self.read_header()

    def read_header(self):
        f = b""
        while True:
            u1 = self.u1()
            if not u1 != b'\0':
                break
            f += u1
        self.format = f
        self.set_id_size(self.i4())
        self.start_time = self.i8()

    def read_next_block(self):
        tag = ord(self.u1())
        tag_name = TAGS.get(tag, 'UNKOWN')
        record_time = self.i4()
        length = self.i4()
        start = self.f.tell()
        self.seek(length)
        block = BLOCK_CLASSES_BY_TAG.get(tag_name, GenericBlock)(tag, self, record_time, start, length)
        return block

    @contextmanager
    def goto(self, goto=None):
        start = self.f.tell()
        if goto is not None:
            self.f.seek(goto)
        yield
        self.f.seek(start)


class HeapDumpParser(BaseParser):

    def __init__(self, f, id_size, length=None):
        super(HeapDumpParser, self).__init__(f)
        self.set_id_size(id_size)
        self.length = length
        self.position = 0

    def check_position_in_bound(self):
        assert self.length is None or self.position <= self.length

    def read(self, n):
        content = super(HeapDumpParser, self).read(n)
        self.position += n
        self.check_position_in_bound()
        return content

    def seek(self, n):
        super(HeapDumpParser, self).seek(n)
        self.position += n
        self.check_position_in_bound()

    def read_next_block(self):
        if self.position == self.length:
            return
        tag = self.u1()
        if ord(tag) not in HEAP_DUMP_SUB_TAGS.keys():
            return
        if HEAP_DUMP_SUB_TAGS[ord(tag)] == 'HEAP_DUMP_END':
            return
        return HEAP_BLOCK_CLASSES_BY_TAG[HEAP_DUMP_SUB_TAGS[ord(tag)]].parse(self)
