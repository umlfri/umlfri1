from .Decorators import params, mainthread, polymorphic

class IConnectionType(object):
    def __init__(self, connectionType):
        self.__connectionType = connectionType
    
    @property
    def uid(self):
        return self.__connectionType.GetUID()
    
    @property
    def _connectionType(self):
        return self.__connectionType
    
    def GetName(self):
        return self.__connectionType.GetId()
    
    def GetDomain(self):
        return self.__connectionType.GetDomain()
