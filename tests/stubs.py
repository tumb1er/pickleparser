import pickle

import jsonpickle
import yaml


class Dangerous(object):
    def __init__(self, arg):
        self.arg = arg

    def __repr__(self):
        if self.arg == "true":
            raise ValueError("Dangerous")
        return super(Dangerous, self).__repr__()

    @staticmethod
    def dump_jsonpickle():
        print(repr(jsonpickle.encode(Dangerous("false"))))

    @staticmethod
    def dump_pickle():
        print(repr(pickle.dumps(Dangerous("false"))))

    @staticmethod
    def dump_yaml():
        print(repr(yaml.dump(Dangerous("false"))))