import os
import os.path
import re
from lib.Exceptions.DevException import *
from Type import CDomainType
from lib.config import config
from lib.consts import METAMODEL_NAMESPACE
from Parser import CDomainParser
from Joiner import CDomainJoiner
from lib.Exceptions import DomainFactoryError
from lib.Generic import CGenericFactory

class CDomainFactory(CGenericFactory):
    '''
    Factory to create Domains
    
    @ivar domains: dictionary with domain names as keys and domain types as values
    '''
    IDENTIFIER = re.compile('[a-zA-Z][a-zA-Z0-9_]*')
    
    def Load(self, root):
        '''
        Load XML from given path
        '''
        
        if root.tag == METAMODEL_NAMESPACE + 'Domain':
            self.__LoadDomain(root)
        
    def __LoadDomain(self, root, name=None):
        '''
        Load Domain from root node
        
        @param root: node <Domain>
        
        @param name: name of parent domain, None for root domain
        @type name: str  
        '''
        if name is None:
            name = root.get('id')
            if self.IDENTIFIER.match(name) is None:
                raise DomainFactoryError('Name "%s" is not valid' %name)
            if name in self.domains:
                raise DomainFactoryError('Duplicate domain identifier "%s"' % name)
        elif root.get('id') is not None:
            raise DomainFactoryError('Domain id not allowed in nested domain "%s"' % name)
        
        obj = CDomainType(name, self)
        self._AddType(name, obj)
        
        for node in root:
            if node.tag == METAMODEL_NAMESPACE + 'Import':
                if '.' in node.get('id'):
                    raise DomainFactoryError('Explicit import of local domain not allowed in "%s"' % name)
                obj.AppendImport(node.get('id'))
            
            elif node.tag == METAMODEL_NAMESPACE + 'Attribute': 
                self.__LoadAttribute(obj, node)
            
            elif node.tag == METAMODEL_NAMESPACE + 'Parse':
                obj.AppendParser(CDomainParser(**dict(node.items())))
            elif node.tag == METAMODEL_NAMESPACE + 'Join':
                obj.AppendJoiner(CDomainJoiner(**dict(node.items())))                
                
            else:
                raise DomainFactoryError('Unknown Section "%s" in domain "%s"'%(name, section.tag, ))
            
        
    
    def __LoadAttribute(self, obj, attribute):
        '''
        Load <Attribute> node of Domain
        
        @param obj: domain type to be altered
        @type obj: L{CDomainType<Type.CDomainType>}
        
        @param attribute: xml node
        '''
        id = attribute.get('id')
        if self.IDENTIFIER.match(id) is None:
            raise DomainFactoryError('Name "%s" is not valid' %id)
        type = attribute.get('type')
        default = attribute.get('default')
        if type is not None and '.' in type:
            raise DomainFactoryError('Local domain "%s" cannot be used as explicitly '
                'set type of "%s.%s"' % (type, obj.GetName(), id))
        obj.AppendAttribute(**dict(attribute.items()))
        for option in attribute:
            if option.tag == METAMODEL_NAMESPACE + 'Enum':
                obj.AppendEnumValue(id, option.text)
            
            elif option.tag == METAMODEL_NAMESPACE + 'List':
                obj.SetList(id, **self.__LoadList(option))
                ltype = obj.GetAttribute(id)['list']['type']
                if ltype == 'list':
                    raise DomainFactoryError('List of lists not supported in "%s.%s"'
                        %(obj.GetName(), id))
                elif ltype is not None and '.' in ltype:
                    raise DomainFactoryError('Local domain "%s" cannot be used as explicitly '
                        'set itemtype of "%s.%s"' % (type, obj.GetName(), id))
            elif option.tag == METAMODEL_NAMESPACE + 'Domain':
                name = obj.GetName() +'.' + id
                self.__LoadDomain(option, name)
                obj.AppendImport(name)
                at = obj.GetAttribute(id)
                attype = at['type']
                if attype is None:
                    obj.GetAttribute(id)['type'] = name
                elif attype == 'list' and ('list' not in at or at['list']['type'] is None):
                    obj.SetList(id, type = name)
                else:
                    raise DomainFactoryError('Nested Domain "%s" is not allowed '
                        'because type is explicitly set.'%(name,))
    
    def __LoadList(self, node):
        '''
        Parse <List> node of attribute
        
        @return: all the information for the list that can be read from node
        @rtype: dict
        
        @param node: <List> XML node
        @type: xml node
        '''
        
        result = dict(node.items())
        for option in node:
            if option.tag == METAMODEL_NAMESPACE + 'Parse':
                result['parser'] = CDomainParser(**dict(option.items()))
        
        return result
