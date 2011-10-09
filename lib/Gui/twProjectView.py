from lib.Depend.gtk2 import gobject
from lib.Depend.gtk2 import gtk

from common import CWidget
from lib.Project import CProject, CProjectNode
from lib.Elements import CElementObject
from lib.Drawing import CElement, CDiagram
from lib.Exceptions.UserException import *
from lib.Drawing.Canvas.GtkPlus import PixmapFromPath

from common import  event
import common


class CtwProjectView(CWidget):
    name = 'twProjectView'
    widgets = ('twProjectView',
               
               'menuTreeElement',
               'mnuTreeAddDiagram', 'mnuTreeAddElement','mnuTreeDelete', 'mnuTreeFindInDiagrams',
               'mnuTreeSetAsDefault', 'mnuTreeUnSetDefault','mnuOpenSpecification'
              )
    
    __gsignals__ = {
        'selected_diagram':  (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)), 
        'selected-item-tree':  (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, )),
        'add-element':   (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'create-diagram':   (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING, )),
        'repaint':  (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'close-diagram': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'selected_diagram_and_select_element': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)), 
        'show_frmFindInDiagram': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,)),
        'open-specification': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, )),
    }
    
    def __init__(self, app, wTree):
        CWidget.__init__(self, app, wTree)
        
        self.TreeStore = gtk.TreeStore(str, gtk.gdk.Pixbuf, str, object)
        self.EventButton = (0,0)
        
        self.Column = gtk.TreeViewColumn(_('Elements'))
        self.twProjectView.append_column(self.Column)
        self.twProjectView.set_reorderable(True)
        
        self.StrRenderer = gtk.CellRendererText()
        self.PbRenderer = gtk.CellRendererPixbuf()
        
        self.Column.pack_start(self.PbRenderer, False)
        self.Column.add_attribute(self.PbRenderer, 'pixbuf', 1)
        self.Column.pack_start(self.StrRenderer, True)
        self.Column.add_attribute(self.StrRenderer, 'text', 0)
            
        
        self.twProjectView.set_model(self.TreeStore)
        self.twProjectView.get_selection().set_mode(gtk.SELECTION_SINGLE)
        
        self.TARGETS = [
        ('MY_TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0),
        ('text/plain', 0, 1),
        ('TEXT', 0, 2),
        ('STRING', 0, 3),
        ]
        
        self.twProjectView.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, self.TARGETS, gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE | gtk.gdk.ACTION_COPY)
        self.twProjectView.enable_model_drag_dest(self.TARGETS, gtk.gdk.ACTION_DEFAULT)
    
    def ClearProjectView(self):
        self.TreeStore.clear()
    
    def Redraw(self, firstTime = False):
        """
        This function load ProjectTree Add menu from enabled diagrams and options of elements
        
        """
        for item in self.mnuTreeAddDiagram.get_children():
            self.mnuTreeAddDiagram.remove(item)
        
        for item in self.mnuTreeAddElement.get_children():
            self.mnuTreeAddElement.remove(item)
        
        for item in self.application.GetProject().GetMetamodel().GetElementFactory().IterTypes():
            if item.GetOptions().get('DirectAdd', False):
                newItem = gtk.ImageMenuItem(item.GetId())
                self.mnuTreeAddElement.append(newItem)
                newItem.connect("activate", self.on_mnuAddElement_activate, item.GetId())
                img = gtk.Image()
                img.set_from_pixbuf(PixmapFromPath(self.application.GetProject().GetMetamodel().GetStorage(), self.application.GetProject().GetMetamodel().GetElementFactory().GetElement(item.GetId()).GetIcon()))
                newItem.set_image(img)
                img.show()
                newItem.show()
        
        for diagram in self.application.GetProject().GetMetamodel().GetDiagrams():
            mi = gtk.ImageMenuItem(diagram)
            
            img = gtk.Image()
            img.set_from_pixbuf(PixmapFromPath(self.application.GetProject().GetMetamodel().GetStorage(), self.application.GetProject().GetMetamodel().GetDiagramFactory().GetDiagram(diagram).GetIcon()))
            img.show()
            
            mi.set_image(img)
            mi.show()   
            mi.connect("activate", self.on_mnuTreeAddDiagram_activate, diagram)
            self.mnuTreeAddDiagram.append(mi)
        
        project = self.application.GetProject()
        root = project.GetRoot()
        self.TreeStore.clear()
        parent = self.TreeStore.append(None)
        self.TreeStore.set(parent, 0, root.GetName(), 1, PixmapFromPath(self.application.GetProject().GetMetamodel().GetStorage(), root.GetObject().GetType().GetIcon()), 2, root.GetType(), 3, root)
        self.__DrawTree(root, parent)
        if firstTime:
            self.twProjectView.expand_to_path(self.TreeStore.get_path(parent))

    def __DrawTree(self, root, parent):
        
        for diagram in root.GetDiagrams():
            novy = self.TreeStore.append(parent)
            self.TreeStore.set(novy, 0, diagram.GetName() , 1, PixmapFromPath(self.application.GetProject().GetMetamodel().GetStorage(), diagram.GetType().GetIcon()), 2, '=Diagram=',3,diagram)
        
        for node in root.GetChilds():
            novy = self.TreeStore.append(parent)
            self.TreeStore.set(novy, 0, node.GetName() , 1, PixmapFromPath(self.application.GetProject().GetMetamodel().GetStorage(), node.GetObject().GetType().GetIcon()), 2, node.GetType(),3,node)
            self.__DrawTree(node, novy)
            
         

    def get_iter_from_path(self, model, root, path):
        chld = root
        
        i = path.split('/')[0]
        j,k = i.rsplit(':',1)
        name, type = model.get(root, 0, 2)
        
        if len(path.split('/')) == 1 and name == j and type == k:
            return root
            
        if name == j and type == k:
            for i in path.split('/')[1:]:
                j, k = i.rsplit(':',1)
                for id in xrange(model.iter_n_children(root)):
                    chld = model.iter_nth_child(root, id)
                    name, type = model.get(chld, 0, 2)
                    
                    if k == "=Diagram=":
                        return root
                        
                    if name == j and type == k:
                        break 
                        
                root = chld
            return root
        else:
            raise ProjectError("BadPath4")


    def get_iters_from_path(self, model, root, path):
        chld = root
        iter = []
        
        i = path.split('/')[0]
        j,k = i.rsplit(':',1)
        name, type = model.get(root, 0, 2)
        endName, endType = path.split('/')[-1].rsplit(':', 1)
        
        if len(path.split('/')) == 1 and name == j and type == k:
            return [root]
        
        if name == j and type == k:
            def rekurzia(root,path):
                j, k = path.split('/')[0].rsplit(':',1)
                for id in xrange(model.iter_n_children(root)):
                    chld = model.iter_nth_child(root, id)
                    name, type = model.get(chld, 0, 2)
                    
                    if k == "=Diagram=":
                        iter.append(root) 
                    
                    if name == j and type == k:
                        if len(path.split('/')) > 1:
                            rekurzia(chld,path.split('/',1)[1])
                        else:
                            iter.append(chld)
            
            rekurzia(root,path.split('/',1)[1])                        

        else:
            raise ProjectError("BadPath4")
        return iter
        
        
    def get_diagrams_iter_from_path(self, model, root, path):
        chld = root
        diagrams = []
        i = path.split('/')[0]
        j,k = i.rsplit(':',1)
        name, type = model.get(root, 0, 2)
        if name == j and type == k:
            for i in path.split('/')[1:]:
                j, k = i.rsplit(':',1)
                for id in xrange(model.iter_n_children(root)):
                    chld = model.iter_nth_child(root, id)
                    name, type = model.get(chld, 0, 2)
                    
                    if k == "=Diagram=" and j == name:
                        diagrams.append(chld)
                root = chld
        else:
            raise ProjectError("BadPath5")
        return diagrams
    
    
    def ShowElement(self,Element):
        object = Element.GetObject()
        for i in self.get_iters_from_path(self.twProjectView.get_model(),self.twProjectView.get_model().get_iter_root() ,object.GetPath()):
            node = self.twProjectView.get_model().get(i,3)[0]
            if object is node.GetObject():
                iter = i
                break
        else:
            return
        self.twProjectView.expand_to_path(self.TreeStore.get_path(iter))
        self.twProjectView.get_selection().select_iter(iter)
        self.twProjectView.scroll_to_cell(self.TreeStore.get_path(iter))  
    
    def ShowDiagram(self, diagram):
        for i in self.get_iters_from_path(self.twProjectView.get_model(),self.twProjectView.get_model().get_iter_root() ,diagram.GetPath()):
            diagram = self.twProjectView.get_model().get(i,3)[0]
            if diagram is diagram:
                iter = i
                break
        self.twProjectView.expand_to_path(self.TreeStore.get_path(iter))
        self.twProjectView.get_selection().select_iter(iter)
                    
    
    def AddElement(self, element, diagram, parentElement = None):
        if parentElement is None:
            path = diagram.GetPath()
        else:
            path = parentElement.GetPath()

        parent = self.application.GetProject().GetNode(path)
        node = CProjectNode(parent, element, parent.GetPath() + "/" + element.GetName() + ":" + element.GetType().GetId())
        self.application.GetProject().AddNode(node, parent)
        novy = self.TreeStore.append(self.get_iter_from_path(self.twProjectView.get_model(), self.twProjectView.get_model().get_iter_root() ,path))
        self.TreeStore.set(novy, 0, element.GetName() , 1, PixmapFromPath(self.application.GetProject().GetMetamodel().GetStorage(), element.GetType().GetIcon()), 2, element.GetType().GetId(),3,node)
        self.twProjectView.get_selection().select_iter(novy)
        self.emit('selected-item-tree',self.twProjectView.get_model().get(novy,3)[0])
        self.twProjectView.scroll_to_cell(self.TreeStore.get_path(novy))        
        
        
    def AddDiagram(self, diagram):
        iter = self.twProjectView.get_selection().get_selected()[1]
        if iter is None:
            iter = self.twProjectView.get_model().get_iter_root()
            self.twProjectView.get_selection().select_iter(iter)
        model = self.twProjectView.get_model()
        
        if model.get(iter,2)[0] == "=Diagram=":
            iter = model.iter_parent(iter)
        node = model.get(iter,3)[0]
        diagram.SetPath(node.GetPath() + "/" + diagram.GetName() + ":=Diagram=")
        node.AddDiagram(diagram)
        novy = self.TreeStore.insert(iter,len(node.diagrams)-1)
        self.TreeStore.set(novy, 0, diagram.GetName() , 1, PixmapFromPath(self.application.GetProject().GetMetamodel().GetStorage(), diagram.GetType().GetIcon()), 2, '=Diagram=',3,diagram)
        path = self.TreeStore.get_path(novy)
        self.twProjectView.expand_to_path(path)
        self.twProjectView.get_selection().select_iter(novy)
        self.emit('selected-item-tree',self.twProjectView.get_model().get(novy,3)[0])
        self.twProjectView.scroll_to_cell(self.TreeStore.get_path(novy))        
        
    
    def UpdateElement(self, object):
        if isinstance(object, CElementObject):
            for iter in self.get_iters_from_path(self.twProjectView.get_model(),self.twProjectView.get_model().get_iter_root() ,object.GetPath()):
                node = self.twProjectView.get_model().get(iter,3)[0]
                if object is node.GetObject():
                    break

            node.Change()
            model = self.twProjectView.get_model()
            self.TreeStore.set_value(iter, 0, object.GetName())

        if isinstance(object, CDiagram):
            for iter in self.get_iters_from_path(self.twProjectView.get_model(),self.twProjectView.get_model().get_iter_root() ,object.GetPath()):
                node = self.twProjectView.get_model().get(iter,3)[0]
                if object is node:
                    break
                parent = node
            
            if parent == object:
                node.SetPath(parent.GetPath().split('/')[0] + '/' + object.GetName() + ":=Diagram=")
            else:
                node.SetPath(parent.GetPath() + '/' + object.GetName() + ":=Diagram=")
            
            model = self.twProjectView.get_model()
            self.TreeStore.set_value(iter, 0, object.GetName())
    
    
    @event("twProjectView","button-press-event")
    def button_clicked(self, widget, event):
        self.EventButton = (event.button, event.time) 
        
    @event("mnuOpenSpecification","activate")
    def on_mnuOpenSpecification_activate(self,widget):
        iter = self.twProjectView.get_selection().get_selected()[1]
        node=self.twProjectView.get_model().get(iter,3)[0]
        self.emit('selected-item-tree',node)
        self.emit('open-specification',node.GetObject())
    
    @event("twProjectView", "row-activated")
    def on_twProjectView_set_selected(self, treeView, path, column):
        model = self.twProjectView.get_model()
        iter =  model.get_iter(path)
        if model.get(iter,2)[0] == "=Diagram=":
            diagram = model.get(iter,3)[0]
            if diagram is None:
                raise ProjectError("Diagram is None.")
            else:
                self.emit('selected_diagram',diagram)
    
    @event("twProjectView", "cursor-changed")
    def on_twProjectView_change_selection(self, treeView):
        
        iter = treeView.get_selection().get_selected()[1]
        if iter is None:
            return
        model = self.twProjectView.get_model()
        if model.get(iter,2)[0] == "=Diagram=":
            self.mnuTreeFindInDiagrams.set_sensitive(False)
            self.mnuTreeSetAsDefault.set_sensitive(True)
            self.mnuTreeUnSetDefault.set_sensitive(True)
            default = model.get(iter,3)[0] in self.application.GetProject().GetDefaultDiagrams()
            self.mnuTreeSetAsDefault.set_property("visible", not default)
            self.mnuTreeUnSetDefault.set_property("visible", default)
        else:
            self.mnuTreeFindInDiagrams.set_sensitive(True)
            self.mnuTreeSetAsDefault.set_sensitive(False)
            self.mnuTreeUnSetDefault.set_sensitive(False)
        if self.EventButton[0] == 3:
            self.mnuTreeDelete.set_sensitive(len(treeView.get_model().get_path(iter)) > 1)
            self.menuTreeElement.popup(None,None,None,self.EventButton[0],self.EventButton[1])
        
        self.emit('selected-item-tree',treeView.get_model().get(iter,3)[0])
            
    
    def on_mnuAddElement_activate(self, widget, element):
        self.emit('add-element', element)
    
    def on_mnuTreeAddDiagram_activate(self, widget, diagramId):
        self.emit('create-diagram', diagramId)
    
    def RemoveFromArea(self,node):
        for i in node.GetDiagrams():
            self.emit('close-diagram',i)
            
        for j in node.GetChilds():
            self.RemoveFromArea(j)

        for d in self.application.GetProject().GetDiagrams():
            d.DeleteObject(node.GetObject())
    
    
    def DeleteElement(self, elementObject):
        iter = self.twProjectView.get_model().get_iter_root()
        
        if elementObject is self.twProjectView.get_model().get(iter,3)[0].GetObject():
            return
        
        for i in self.get_iters_from_path(self.twProjectView.get_model(),self.twProjectView.get_model().get_iter_root() ,elementObject.GetPath()):
            node = self.twProjectView.get_model().get(i,3)[0]
            if elementObject is node.GetObject():
                break

        self.TreeStore.remove(i)
        self.RemoveFromArea(node)
        self.application.GetProject().RemoveNode(node)
    
    @event("mnuTreeDelete","activate")
    def on_mnuTreeDelete_activate(self, menuItem):
        iter = self.twProjectView.get_selection().get_selected()[1]
        self.twProjectView.get_selection().select_iter(self.twProjectView.get_model().iter_parent(iter))
        self.emit('selected-item-tree',self.twProjectView.get_model().get(self.twProjectView.get_model().iter_parent(iter),3)[0])
        model = self.twProjectView.get_model()
        if model.get(iter,2)[0] != "=Diagram=":
            node = model.get(iter,3)[0]
            self.TreeStore.remove(iter)
            self.RemoveFromArea(node)
            self.application.GetProject().RemoveNode(node)
            self.emit('repaint')
        else:
            diagram = model.get(iter,3)[0]
            itr = model.iter_parent(iter)
            node = model.get(itr,3)[0]
            node.RemoveDiagram(diagram)
            self.TreeStore.remove(iter)
            self.emit('close-diagram',diagram)
        
    @event("mnuTreeFindInDiagrams","activate")
    def on_mnuTreeFindInDiagrams(self, menuItem):
        iter = self.twProjectView.get_selection().get_selected()[1]
        model = self.twProjectView.get_model()
        node = model.get(iter,3)[0]
        cnt = len(list(node.GetAppears()))
        if cnt == 0:
            pass
        elif cnt == 1:
            self.emit('selected_diagram_and_select_element',list(node.GetAppears())[0], node.GetObject())
        elif cnt > 1:
            self.emit('show_frmFindInDiagram', list(node.GetAppears()), node.GetObject())

    def GetSelectedDiagram(self):
        iter = self.twProjectView.get_selection().get_selected()[1]
        if iter == None:
            return None
        node = self.twProjectView.get_model().get(iter,3)[0]
        if isinstance(node,CDiagram):
            return node
        else:
            return None
        
    def GetSelectedNode(self):
        iter = self.twProjectView.get_selection().get_selected()[1]
        if iter == None:
            return None
        node = self.twProjectView.get_model().get(iter,3)[0]
        if isinstance(node,CProjectNode):
            return node
        else:
            return None
        
    def GetRootNode(self):
        iter = self.twProjectView.get_model().get_iter_root()
        self.twProjectView.get_selection().select_iter(iter)
        node = self.twProjectView.get_model().get(iter,3)[0]
        return node
        
    @event("twProjectView","drag-data-get")
    def on_drag_data_get(self, widget,drag_context, selection_data, info, time):
        treeselection = widget.get_selection()
        model, iter = treeselection.get_selected()
        data = model.get_value(iter, 0)
        selection_data.set(selection_data.target, 8, data)

        
    
    def CheckSanity(self, model, iter_to_copy, target_iter):
        path_of_iter_to_copy = model.get_path(iter_to_copy)
        path_of_target_iter = model.get_path(target_iter)
        if path_of_target_iter[0:len(path_of_iter_to_copy)] == path_of_iter_to_copy:
            return False
        elif len(path_of_target_iter) < 2:
            return False
        else:
            return True
    
    
    def IterCopy(self, treeview, model, iter_to_copy, target_iter, pos):
        new_pos_str=(model.get_string_from_iter(target_iter)).split(':')
        old_pos_str=(model.get_string_from_iter(iter_to_copy)).split(':')
        new_el_pos=int(new_pos_str[len(new_pos_str)-1])
        old_el_pos=int(old_pos_str[len(old_pos_str)-1])
        
        if treeview.get_model().get(iter_to_copy,2)[0] == "=Diagram=":
            node_to_copy = treeview.get_model().get(treeview.get_model().iter_parent(iter_to_copy),3)[0]
        else:
            node_to_copy = treeview.get_model().get(iter_to_copy,3)[0]
        if treeview.get_model().get(target_iter,2)[0] == "=Diagram=":
            target_node = treeview.get_model().get(treeview.get_model().iter_parent(target_iter),3)[0]
        else:
            target_node = treeview.get_model().get(target_iter,3)[0]
        
        if (pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE) or (pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER):
            if treeview.get_model().get(target_iter,2)[0] == "=Diagram=":
                raise ProjectError("BadMove")#MoveElementToDiagram
            elif treeview.get_model().get(iter_to_copy,2)[0] == "=Diagram=":
                node_to_copy.MoveDiagramToNewNode(target_node,treeview.get_model().get(iter_to_copy,3)[0])
                new_iter = model.insert(target_iter,len(target_node.diagrams)-1)
            else:
                node_to_copy.MoveNode(target_node)
                new_iter = model.append(target_iter)
        
        elif pos == gtk.TREE_VIEW_DROP_BEFORE:
            if treeview.get_model().get(iter_to_copy,2)[0] == "=Diagram=":
                if treeview.get_model().get(target_iter,2)[0] != "=Diagram=":
                    if new_el_pos>len(target_node.GetParent().diagrams):
                        raise ProjectError("BadMove")#MoveDiagramBeforeElement
                    else:
                        if target_node.GetParent()==node_to_copy and old_el_pos<new_el_pos:
                            new_el_pos=new_el_pos-1
                        node_to_copy.MoveDiagramToNewNode(target_node.GetParent(),treeview.get_model().get(iter_to_copy,3)[0],new_el_pos)
                else:
                    if target_node==node_to_copy and old_el_pos<new_el_pos:
                        new_el_pos=new_el_pos-1
                    node_to_copy.MoveDiagramToNewNode(target_node,treeview.get_model().get(iter_to_copy,3)[0],new_el_pos)
            elif treeview.get_model().get(target_iter,2)[0] == "=Diagram=":
                raise ProjectError("BadMove")#MoveElementBeforeDiagram
            else:
                if target_node.GetParent()==node_to_copy.GetParent() and old_el_pos<new_el_pos:
                    new_el_pos=new_el_pos-1
                node_to_copy.MoveNode(target_node.GetParent(),new_el_pos-len(target_node.GetParent().diagrams))
            new_iter = model.insert_before(None, target_iter)
        
        elif pos == gtk.TREE_VIEW_DROP_AFTER:
            if treeview.get_model().get(iter_to_copy,2)[0] == "=Diagram=":
                if treeview.get_model().get(target_iter,2)[0] != "=Diagram=":
                    raise ProjectError("BadMove")#MoveDiagramAfterElement
                else:
                    if (target_node==node_to_copy and old_el_pos>new_el_pos) or (target_node!=node_to_copy):
                        new_el_pos=new_el_pos+1
                    node_to_copy.MoveDiagramToNewNode(target_node,treeview.get_model().get(iter_to_copy,3)[0],new_el_pos)
            elif treeview.get_model().get(target_iter,2)[0] == "=Diagram=":
                if new_el_pos+1<len(target_node.diagrams):
                    raise ProjectError("BadMove")#MoveElementAfterDiagram
                else:
                    if (target_node==node_to_copy.GetParent() and old_el_pos>new_el_pos) or (target_node!=node_to_copy.GetParent()):
                        new_el_pos=new_el_pos+1
                    node_to_copy.MoveNode(target_node,new_el_pos-len(target_node.diagrams))
            else:
                if (target_node.GetParent()==node_to_copy.GetParent() and old_el_pos>new_el_pos) or (target_node.GetParent()!=node_to_copy.GetParent()):
                    new_el_pos=new_el_pos+1
                node_to_copy.MoveNode(target_node.GetParent(),new_el_pos-len(target_node.GetParent().diagrams))
            new_iter = model.insert_after(None, target_iter)
                    
        for i in range(4):
            model.set_value(new_iter, i, model.get_value(iter_to_copy, i))
              
        if model.iter_has_child(iter_to_copy):
            for i in range(0, model.iter_n_children(iter_to_copy)):
                next_iter_to_copy = model.iter_nth_child(iter_to_copy, i)
                self.IterCopy(treeview, model, next_iter_to_copy, new_iter, gtk.TREE_VIEW_DROP_INTO_OR_BEFORE)
    
    @event("mnuTreeSetAsDefault", "activate", "set")
    @event("mnuTreeUnSetDefault", "activate", "unset")
    def on_set_as_default_activate(self, widget, action):
        iter = self.twProjectView.get_selection().get_selected()[1]
        model = self.twProjectView.get_model()
        if model.get(iter,2)[0] == "=Diagram=":
            diagram = model.get(iter,3)[0]
            if action == 'set':
                self.application.GetProject().AddDefaultDiagram(diagram)
            else:
                self.application.GetProject().DeleteDefaultDiagram(diagram)
    
    @event("twProjectView","drag_data_received")
    def on_drag_data_received(self, widget, context, x, y, selection, info, etime):
        if widget.get_dest_row_at_pos(x, y) is not None:
            path, pos = widget.get_dest_row_at_pos(x, y)
            model, iter_to_copy = widget.get_selection().get_selected()
            target_iter = model.get_iter(path)
                       
            if self.CheckSanity(model, iter_to_copy, target_iter):
                try:
                    self.IterCopy(widget, model, iter_to_copy, target_iter, pos)
                except ProjectError, e:
                    if e.GetName() == "BadMove":
                        context.finish(False, False, etime)
                        return
                context.finish(True, True, etime)
            else:
                context.finish(False, False, etime)
    
    @event("application.bus", "diagram-created-from-plugin")
    def on_diagram_created(self, widget, diagram):
        parent = diagram.GetNode()
        iter = self.get_iter_from_path(self.TreeStore, self.TreeStore.get_iter_root(), parent.GetPath())
        newIter = self.TreeStore.append(iter)
        self.TreeStore.set(newIter,
                           0, diagram.GetName(),
                           1, PixmapFromPath(self.application.GetProject().GetMetamodel().GetStorage(), diagram.GetType().GetIcon()),
                           2, '=Diagram=',
                           3, diagram)
