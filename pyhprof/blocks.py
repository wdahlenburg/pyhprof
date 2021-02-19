"""Object model for elements of a Java hprof file
"""

import time
from contextlib import contextmanager

from .constants import TAGS


class BaseBlock(object):
    def __init__(self, tag, parser, record_time, start, length):
        self.tag = tag
        self.parser = parser
        self.record_time = record_time
        self.start = start
        self.length = length

    @property
    def tag_name(self):
        return TAGS.get(self.tag, 'UNKOWN')

    @property
    def timestamp(self):
        return self.parser.start_time / 1e3 + self.record_time / 1e6

    def __str__(self):
        return '%s @ %s of length %d' % (
        self.tag_name, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.timestamp)), self.length)


class GenericBlock(BaseBlock):
    pass

class StringBlock(BaseBlock):
    _id = _contents = None

    def read_contents(self):
        with self.parser.goto(self.start):
            try:
                s_id = self.parser.read_id()
                contents = self.parser.f.read(self.length - self.parser.id_size)
                contents = contents.decode('utf-8')
            except:
                contents = str(contents)
        self._id = s_id
        self._contents = contents

    @property
    def id(self):
        if self._id is None:
            self.read_contents()
        return self._id

    @property
    def contents(self):
        if self._contents is None:
            self.read_contents()
        return self._contents

    def __str__(self):
        return '%s %d %r' % (self.tag_name, self.id, self.contents)


class LoadClass(BaseBlock):
    _serial_number = _class_id = _stack_trace = _class_name_id = None

    def read_contents(self):
        with self.parser.goto(self.start):
            self._serial_number = self.parser.i4()
            self._class_id = self.parser.read_id()
            self._stack_trace = self.parser.i4()
            self._class_name_id = self.parser.read_id()

    @property
    def class_id(self):
        if self._class_id is None:
            self.read_contents()
        return self._class_id

    @property
    def class_name_id(self):
        if self._class_name_id is None:
            self.read_contents()
        return self._class_name_id


class HeapDump(BaseBlock):
    @contextmanager
    def heap_parser(self):
        from .parsers import HeapDumpParser
        with self.parser.goto(self.start):
            yield HeapDumpParser(self.parser.f, self.parser.id_size, self.length)

    def __iter__(self):
        with heap_parser(self) as hp:
            for b in hp:
                yield b


BLOCK_CLASSES_BY_TAG = {
    'STRING': StringBlock,
    'LOAD_CLASS': LoadClass,
    'HEAP_DUMP': HeapDump
}
