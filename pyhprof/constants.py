
TAGS = {
    0x01: 'STRING',
    0x02: 'LOAD_CLASS',
    0x03: 'UNLOAD_CLASS',
    0x04: 'STACK_FRAME',
    0x05: 'STACK_TRACE',
    0x06: 'ALLOC_SITES',
    0x07: 'HEAP_SUMMARY',
    0x0A: 'START_THREAD',
    0x0B: 'END_THREAD',
    0x0C: 'HEAP_DUMP',
    0x1C: 'HEAP_DUMP_SEGMENT',
    0x2C: 'HEAP_DUMP_END',
    0x0D: 'CPU_SAMPLES',
    0x0E: 'CONTROL_SETTINGS'
}

HEAP_DUMP_SUB_TAGS = {
    0xFF : 'ROOT_UNKNOWN',
    0x01 : 'ROOT_JNI_GLOBAL',
    0x02 : 'ROOT_JNI_LOCAL',
    0x03 : 'ROOT_JAVA_FRAME',
    0x04 : 'ROOT_NATIVE_STACK',
    0x05 : 'ROOT_STICKY_CLASS',
    0x06 : 'ROOT_THREAD_BLOCK',
    0x07 : 'ROOT_MONITOR_USED',
    0x08 : 'ROOT_THREAD_OBJECT',
    0x20 : 'CLASS_DUMP',
    0x21 : 'INSTANCE_DUMP',
    0x22 : 'OBJECT_ARRAY_DUMP',
    0x23 : 'PRIMITIVE_ARRAY_DUMP'
}

OBJECT_TYPES = {
    2: 'OBJECT',
    4: 'BOOLEAN',
    5: 'CHAR',
    6: 'FLOAT',
    7: 'DOUBLE',
    8: 'BYTE',
    9: 'SHORT',
    10: 'INT',
    11: 'LONG'
}

TYPE_SIZES = {
    'BOOLEAN': 1,
    'CHAR': 2,
    'FLOAT': 4,
    'DOUBLE': 8,
    'BYTE': 1,
    'SHORT': 2,
    'INT': 4,
    'LONG': 8
}
