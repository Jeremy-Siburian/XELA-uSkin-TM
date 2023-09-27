from typing import Any
import yaml
import os

def e2t(e:Exception) -> str:
    return f"{type(e).__name__}: {e}"

def import_param(path, yamlfile):
    # settings
    with open(os.path.join(path, yamlfile)) as file:
        params = yaml.safe_load(file)
    return params


class MyData(object):
    def __init__(self) -> None:
        self.__data:Any = {}
    def newdata(self,data:Any) -> None:
        self.__data = data
    def getdata(self) -> Any:
        return self.__data

class Bit(object):
    def __init__(self,value:bool=False) -> None:
        self.__value = value
    def toggle(self) -> None:
        self.__value = not self.__value
    def on(self) -> None:
        self.__value = True
    def off(self) -> None:
        self.__value = False
    def __bool__(self) -> bool:
        return self.__value

class Color:
    BLACK     = '\033[30m'
    RED       = '\033[31m'
    GREEN     = '\033[32m'
    YELLOW    = '\033[33m'
    BLUE      = '\033[34m'
    PURPLE    = '\033[35m'
    CYAN      = '\033[36m'
    WHITE     = '\033[37m'
    END       = '\033[0m'
    BOLD      = '\038[1m'
    UNDERLINE = '\033[4m'
    INVISIBLE = '\033[08m'
    REVERSE   = '\033[07m'
