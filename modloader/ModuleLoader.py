from __future__ import annotations
import inspect
import sys
from typing import *


_T_Class = TypeVar("_T_Class", bound=type)
_T_Object = TypeVar("_T_Object", bound=object)


class ModuleLoader(object):
    def __init__(self, predicate: Callable[[object], bool], auto_instantiate: bool = True):
        self.__filter = predicate
        self.__autoInstantiate = auto_instantiate

    __filter: Callable[[_T_Class], bool]
    __classes: Dict[str, _T_Class | _T_Object]
    __autoInstantiate: bool

    def Load(self, module: str = None) -> Dict[str, _T_Class | _T_Object]:
        self.__classes = dict(inspect.getmembers(sys.modules[module], lambda obj: inspect.isclass(obj) and self.__filter(obj)))
        if self.__autoInstantiate:
            self._instantiate()
        return self.__classes

    def _instantiate(self):
        for key, cls in self.__classes.items():
            self.__classes[key] = cls()

    def __getitem__(self, item: str):
        if item in self.__classes.keys():
            return self.__classes[item]
        raise IndexError(f"Loader does not contains {item} module")
