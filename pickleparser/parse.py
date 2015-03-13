# coding: utf-8

# $Id: $
import json
import pickle
from pickletools import genops
from pprint import pprint
from pickleparser.stubs import StubContext


excluded = [
    '__builtin__',
    'copy_reg'
]

def unpickle(data):
    for opcode, arg, pos in genops(data):
        print opcode.name, arg
        if opcode.name == "GLOBAL":
            module_name, attr_name = arg.split(' ')
            if module_name not in excluded:
                StubContext.add_global_stub(module_name, attr_name)
    with StubContext():
        return pickle.loads(data)


def jsonpickle_check(obj):
    if isinstance(obj, (list, tuple)):
        for item in obj:
            jsonpickle_check(item)
    if isinstance(obj, dict):
        maybe_object = obj.pop("py/object", None)
        if isinstance(maybe_object, unicode):
            maybe_object = maybe_object.encode("utf-8")
        if maybe_object is not None:
            module_name, attr_name = maybe_object.rsplit('.', 1)
            if module_name not in excluded:
                StubContext.add_global_stub(module_name, attr_name,
                                            with_reduce=False)
        for item in obj.values():
            jsonpickle_check(item)


def unjsonpickle(data):
    import jsonpickle
    struct = json.loads(data)
    pprint(struct)
    jsonpickle_check(struct)
    with StubContext():
        return jsonpickle.decode(data)