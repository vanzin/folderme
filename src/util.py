# SPDX-License-Identifier: BSD-2-Clause
import jsonpickle
import os
from PyQt5 import uic


class ConfigObj:
    """
    Base class for config objects that disables serialization of "private" fields.
    """

    @classmethod
    def config_file_name(cls):
        return "{}.{}".format(cls.__module__, cls.__name__)

    def __getstate__(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def __setstate__(self, data):
        self.__init__()
        for k, v in data.items():
            setattr(self, k, v)


def init_ui(widget, src):
    path = os.path.join(os.path.dirname(__file__), "ui", src)
    uic.loadUi(path, widget)


def config_dir(create=False):
    path = os.path.join(os.environ["HOME"], ".config", "folderme")
    path = os.environ.get("FOLDERME_CONFIG", path)
    if create and not os.path.isdir(path):
        os.mkdir(path)
    return path


def _init_pickler():
    jsonpickle.set_preferred_backend("json")
    jsonpickle.set_encoder_options("json", indent=2)


def save_config(obj):
    _init_pickler()
    path = os.path.join(config_dir(create=True), obj.config_file_name())
    data = jsonpickle.encode(obj)
    with open(path, "wt", encoding="utf-8") as out:
        out.write(data)


def load_config(cls):
    path = os.path.join(config_dir(), cls.config_file_name())
    if os.path.isfile(path):
        return jsonpickle.decode(open(path).read())
    return cls()
