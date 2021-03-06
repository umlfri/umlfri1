from select import select
from lib.Depend.gtk2 import gtk
from common import CWindow, event

from lib.consts import WEB, UNDO_BUTTONS_VISIBLE, SHOW_UNDO_REDO_ITEMS
from lib.Exceptions import *

import gobject
import os.path
from lib.Drawing import CElement, CDiagram, CConnection, CConLabelInfo
from lib.Elements import CElementObject, CElementType
from dialogs import CErrorDialog, CWarningDialog, CQuestionDialog, ECancelPressed
from tbToolBox import CtbToolBox
from twProjectView import CtwProjectView
from twWarnings import CtwWarnings
from mnuItems import CmnuItems
from picDrawingArea import CpicDrawingArea
from nbProperties import CnbProperties
from tabs import CTabs
from tabStartPage import CtabStartPage
from lib.Distconfig import IMAGES_PATH
from lib.Gui.diagramPrint import CDiagramPrint
from lib.Exceptions import UserException, ProjectError
from lib.Gui.frmProperties import CfrmProperties
from lib.Project import CProjectNode

class CfrmMain(CWindow):
    name = 'frmMain'
    glade = 'main.glade'

    widgets = (
        #menu
        #############
        'mItemFile',
        'mnuOpen', 'mnuNewProject', 'mnuOpenRecent', 'mOpenRecent_menu', 'mnuSave', 'mnuSaveAs', 'mnuPrint', 'mnuImport','mnuExportToFile', 'mnuProperties', 'mnuQuit',
        #############
        'mItemEdit',
        'mnuCut', 'mnuCopy', 'mnuCopyAsImage', 'mnuPaste', 'mnuDelete',
        #############
        'mItemProject',
        #############
        'mItemDiagram',
        'mnuExport',
        #############
        'mItemView',
        'mnuViewTools', 'mnuViewCommands', 'mnuViewAlignAndDistribute', 'mnuNormalSize', 'mnuZoomIn','mnuZoomOut', 'mnuBestFit',
        'hndCommandBar', 'hndCommandBar2', 'mnuViewWarnings',
        #############
        'mnuAddons', 'mnuOptions',
        #############
        'mItemHelp',
        'mnuAbout',
        'mnuWebsite',
        'mnuError',
        #############
        'mItemElement',
        'mmShift_SendBack', 'mmShift_BringForward', 'mmShift_ToBottom', 'mmShift_ToTop',
        #############
        #toolbar
        'cmdNew', 'cmdOpen', 'cmdSave', 'cmdCopy', 'cmdCut', 'cmdPaste', 'cmdZoomOut', 'cmdZoomIn',
        'cmdUndo', 'cmdRedo', 'sepUndoRedo',
        #############
        #toolbar2
        'cmdAlignLeftMost', 'cmdAlignRightMost', 'cmdAlignUpMost', 'cmdAlignDownMost', 'cmdSpaceEvenlyHorizontally', 'cmdSpaceEvenlyVertically',
        'cmdResizeByMax', 'cmdResizeByMin',
        #############
        #fullscreen
        'mnuMenubar', 'mnuFullscreen', 'cmdCloseFullscreen', 'vpaRight', 'sbStatus','hpaRight',
        )

    complexWidgets = (CtbToolBox, CtwProjectView, CmnuItems, CpicDrawingArea, CnbProperties, CTabs,
                      CtabStartPage, CtwWarnings, )

    def __init__(self, app, wTree):
        CWindow.__init__(self, app, wTree)
        self.form.set_icon_from_file(os.path.join(IMAGES_PATH, 'app_icon.png'))
        self.diagramPrint = CDiagramPrint()
        self.form.maximize()
        self.__sensitivity_project = None
        self.UpdateMenuSensitivity(project = False)
        self.ReloadTitle()

        self.__undoMenu = gtk.Menu()
        self.__redoMenu = gtk.Menu()

        self.cmdUndo.set_menu(self.__undoMenu)
        self.cmdRedo.set_menu(self.__redoMenu)

        if UNDO_BUTTONS_VISIBLE:
            self.cmdUndo.show()
            self.cmdRedo.show()
            self.sepUndoRedo.show()

        self.on_undo_redo_action(None, 'start')

        self.actionQuit = False
        self.after_on_open_file = False
        self.afterActionOpen = False
        self.copy = None

    def SetSensitiveMenuChilds(self, MenuItem, value):
        for i in MenuItem.get_submenu().get_children():
            i.set_sensitive(value)

    def UpdateMenuSensitivity(self, project = None, diagram = None, element = None, topElement = None, connection = None):
        if self.__sensitivity_project is None:
            self.__sensitivity_project = [True, True, True, True, True, True, True]
        changes = 0
        if project is not None:
            if not project:
                diagram = False
            if project != self.__sensitivity_project[0]:
                changes += 1
            self.__sensitivity_project[0] = project
        else:
            project = self.__sensitivity_project[0]
        if diagram is not None:
            if not diagram:
                element = False
            if diagram != self.__sensitivity_project[1]:
                changes += 1
            self.__sensitivity_project[1] = diagram
        else:
            diagram = self.__sensitivity_project[1]
        if element is not None:
            if element != self.__sensitivity_project[2]:
                changes += 1
            self.__sensitivity_project[2] = element
        else:
            element = self.__sensitivity_project[2]
        if connection is not None:
            if connection != self.__sensitivity_project[5]:
                changes += 1
            self.__sensitivity_project[5] = connection
        else:
            connection = self.__sensitivity_project[5]
        if topElement is not None:
            if topElement != self.__sensitivity_project[6]:
                changes += 1
            self.__sensitivity_project[6] = topElement
        else:
            topElement = self.__sensitivity_project[6]
        if not self.application.GetClipboard().IsEmpty():
             changes += 1

        zoomin = diagram and self.picDrawingArea.CanIncreaseScale()
        zoomout = diagram and self.picDrawingArea.CanDecreaseScale()

        changes += zoomin != self.__sensitivity_project[3]
        changes += zoomout != self.__sensitivity_project[4]
        self.__sensitivity_project[3] = zoomin
        self.__sensitivity_project[4] = zoomout

        if changes == 0:
            return

        self.picDrawingArea.UpdateMenuSensitivity(project, diagram, element, topElement, connection)

        self.SetSensitiveMenuChilds(self.mItemProject, project)
        self.SetSensitiveMenuChilds(self.mItemDiagram, diagram)
        self.SetSensitiveMenuChilds(self.mItemElement, element)
        self.mnuSave.set_sensitive(project)
        self.mnuSaveAs.set_sensitive(project)
        self.mnuPrint.set_sensitive(diagram)
        self.cmdSave.set_sensitive(project)
        self.cmdCopy.set_sensitive(element)
        self.cmdCut.set_sensitive(element)
        self.cmdPaste.set_sensitive(
            diagram and not self.application.GetClipboard().IsEmpty() and
            not bool(set(i.GetObject() for i in self.picDrawingArea.GetDiagram().GetElements()).intersection(set(i.GetObject() for i in self.application.GetClipboard().GetContent()))))
        self.cmdZoomIn.set_sensitive(diagram)
        self.cmdZoomOut.set_sensitive(diagram)
        self.mnuSave.set_sensitive(project)

        self.mnuCopy.set_sensitive(element)
        self.mnuCopyAsImage.set_sensitive(element)
        self.mnuCut.set_sensitive(element)
        self.mnuPaste.set_sensitive(
            diagram and not self.application.GetClipboard().IsEmpty() and
            not bool(set(i.GetObject() for i in self.picDrawingArea.GetDiagram().GetElements()).intersection(set(i.GetObject() for i in self.application.GetClipboard().GetContent()))))
        self.mnuDelete.set_sensitive(element or connection)
        self.mnuNormalSize.set_sensitive(diagram)
        self.mnuZoomIn.set_sensitive(zoomin)
        self.cmdZoomIn.set_sensitive(zoomin)
        self.mnuZoomOut.set_sensitive(zoomout)
        self.cmdZoomOut.set_sensitive(zoomout)
        self.mnuBestFit.set_sensitive(diagram)
        self.mnuFullscreen.set_sensitive(diagram)

    def LoadProject(self, filenameOrTemplate, copy = None):
        self.nbTabs.CloseAll()
        self.application.ProjectDelete()
        self.application.ProjectInit()
        try:
            if copy is None:
                self.application.GetProject().CreateProject(filenameOrTemplate)
            else:
                self.application.GetProject().LoadProject(filenameOrTemplate, copy)
        except ProjectError as e:
            self.__ClearApplication(filenameOrTemplate, copy)
            return CErrorDialog(self.form, str(e)).run()
        except Exception, ex:
            self.__ClearApplication(filenameOrTemplate, copy)
            '''
            if __debug__:
                raise
            '''
            return CErrorDialog(self.form, _('Error opening file') + '\n' + _(str(ex))).run()

        self.ReloadTitle()
        self.twProjectView.Redraw(True)
        self.mnuItems.Redraw()
        self.nbProperties.Fill(None)
        self.picDrawingArea.Redraw()
        self.UpdateMenuSensitivity(project = True)
        for diagram in self.application.GetProject().GetDefaultDiagrams():
            self.AddDiagram(diagram)
        self.twProjectView.GetRootNode()
        self.twProjectView.twProjectView.grab_focus()
        self.application.GetCommands().Clear()
        self.on_undo_redo_action(None, 'start')

    def AddDiagram(self, diagram):
        """
        Method for adding diagram into CTabs and COpenedDrawingAreas.
        :param diagram:
        :return:
        """
        self.picDrawingArea.SetDiagram(diagram)
        self.nbTabs.AddTab(diagram)

    def __ClearApplication(self, filenameOrTemplate, copy = None):
        """
        It sets main application for clear using (for loading new project). It's closing last loaded project, closing all tabs...
        It can be called, when exceptions were threw during loading project.
        :param filenameOrTemplate:
        :param copy:
        :return:
        """
        if copy is not None:
            self.application.GetRecentFiles().RemoveFile(filenameOrTemplate)
        self.application.ProjectDelete()
        self.nbTabs.CloseAll()
        self.twProjectView.ClearProjectView()
        self.ReloadTitle()
        self.nbProperties.Fill(None)
        self.UpdateMenuSensitivity(project = False)

    def PaintAll(self):
        if not self.nbTabs.IsStartPageActive():
            self.picDrawingArea.Paint(True)

    def ApplyNewSettings(self):
        '''
        Calls appropriate update methods after settings changed.
        '''
        for diagram in self.nbTabs.diagrams:
            if diagram.GetType():
                diagram.ApplyNewSettings()

    def OnOpen(self, win):
        filenameOrTemplate, copy = win
        if filenameOrTemplate is not None:
            try:
                if self.application.GetProject() is not None and CQuestionDialog(self.form, _('Do you want to save project?'), True).run():
                    self.afterActionOpen = True
                    self.filename = filenameOrTemplate
                    self.copy = copy
                    self.ActionSave(None)
                else:
                    self.LoadProject(filenameOrTemplate, copy)
                    self.tabStartPage.Fill()
            except ECancelPressed:
                return

    def OnSaveAs(self, win):
        filename, isZippedFile = win
        try:
            if filename is not None:
                self.application.GetProject().SaveProject(filename, isZippedFile)
                self.ReloadTitle()
                self.tabStartPage.Fill()
        except UserException as e:
            CErrorDialog(self.form, str(e)).run()
        self.AfterSaveAction()

    def AfterSaveAction(self):
        if self.actionQuit:
            self.application.Quit()
        if self.after_on_open_file:
            self.LoadProject(self.filename, False)
            self.tabStartPage.Fill()
            self.after_on_open_file = False
        if self.afterActionOpen:
            self.LoadProject(self.filename, self.copy)
            self.tabStartPage.Fill()
            self.afterActionOpen = False

    # Diagrams
    @event("mnuViewTools", "activate")
    def ActionViewTools(self, *args):
        self.tbToolBox.SetVisible(self.mnuViewTools.get_active())

    @event("mnuViewCommands", "activate")
    def ActionViewCommands(self, *args):
        if self.mnuViewCommands.get_active():
            self.hndCommandBar.show()
        else:
            self.hndCommandBar.hide()

    @event("mnuViewAlignAndDistribute", "activate")
    def ActionViewAlignAndDistribute(self, *args):
        if self.mnuViewAlignAndDistribute.get_active():
            self.hndCommandBar2.show()
        else:
            self.hndCommandBar2.hide()

    @event("mnuViewWarnings", "activate")
    def ActionViewWarnings(self, *args):
        if self.mnuViewWarnings.get_active():
            self.twWarnings.Show()
        else:
            self.twWarnings.Hide()

    @event("cmdCloseFullscreen", "clicked")
    def ActionExitFullscreen(self, *args):
        self.mnuFullscreen.set_active(False)
        self.ActionFullscreen(*args)

    @event("mnuFullscreen", "activate")
    def ActionFullscreen(self, *args):
        if self.mnuFullscreen.get_active():
            self.mnuMenubar.hide()
            self.hndCommandBar.hide()
            self.hndCommandBar2.hide()
            self.sbStatus.hide()
            self.cmdCloseFullscreen.show()
            self.nbTabs.Hide()
            self.vpaRight.hide()
            self.form.window.fullscreen()
        else:
            self.mnuMenubar.show()
            self.ActionViewCommands()
            self.ActionViewAlignAndDistribute()
            self.sbStatus.show()
            self.cmdCloseFullscreen.hide()
            self.nbTabs.Show()
            self.vpaRight.show()
            self.form.window.unfullscreen()

    @event("mnuAddons", "activate")
    def on_mnuAddons_activate(self, mnu):
        tmp = self.application.GetWindow('frmAddons')
        tmp.SetParent(self)
        tmp.Show()

    # Preferencies
    @event("mnuOptions", "activate")
    def on_mnuOptions_activate(self, mnu):
        tmp = self.application.GetWindow('frmOptions')
        tmp.SetParent(self)
        if tmp.Show():
            self.ApplyNewSettings()
        self.PaintAll()

    # Help
    @event("tabStartPage","open-about-dialog")
    @event("mnuAbout", "activate")
    def on_mnuAbout_activate(self, mnu):
        tmp = self.application.GetWindow('frmAbout')
        tmp.SetParent(self)
        tmp.Show()

    @event("mnuWebsite", "activate")
    def on_mnuWebsite_activate(self, mnu):
        from webbrowser import open_new
        open_new(WEB)

    @event("mnuError", "activate")
    def on_mnuError_activate(self, mnu):
        text = _('This is just a test for the Exception handler window.\nYou will see this window if something really bad happens.\nSee the Help tab for more info.')
        raise Exception(text)

    @event('nbTabs','export-svg-from-TabMenu')
    @event('mnuExport', 'activate')
    def on_mnuExport_activate(self, widget):
        exportDialog = self.application.GetWindow('frmExport')
        exportDialog.setArea(self.picDrawingArea)
        exportDialog.SetParent(self)
        exportDialog.Show()

    def ReloadTitle(self):
        if self.application.GetProject() is None or self.application.GetProject().GetFileName() is None:
            self.form.set_title(_('UML .FRI designer'))
        else:
            self.form.set_title(_('UML .FRI designer [%s]')%self.application.GetProject().GetFileName())

    # Actions
    @event("form", "delete-event")
    @event("mnuQuit", "activate")
    def ActionQuit(self, widget, event = None):
        try:
            if self.application.GetProject() is not None and CQuestionDialog(self.form, _('Do you want to save project?'), True).run():
                self.actionQuit = True
                self.ActionSave(widget)
            else:
                self.application.Quit()
            return True
        except ECancelPressed:
            return True

    @event("tabStartPage","open-file")
    def on_open_file(self, widget, filename):
        if filename is not None:
            try:
                if self.application.GetProject() is not None and CQuestionDialog(self.form, _('Do you want to save project?'), True).run():
                    self.after_on_open_file = True
                    self.filename = filename
                    self.ActionSave(widget)
                else:
                    self.LoadProject(filename, False)
                    self.tabStartPage.Fill()
            except ECancelPressed:
                return

    @event("tabStartPage","open-project")
    @event("cmdOpen", "clicked")
    @event("mnuOpen", "activate")
    def ActionOpen(self, widget):
        self.application.GetWindow("frmOpenProject").ShowDialog(self, widget)
	
    @event("cmdNew", "clicked")
    @event("tabStartPage", "create-project")
    @event("mnuNewProject", "activate")
    def ActionNewProject(self, widget):
        filenameOrTemplate, copy = self.application.GetWindow ("frmNewProject").ShowDialog (self)
        if filenameOrTemplate:
            try:
                if self.application.GetProject () and CQuestionDialog (self.form, _('Do you want to save project?'), True).run ():
                    self.filename = filenameOrTemplate
                    self.copy = copy
                    self.afterActionOpen = True
                    self.ActionSave (widget)
                else:
                    self.LoadProject (filenameOrTemplate, copy)
                    self.tabStartPage.Fill()
            except ECancelPressed:
                return

    @event("mnuOpenRecent", "activate")
    def mnuOpenRecent_refresh (self, widget):
        # clear submenu
        for child in self.mOpenRecent_menu.get_children ():
            self.mOpenRecent_menu.remove (child)
        # reload submenu items
        self.application.GetRecentFiles ().RecheckFiles()
        i = 1
        for name, date in self.application.GetRecentFiles ().GetRecentFiles ():
            item = gtk.MenuItem ("%d %s" % (i, name), False)
            item.connect ("activate", self.on_RecentItem_activate)
            self.mOpenRecent_menu.add (item)
            i += 1
        widget.show_all ()

    def on_RecentItem_activate (self, widget):
        try:
            if self.application.GetProject() is not None and CQuestionDialog(self.form, _('Do you want to save project?'), True).run():
                self.filename = widget.get_label().split(' ', 1)[1]
                self.copy = False
                self.afterActionOpen = True
                self.ActionSave(widget)
            else:                
                filename = widget.get_label().split(' ', 1)[1]                
                self.LoadProject(filename, False)
                self.tabStartPage.Fill()
        except ECancelPressed:
            return

    @event("form", "key-press-event")
    def on_key_press_event(self, widget, event):
        if event.keyval in (gtk.keysyms.Tab, gtk.keysyms.ISO_Left_Tab):
            if event.state == (gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK):
                self.nbTabs.PreviousTab()
                self.form.emit_stop_by_name('key-press-event')
            elif event.state == gtk.gdk.CONTROL_MASK:
                self.nbTabs.NextTab()
                self.form.emit_stop_by_name('key-press-event')
        if event.state == gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK:
            if event.keyval == gtk.keysyms.F4:
                self.nbTabs.CloseAll()
        if event.state == gtk.gdk.CONTROL_MASK:
            if event.keyval  in (gtk.keysyms.F4, gtk.keysyms.w):
                self.nbTabs.CloseCurrentTab()
        if event.state == gtk.gdk.MOD1_MASK:
            Keys = [gtk.keysyms._1, gtk.keysyms._2, gtk.keysyms._3, gtk.keysyms._4, gtk.keysyms._5,
                    gtk.keysyms._6, gtk.keysyms._7, gtk.keysyms._8, gtk.keysyms._9, gtk.keysyms._0]
            if event.keyval in Keys:
                self.nbTabs.set_current_page(Keys.index(event.keyval))

    @event("nbTabs","drawing-area-set-focus")
    def on_drawing_area_set_focus(self,widget):
        self.picDrawingArea.SetFocus()

    @event("cmdSave", "clicked")
    @event("mnuSave", "activate")
    def ActionSave(self, widget):
        if self.application.GetProject().GetFileName() is None:
            self.ActionSaveAs(widget)
        else:
            self.application.GetProject().SaveProject()
            self.AfterSaveAction()

    @event("mnuSaveAs", "activate")
    def ActionSaveAs(self, widget):
        self.application.GetWindow("frmSave").ShowDialog(self)

    @event("mnuProperties", "activate")
    def ActionProperties(self, widget):
        self.diagramPrint.printPropertiesSetup()

    @event("mnuPrint", "activate")
    def ActionPrint(self, widget):
        self.diagramPrint.printStart(self.picDrawingArea.GetDiagram())

    @event("mnuImport", "activate")
    def ActionImport(self, widget):
        self.application.GetWindow("frmImport").ShowDialog(self)

    @event("mnuExportToFile", "activate")
    def ActionExportToFile(self, widget):
        self.application.GetWindow("frmExportToFile").ShowDialog(self)
    
    @event("mnuDelete","activate")
    def on_mnuDelete_click(self, widget):
        self.picDrawingArea.DeleteElements()

    @event("mnuNormalSize","activate")
    def mnuNormalSize_click(self, widget):
        self.picDrawingArea.SetNormalScale()
        self.UpdateMenuSensitivity()

    @event("mnuBestFit","activate")
    def mnuBestFit_click(self, widget):
        self.picDrawingArea.BestFitScale()
        self.UpdateMenuSensitivity()

    @event("cmdZoomOut", "clicked")
    @event("mnuZoomOut","activate")
    def on_mnuZoomOut_click(self, widget):
        self.picDrawingArea.DecreaseScale()
        self.UpdateMenuSensitivity()

    @event("cmdZoomIn", "clicked")
    @event("mnuZoomIn","activate")
    def on_mnuZoomIn_click(self, widget):
        self.picDrawingArea.IncreaseScale()
        self.UpdateMenuSensitivity()

    @event("cmdCut", "clicked")
    @event("mnuCut","activate")
    def on_mnuCut_click(self, widget):
        if self.picDrawingArea.HasFocus():
            self.picDrawingArea.ActionCut()
        else:
            pass

    @event("cmdCopy", "clicked")
    @event("mnuCopy","activate")
    def on_mnuCopy_click(self, widget):
        if self.picDrawingArea.HasFocus():
            self.picDrawingArea.ActionCopy()
            self.UpdateMenuSensitivity()

    @event("mnuCopyAsImage","activate")
    def on_mnuCopyAsImage_click(self, widget):
        if self.picDrawingArea.HasFocus():
            zoom, padding, bg = self.application.GetWindow('frmCopyImage').Show()
            if zoom is None:
                return
            gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD).set_image(self.picDrawingArea.GetSelectionPixbuf(zoom, padding, bg))

    @event("cmdPaste", "clicked")
    @event("mnuPaste","activate")
    def on_mnuPaste_click(self, widget):
        if self.picDrawingArea.HasFocus():
            try:
                self.picDrawingArea.ActionPaste()
            except UserException, e:
                if e.GetName() == "ElementAlreadyExists":
                    return CWarningDialog(self.form, _('Element is already in this diagram')).run()
                elif e.GetName() == "DiagramHasNotThisElement":
                    return CWarningDialog(self.form, _('Wrong element: ') + e.GetParameter(1).GetObject().GetType().GetId()).run()
                else:
                    return CWarningDialog(self.form, e.GetName()).run()

    def ActionLoadToolBar(self, widget):
        pass

    @event("cmdAlignLeftMost", "clicked", True, True, False)
    @event("cmdAlignRightMost", "clicked", True, False, False)
    @event("cmdAlignRightMost", "clicked", True, False, False)
    @event("cmdAlignUpMost","clicked", False, True, False)
    @event("cmdAlignDownMost","clicked", False, False, False)
    def on_mnuAlignMost_click(self, widget, horiz, lower, defaultE):
        self.picDrawingArea.on_mnuAlign_activate(widget, horiz, lower, defaultE)

    @event("cmdSpaceEvenlyHorizontally","clicked", True)
    @event("cmdSpaceEvenlyVertically","clicked", False)
    def on_mnuMakeSpacing_click(self, widget, p1):
        self.picDrawingArea.on_mnuMakeSpacing(widget, p1)

    @event("cmdResizeByMax","clicked")
    def on_mnuResizeByMax(self, widget):
        self.picDrawingArea.on_mnuResizeByMaximalElement(widget)

    @event("cmdResizeByMin","clicked")
    def on_mnuResizeByMin(self, widget):
        self.picDrawingArea.on_mnuResizeByMinimalElement(widget)

    # User defined signals
    @event("mnuItems", "add-element")
    def on_directAdd_element(self, widget, element):
        """
        Add element into a project tree

        @param widget:  Widget
        @type widget:   CWidget

        @param element: Id (name) of added element
        @type element:  String
        """
        if self.twProjectView.GetSelectedElement()!=None:
            parentElement = self.twProjectView.GetSelectedElement()
        elif self.twProjectView.GetSelectedDiagram()!=None:
            parentElement = self.twProjectView.GetSelectedDiagram()
        else:
            parentElement = self.twProjectView.GetRootNode()
        ElementType = self.application.GetProject().GetMetamodel().GetElementFactory().GetElement(element)
        ElementObject = CElementObject(ElementType)
        self.twProjectView.AddElement(ElementObject, None, parentElement)

    @event("application.bus", "add-element")
    def on_add_element(self, widget, Element, diagram, parentElement):
        self.twProjectView.AddElement(Element, diagram, parentElement)

    @event("mItemFile", "activate")
    def on_mItemFile_activate (self, widget):
        toImport = False
        toExport = False
        
        for fileType in self.application.GetFileTypeManager().GetFileTypes():
            toImport = toImport or fileType.GetImportPossible()
            toExport = toExport or fileType.GetExportPossible()
        self.mnuImport.set_sensitive(toImport)
        self.mnuExportToFile.set_sensitive(toExport)

    @event("twProjectView", "close-diagram")
    def on_remove_diagram(self, widget, diagram):
        self.nbTabs.CloseTabByDiagram(diagram)

    @event("nbTabs", "change_current_page")
    def on_change_diagram(self, widget, diagram):
        if diagram is None:
            self.tbToolBox.SetButtons(None)
            self.UpdateMenuSensitivity(diagram = False)
        else:
            self.picDrawingArea.SetDiagram(diagram)
            self.tbToolBox.SetButtons(diagram.GetType().GetId())
            self.UpdateMenuSensitivity(diagram = True)

    @event("nbTabs","show-diagram-in-project")
    def on_show_diagram_in_project(self, widget, diagram):
        self.twProjectView.ShowDiagram(diagram)

    @event("application.bus", "selected-items")
    def on_picDrawingArea_selected_item(self, widget, selected):
        self.UpdateMenuSensitivity(
            element = any(isinstance(x, CElement) for x in selected),
            topElement = any((isinstance(x, CElement) and x.GetObject().GetNode().GetParent() is None) for x in selected),
            connection = any(isinstance(x, CConnection) for x in selected)
        )
        if len(selected) == 1:
            self.nbProperties.Fill(selected[0])
        else:
            self.nbProperties.Fill(None)

    @event("application.bus","delete-element-from-all")
    def on_picDrawingArea_delete_selected_item(self, widget, selected):
        self.twProjectView.DeleteElement(selected)

    @event("twProjectView", "selected-item-tree")
    def on_twTreeView_selected_item(self, widget, selected):
        self.picDrawingArea.DeselectAll()
        self.picDrawingArea.Paint()
        self.nbProperties.Fill(selected)

    @event("twProjectView", "repaint")
    def on_repaint_picDravingArea(self, widget):
        self.picDrawingArea.Paint()

    @event("twProjectView","selected_diagram")
    def on_select_diagram_and_element(self, widget, diagram, object):
        self.AddDiagram(diagram)
        if object is not None:
            self.picDrawingArea.SelectObject(object)

    @event("application.bus","open-diagram")
    def on_open_diagram(self, widget, diagrams):
        for diagram in diagrams:
            self.on_select_diagram_and_element(widget, diagram, None)

    @event("application.bus", "open-specification")
    def on_open_specification(self, widget, obj):
        frmProps = self.application.GetWindow('frmProperties')
        frmProps.SetParent(self)
        frmProps.ShowPropertiesWindow(obj, self.application)

    @event('application.bus', 'properties-editing-started')
    def on_nbProperties_editing_started (self, widget):
        for menuitem in self.mnuMenubar:
            menuitem.set_sensitive (False)

    @event('application.bus', 'properties-editing-stoped')
    def on_nbProperties_editing_stoped (self, widget):
        for menuitem in self.mnuMenubar:
            menuitem.set_sensitive (True)

    @event('application.bus', 'all-content-update', '', False)
    @event('application.bus', 'all-content-update-from-plugin', '', True)
    @event('application.bus', 'content-update', False)
    @event('application.bus', 'content-update-from-plugin', True)
    def on_nbProperties_content_update(self, widget, element, property, fromPlugin):
        if isinstance(element, (CElement, CConnection, CProjectNode, CConLabelInfo)):
            object = element.GetObject()
        else:
            object = element
        if property == '' or object.HasVisualAttribute(property):
            if (self.picDrawingArea.GetDiagram().HasElementObject(object)
                or self.picDrawingArea.GetDiagram().HasConnection(object)):
                if fromPlugin:
                    self.picDrawingArea.ToPaint()
                else:
                    self.picDrawingArea.Paint()
            self.twProjectView.UpdateElement(object)
            self.nbProperties.Fill(element)

    @event("tbToolBox", "toggled")
    def on_tbToolBox_toggled(self, widget, ItemId, ItemType):
        # self.picDrawingArea.GetDiagram().GetSelection().DeselectAll()
        # self.picDrawingArea.ResetAction()
        self.application.GetBus().emit('selected-toolbox-item-changed', (ItemId, ItemType))

    @event('application.bus', 'get-selected-toolbox-item')
    def on_get_selected_toolbox_item(self, widget):
        return self.tbToolBox.GetSelected()

    @event('application.bus', 'set-selected-toolbox-item')
    def on_get_selected_toolbox_item(self, widget, item):
        self.tbToolBox.SetSelected(item)


    @event('application.bus', 'run-dialog')
    def on_run_dialog(self, widget, type, message):
        if type == 'warning':
            return CWarningDialog(self.form, message).run()
        else:
            pass

    #Z-Order
    # 'mmShift_SendBack', 'mmShift_BringForward', 'mmShift_ToBottom', 'mmShift_ToTop'
    @event("mmShift_SendBack", "activate")
    def on_mnuItems_mmShift_SendBack(self, menuItem):
        self.picDrawingArea.Shift_activate('SendBack')

    @event("mmShift_BringForward", "activate")
    def on_mnuItems_mmShift_BringForward(self, menuItem):
        self.picDrawingArea.Shift_activate('BringForward')

    @event("mmShift_ToBottom", "activate")
    def on_mnuItems_mmShift_ToBottom(self, menuItem):
        self.picDrawingArea.Shift_activate('ToBottom')

    @event("mmShift_ToTop", "activate")
    def on_mnuItems_mmShift_ToTop(self, menuItem):
        self.picDrawingArea.Shift_activate('ToTop')

    @event("cmdUndo", "clicked")
    def on_cmdUndo_clicked(self, cmd):
        self.application.GetCommands().Undo()

    @event("cmdRedo", "clicked")
    def on_cmdRedo_clicked(self, cmd):
        self.application.GetCommands().Redo()

    def __fillUndoRedoMenu(self, type, menu, items):
        for child in menu.get_children():
            menu.remove(child)

        for id, item in enumerate(items):
            menuItem = gtk.MenuItem(label = item)
            menuItem.connect('activate', self.on_undo_redo_menu_item, type, id + 1)
            menuItem.show()
            menu.append(menuItem)

    def on_undo_redo_menu_item(self, mnuItem, type, count):
        if type == 'undo':
            self.application.GetCommands().Undo(count)
        else:
            self.application.GetCommands().Redo(count)

    @event("picDrawingArea.picEventBox", "scroll-event")
    def on_picEventBox_scroll_event(self, widget, event):
        if (event.state & gtk.gdk.CONTROL_MASK):
            self.UpdateMenuSensitivity()

    @event('application.bus', 'project-opened-from-plugin-adapter')
    def on_project_opened(self, widget):
        self.nbTabs.CloseAll()
        self.ReloadTitle()
        self.twProjectView.Redraw(True)
        self.mnuItems.Redraw()
        self.nbProperties.Fill(None)
        self.picDrawingArea.Redraw()
        self.UpdateMenuSensitivity(project = True)
        for diagram in self.application.GetProject().GetDefaultDiagrams():
            self.AddDiagram(diagram)
        self.application.GetCommands().Clear()
        self.on_undo_redo_action(None, 'start')

    @event('application.bus', 'undo-redo-action')
    def on_undo_redo_action(self, bus, action):
        self.cmdUndo.set_sensitive(self.application.GetCommands().CanUndo())
        self.__fillUndoRedoMenu('undo', self.__undoMenu, self.application.GetCommands().GetUndoStack(SHOW_UNDO_REDO_ITEMS))
        self.cmdRedo.set_sensitive(self.application.GetCommands().CanRedo())
        self.__fillUndoRedoMenu('redo', self.__redoMenu, self.application.GetCommands().GetRedoStack(SHOW_UNDO_REDO_ITEMS))
