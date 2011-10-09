from base import IBase
from lib.Addons.Plugin.Communication.ComSpec import *
from lib.Addons.Plugin.Interface.decorators import *
from lib.Drawing.Connection import CConnection
from lib.Drawing.Diagram import CDiagram
from lib.Drawing.Element import CElement
from lib.Elements.Object import CElementObject
from lib.Connections.Object import CConnectionObject
from lib.Addons.Plugin.Interface.Classes.DomainObject import IDomainObject
from lib.Drawing import CConLabelInfo
from lib.Project.ProjectNode import CProjectNode

class IDiagram(IDomainObject):
    __cls__ = CDiagram
    
    def GetElement(him, obj):
        return him.HasElementObject(obj)
    
    def GetConnection(him, obj):
        return him.GetConnection(obj)
    
    def GetSelected(him):
        return list(him.GetSelected())
    
    def GetSelectedElements(him):
        return list(him.GetSelectedElements(True))
        
    def GetSelectedConnectionLabels(him):
        return [item for item in him.GetSelectedElements(False) if isinstance(item, CConLabelInfo)]
    
    def GetSelectedConnections(him): 
        return list(him.GetSelectedConnections())
        
    def GetSelectSquare(him):
        return him.GetSelectSquare(IBase.adapter.GetCanvas())
    
    def GetElementAtPosition(him, pos): 
        return him.GetElementAtPosition(IBase.adapter.GetCanvas(), pos)
    
    def GetElementsInRange(him, topLeft, bottomRight, includeAll = True):
        return list(him.GetElementsInRange(IBase.adapter.GetCanvas(), topLeft, bottomRight, includeAll))
    
    def GetSizeSquare(him):
        return him.GetSizeSquare(IBase.adapter.GetCanvas())
    
    def GetElements(him):
        return list(him.GetElements())
        
    def GetConnections(him):
        return list(him.GetConnections())
    
    def GetName(him):
        return him.GetName()
    
    def CreateElement(him, elementType):
        parentNode = him.GetNode()
        
        elementObject = CElementObject(elementType)
        elementVisual = CElement(him, elementObject)

        elementNode = CProjectNode(parentNode, elementObject, parentNode.GetPath() + "/" + elementObject.GetName() + ":" + elementObject.GetType().GetId())
        parentNode.AddChild(elementNode)
        
        IBase.adapter.plugin_change_object(elementVisual)
        IBase.adapter.plugin_change_visual(elementVisual)
