from lib.config import config
from lib.Base import CBaseObject

class CConfigEvalWrapper(CBaseObject):
    def __init__(self, path = []):
        self.__path = path
    
    def __getattr__(self, attr):
        path = self.__path + [attr]
        pathStr = '/' + '/'.join(path)
        if pathStr in config:
            return config[pathStr]
        else:
            return CConfigEvalWrapper(path)
