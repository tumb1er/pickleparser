# coding: utf-8

# $Id: $
import sys
import types
import mock

PY3 = sys.version_info[0] >= 3


if PY3:
    builtins_module = 'builtins'
    # Выключаем C-extension для Pickle, т.к. оно использует другой способ
    # импорта.
    import pickle
    try:
        pickle.loads = pickle._loads
        pickle.load = pickle._load
    except AttributeError:
        # В Py3.3 нет C-extension
        pass
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

    def __enter__(self):
        self.p = mock.patch('%s.__import__' % builtins_module,
                            side_effect=self.import_mock)
        self.p.start()

        self.backup_modules = {}
        self.prev_context = self.__class__.context
        self.__class__.context = self

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
        if self.context and name in self.stubbed_modules:
            if name in sys.modules:
                self.backup_modules[name] = sys.modules[name]
            else:
                self.backup_modules[name] = None
            sys.modules[name] = self.stubbed_modules[name]
            return self.stubbed_modules[name]
        return orig_import(name, *args, **kwargs)

    @classmethod
    def add_global_stub(cls, module_name, attr_name, with_reduce=True):
        if module_name not in cls.stubbed_modules:
            module = types.ModuleType(module_name)
            cls.stubbed_modules[module_name] = module
        else:
            module = cls.stubbed_modules[module_name]
        if getattr(module, attr_name, None) is None:
            klass = PickleCallableStub if with_reduce else CallableStub
            attr = type(attr_name, (klass,), {"__module__" : module_name})
            setattr(module, attr_name, attr)





