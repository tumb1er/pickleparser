# coding: utf-8

# $Id: $
from imp import reload
import sys
import types
import mock

PY3 = sys.version_info[0] >= 3


if PY3:
    builtins_module = 'builtins'
else:
    builtins_module = '__builtin__'


orig_import = __import__


class CallableStub(object):

    def __init__(self, *args):
        self.args = args


class PickleCallableStub(CallableStub):

    def __reduce__(self):
        if hasattr(self, 'args'):
            # класс конструировался через object.__new__ + cls.__init__
            return self.__class__, self.args
        else:
            # класс похоже конструировался через meta.__new__
            # без вызова __init__
            val = object.__reduce__(self)
            return val


class StubContext(object):
    stubbed_modules = {}

    context = None

    pickle_reloaded = False

    def reload_pickle(self):
        """ Reload pickle module if not sure that pickle c-extension is
        disabled."""
        if self.__class__.pickle_reloaded:
            return

        # ensure that pickle is imported in StubContext without c-extension
        import pickle

        reload(pickle)
        self.__class__.pickle_reloaded = True

    def __enter__(self):
        self.p = mock.patch('%s.__import__' % builtins_module,
                            side_effect=self.import_mock)
        self.p.start()

        self.backup_modules = {}
        self.prev_context = self.__class__.context
        self.__class__.context = self
        self.reload_pickle()

    def __exit__(self, *args):
        # Возвращаем на место заменненные на заглушки модули.
        # Если до импорта внутри контекста модуля не было,
        # удаляем его из sys.modules
        self.__class__.context = self.prev_context
        for module_name, old in self.backup_modules.items():
            if old is not None:
                sys.modules[module_name] = old
            else:
                del sys.modules[module_name]

        self.p.stop()

    def import_mock(self, name, *args, **kwargs):
        if PY3 and name == '_pickle':
            raise ImportError("cPickle is forbidden")
        if self.context and name in self.stubbed_modules:
            self.stub_module(name)
            return self.stubbed_modules[name]
        return orig_import(name, *args, **kwargs)

    def stub_module(self, name):
        if name in self.backup_modules:
            return
        if name in sys.modules:
            self.backup_modules[name] = sys.modules[name]
        else:
            self.backup_modules[name] = None
        sys.modules[name] = self.stubbed_modules[name]

    @classmethod
    def add_global_stub(cls, module_name, attr_name=None, with_reduce=True):
        if not cls.context:
            raise RuntimeError("Called without context")
        if module_name not in cls.stubbed_modules:
            module = types.ModuleType(module_name)
            cls.stubbed_modules[module_name] = module
        else:
            module = cls.stubbed_modules[module_name]
        if attr_name and getattr(module, attr_name, None) is None:
            klass = PickleCallableStub if with_reduce else CallableStub
            attr = type(attr_name, (klass,), {"__module__" : module_name})
            setattr(module, attr_name, attr)
        cls.context.stub_module(module_name)


