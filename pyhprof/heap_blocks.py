
class BaseHeapDumpBlock(object):
    
    def __init__(self, id):
        self.id = id
        
class BaseOnlyIdHeapDumpBlock(BaseHeapDumpBlock):
    
    @classmethod
    def parse(cls, p):
        return cls(p.read_id())
        
class BaseThreadHeapDumpBlock(BaseHeapDumpBlock):
    
    def __init__(self, id, thread_serial_number):
        super(BaseThreadFrameHeadDumpBlock, self).__init__(id)
        self.thread_serial_number = thread_serial_number

    @classmethod
    def parse(cls, p):
        return cls(p.read_id(), p.i4())         

class BaseThreadFrameHeadDumpBlock(BaseThreadHeapDumpBlock):
    
    def __init__(self, id, thread_serial_number, frame_number):
        super(BaseThreadFrameHeadDumpBlock, self).__init__(id, thread_serial_number)
        self.frame_number = frame_number
        
    @classmethod
    def parse(cls, p):
        return cls(p.read_id(), p.i4(), p.i4())    
        
class RootUnkown(BaseOnlyIdHeapDumpBlock):

    pass
    
class RootJniGlobal(BaseHeapDumpBlock):
    
    def __init__(self, id, jni_global_ref):
        super(RootJniGlobal, self).__init__(id)
        self.jni_global_ref = jni_global_ref
        
    @classmethod
    def prase(cls, p):
        return cls(p.read_id(), p.read_id())
                
class RootJniLocal(BaseThreadFrameHeadDumpBlock):
    
    pass
    
class RootJavaFrame(BaseThreadFrameHeadDumpBlock):    
    
    pass
    
class RootNativeStack(BaseThreadHeapDumpBlock):
    
    pass
    
class RootStickyClass(BaseOnlyIdHeapDumpBlock):
    
    pass
    
class RootThreadBlock(BaseThreadHeapDumpBlock):
    
    pass
    
class RootMonitorUsed(BaseOnlyIdHeapDumpBlock):
    
    pass
    
class RootThreadObject(BaseThreadHeapDumpBlock):
    
    def __init__(self, id, thread_serial_number, stack_trace_serial_number):
        super(BaseThreadFrameHeadDumpBlock, self).__init__(id, thread_serial_number)
        self.stack_trace_serial_number = stack_trace_serial_number
        
    @classmethod
    def parse(cls, p):
        return cls(p.read_id(), p.i4(), p.i4())
        
class ClassDump(BaseHeapDumpBlock):
    
    def __init__(self,
                 id,
                 stack_trace_serial_number,
                 super_class_id,
                 class_loader_id,
                 signers_object_id,
                 protection_domain_object_id,
                 reserved1,
                 reserved2,
                 instance_size,
                 constants_pool,
                 static_fields,
                 instance_fields):
        super(ClassDump, self).__init__(id)
        vars(self).update(locals())
        del self.self
        
    @classmethod
    def parse(cls, p):
        id = p.read_id()
        stack_trace_serial_number = p.i4()
        super_class_id = p.read_id()
        class_loader_id = p.read_id()
        signers_object_id = p.read_id()
        protection_domain_object_id = p.read_id()
        reserved1 = p.read_id()
        reserved2 = p.read_id()
        instance_size = p.i4()
        constants = [cls.read_constant(p) for _ in xrange(p.i2())]
        static_fields = [cls.read_static_field(p) for _ in xrange(p.i2())]
        instance_fields = [cls.read_instance_field(p) for _ in xrange(p.i2())]
        return cls(id, stack_trace_serial_number, super_class_id, class_loader_id, signers_object_id, protection_domain_object_id,
                   reserved1, reserved2, instance_size, constants, static_fields, instance_fields)
                   
    @classmethod
    def read_constant(cls, p):
        pool_index = p.i2()
        tp = p.read_value_type()
        value = p.read_value(tp)
        return [pool_index, tp, value]
        
    @classmethod
    def read_static_field(cls, p):
        name_id = p.read_id()
        tp = p.read_value_type()
        value = p.read_value(tp)
        return [name_id, tp, value]
        
    @classmethod
    def read_instance_field(cls, p):
        name_id = p.read_id()
        tp = p.read_value_type()
        return [name_id, tp]
       
class InstanceDump(BaseHeapDumpBlock):
    
    def __init__(self, id, stack_trace_serial_number, class_object_id, bytes):
        self.id = id
        self.stack_trace_serial_number = stack_trace_serial_number
        self.class_object_id = class_object_id
        self.bytes = bytes
        
    @classmethod
    def parse(cls, p):
        id = p.read_id()
        stack_trace_serial_number = p.i4()
        class_object_id = p.read_id()
        n_bytes = p.i4()
        bytes = p.read(n_bytes)
        return cls(id, stack_trace_serial_number, class_object_id, bytes)
        
class ObjectArrayDump(BaseHeapDumpBlock):
    
    def __init__(self, id, stack_trace_serial_number, array_class_object_id, elements):
        self.id = id
        self.stack_trace_serial_number = stack_trace_serial_number
        self.array_class_object_id = array_class_object_id
        self.elements = elements
        
    @classmethod
    def parse(cls, p):
        id = p.read_id()
        stack_trace_serial_number = p.i4()
        n_elements = p.i4()
        array_class_object_id = p.read_id()
        elements = [p.read_id() for _ in xrange(n_elements)]
        return cls(id, stack_trace_serial_number, array_class_object_id, elements)
        
class PrimitiveArrayDump(BaseHeapDumpBlock):
    
    def __init__(self, id, stack_trace_serial_number, element_type, size):
        self.id = id
        self.stack_trace_serial_number = stack_trace_serial_number
        self.element_type = element_type
        self.size = size
        
    @classmethod
    def parse(cls, p):
        id = p.read_id()
        stack_trace_serial_number = p.i4()
        size = p.i4()
        element_type = p.read_value_type()
        p.seek(p.type_size(element_type) * size)
        return cls(id, stack_trace_serial_number, element_type, size)
    
HEAP_BLOCK_CLASSES_BY_TAG = {
    'ROOT_UNKNOWN' : RootUnkown,
    'ROOT_JNI_GLOBAL' : RootJniGlobal,
    'ROOT_JNI_LOCAL' : RootJniLocal,
    'ROOT_JAVA_FRAME' : RootJavaFrame,
    'ROOT_NATIVE_STACK' : RootNativeStack,
    'ROOT_STICKY_CLASS' : RootStickyClass,
    'ROOT_THREAD_BLOCK' : RootThreadBlock,
    'ROOT_MONITOR_USED' : RootMonitorUsed,
    'ROOT_THREAD_OBJECT' : RootThreadObject,
    'CLASS_DUMP' : ClassDump,
    'INSTANCE_DUMP' : InstanceDump,
    'OBJECT_ARRAY_DUMP' : ObjectArrayDump,
    'PRIMITIVE_ARRAY_DUMP' : PrimitiveArrayDump    
}