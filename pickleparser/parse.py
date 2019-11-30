# coding: utf-8

# $Id: $
import json
import pickle
from pickletools import genops
from yaml import nodes

from pickleparser.stubs import StubContext


excluded = [
    'builtins',
    'copy_reg'
]


__all__ = ['unpickle', 'unjsonpickle']


def unpickle(data):
    # forcing bytes for PY3
    if hasattr(data, 'encode'):
        data = data.encode('utf-8')
    # preliminary add module mocks for all GLOBAL tokens in pickled data
    for opcode, arg, pos in genops(data):
        if opcode.name == "GLOBAL":
            module_name, attr_name = arg.split(' ')
            if module_name not in excluded:
                StubContext.add_global_stub(module_name, attr_name)
    # Run import in safe context
    with StubContext():
        return pickle.loads(data)


def _jsonpickle_check(obj):
    """ Recursively checks for all possible py/object definitions."""

    if isinstance(obj, (list, tuple)):
        for item in obj:
            _jsonpickle_check(item)

    # item is a dict, so check if it's an instruction for constructing a
    # python object
    if isinstance(obj, dict):
        maybe_object = obj.pop("py/object", None)
        # ensure string type for py/object class path
        if maybe_object is not None and not isinstance(maybe_object, str):
            maybe_object = maybe_object.encode("utf-8")
        # preliminary add module mock for py/object class path definition
        if maybe_object is not None:
            module_name, attr_name = maybe_object.rsplit('.', 1)
            if module_name not in excluded:
                StubContext.add_global_stub(module_name, attr_name,
                                            with_reduce=False)
        # continue recursive check
        for item in obj.values():
            _jsonpickle_check(item)


def _yaml_check(node):
    YAML_PY_OBJECT = 'tag:yaml.org,2002:python/object:'
    if node.tag.startswith(YAML_PY_OBJECT):
        tag_suffix = node.tag[len(YAML_PY_OBJECT):]
        module_name, attr_name = tag_suffix.rsplit('.', 1)
        if module_name not in excluded:
            StubContext.add_global_stub(module_name, attr_name,
                                        with_reduce=False)
    if isinstance(node, nodes.MappingNode):
        for k, v in node.value:
            _yaml_check(k)
            _yaml_check(v)
    else:
        pass

def unjsonpickle(data):
    struct = json.loads(data)
    # scan JSON object for py/object class paths and add global stubs for them.
    _jsonpickle_check(struct)

    import jsonpickle
    # Run import in safe context
    with StubContext():
        return jsonpickle.decode(data)


def unyaml(data):
    import yaml
    loader = yaml.Loader(data)
    node = loader.get_single_node()
    _yaml_check(node)
    return yaml.load(data)
