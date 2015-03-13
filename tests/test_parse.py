# coding: utf-8

# $Id: $
import pickle
from unittest import TestCase
import sys

import jsonpickle

from pickleparser import unpickle, unjsonpickle
from pickleparser import StubContext


__all__ = [
    'PickleUnparseTestCase',
    'JSONPickleUnparseTestCase'
]


class Dangerous(object):
    def __init__(self, arg):
        self.arg = arg

    def __repr__(self):
        if self.arg == "true":
            raise ValueError("Dangerous")
        return super(Dangerous, self).__repr__()

    @staticmethod
    def dump_jsonpickle():
        print repr(jsonpickle.encode(Dangerous("false")))

    @staticmethod
    def dump_pickle():
        print repr(pickle.dumps(Dangerous("false")))


class UnparseTestCaseBase(object):

    def check_parcel(self, parcel):
        with StubContext():
            stub = self.unparse(parcel)
            expected = self.dumps(stub)
        self.assertEqual(parcel, expected)

    def testImportError(self):
        """ Проверяет, как загружается и пересохраняется pickle с неизвестным
        модулем внутри."""
        self.check_parcel(self.GLOBAL)

    def testSafeImport(self):
        """ Проверяет что если в pickle есть глобальный объект с известным
        классом, то при разборе pickle вместо исходного класса используется
        заглушка."""
        with self.assertRaises(ValueError):
            d = self.loads(self.COPY_REG_DANGEROUS)
            repr(d)

        with StubContext():
            d = self.unparse(self.COPY_REG_DANGEROUS)
            repr(d)

        m = sys.modules[self.__module__]
        self.assertTrue(hasattr(m, "Dangerous"))

    def testImportReconstructor(self):
        """ Проверяет загрузку и пересохранения pickle, в котором инстанцируется
        неизвестный класс с помощью copy_rec.reconstructor."""
        unknown_class = self.COPY_REG_DANGEROUS.replace("Dangerous", "Unknown")
        self.check_parcel(unknown_class)

    def testContextExit(self):
        """ Проверяет что после выхода из контекста атрибуты замененных модулей
        возвращаются на место."""

        with StubContext():
            d = self.unparse(self.COPY_REG)
            repr(d)
        with self.assertRaises(ValueError):
            d = self.loads(self.COPY_REG_DANGEROUS)
            repr(d)


class PickleUnparseTestCase(UnparseTestCaseBase, TestCase):
    COPY_REG_DANGEROUS = (
        "ccopy_reg\n_reconstructor\np0\n(ctests.test_parse\nDangerous\np1\n"
        "c__builtin__\nobject\np2\nNtp3\nRp4\n(dp5\nS'arg'\np6\nS'true'\np7\nsb.")

    COPY_REG = (
        "ccopy_reg\n_reconstructor\np0\n(ctests.test_parse\nDangerous\np1\n"
        "c__builtin__\nobject\np2\nNtp3\nRp4\n(dp5\nS'arg'\np6\nS'false'\np7\nsb.")

    GLOBAL = ("(dp0\nS'error'\np1\ncworkers.encoder\nEncodeError\n"
              "p2\n(S'test'\np3\ntp4\nRp5\ns.")

    def setUp(self):
        self.loads = pickle.loads
        self.dumps = pickle.dumps
        self.unparse = unpickle

    def testNotInContext(self):
        """ Проверяет, что после выхода из контекста, неизвестные модули
        все еще отваливаются с ImportError."""
        unknown_class = self.COPY_REG_DANGEROUS.replace(
            "tests.test_parse", "unknown.module")
        self.check_parcel(unknown_class)
        with self.assertRaises(ImportError):
            self.loads(unknown_class)


class JSONPickleUnparseTestCase(UnparseTestCaseBase, TestCase):

    GLOBAL = COPY_REG = '{"py/object": "tests.test_parse.Dangerous", "arg": "false"}'
    COPY_REG_DANGEROUS = '{"py/object": "tests.test_parse.Dangerous", "arg": "true"}'

    def setUp(self):
        self.loads = jsonpickle.decode
        self.dumps = jsonpickle.encode
        self.unparse = unjsonpickle

    def testNotInContext(self):
        """ Проверяет, что после выхода из контекста, неизвестные модули
        остаются неизвестными."""
        unknown_class = self.COPY_REG_DANGEROUS.replace(
            "tests.test_parse", "unknown.module")
        expected = self.loads(unknown_class)
        self.check_parcel(unknown_class)
        after = self.loads(unknown_class)
        self.assertDictEqual(after, expected)

