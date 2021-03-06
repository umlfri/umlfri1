from .identifier import Identifier

class Base(object):
    def __init__(self, name, parent):
        if name is None:
            self.__identifier = None
        else:
            self.__identifier = Identifier(name)
        self.__parent = parent
        
        if self.__parent is not None:
            self.__parent._addChild(self)
    
    @property
    def name(self):
        if self.__identifier is None:
            return None
        else:
            return self.__identifier.default
    
    @property
    def identifier(self):
        return self.__identifier
    
    @property
    def fqn(self):
        sn = self.name
        if self.__parent:
            pfqn = self.__parent.fqn
            
            if pfqn is not None:
                if sn is None:
                    return pfqn
                else:
                    return pfqn + "::" + sn
            else:
                return sn
        else:
            return sn
    
    @property
    def parent(self):
        return self.__parent
    
    @property
    def typeName(self):
        return self.__class__.__name__
    
    def validate(self):
        pass
    
    def _link(self, builder):
        pass
    
    def __str__(self):
        return str(self.fqn)
    
    def __repr__(self):
        return '<%s %s>'%(self.__class__.__name__, self.fqn)
    
    def __cmp__(self, other):
        return cmp(self.name, other.name)
    
    def __eq__(self, other):
        return self is other
    
    def __ne__(self, other):
        return self is not other
