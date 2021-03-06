#!/usr/bin/python

import lib
from lib.Drawing.OpenedDrawingAreas import COpenedDrawingAreas

import lib.Warnings.List
lib.Warnings.List.WarningList.handle()

from lib.Depend.gtk2 import gtk
from lib.Depend.gtk2 import gobject

from lib.Clipboard import CClipboard
from lib.Gui.common import CApplication, argument

import os.path
import traceback

from lib.Project import CProject
from lib.Project import CRecentFiles
from lib.Project.Templates import CTemplateManager
from lib.Addons import CAddonManager

from lib.GenericGui import CFileTypeManager

import lib.Gui
from lib.Gui import CBus, CPluginAdapter
from lib.Gui.dialogs import CExceptionDialog, CErrorDialog

from lib.config import config
from lib.Distconfig import LOCALES_PATH, GUI_PATH, SVN_REVISION, IS_FROZEN, ETC_PATH
from lib.consts import SPLASH_TIMEOUT, CHECK_ADDON_INTERVAL

from lib.Exceptions import UserException

from lib.Base.Registrar import registrar

from lib.datatypes import CVersion

from lib.Commands import CCommandProcessor

if IS_FROZEN:
    gtkrc = os.path.join(ETC_PATH, 'gtkrc')
    gtk.rc_set_default_files([gtkrc])
    gtk.rc_reparse_all_for_settings(gtk.settings_get_default(), True)

__version__ = '1.0'

class Application(CApplication):
    version = CVersion(__version__)
    
    if SVN_REVISION:
        version = version.OfRevision(SVN_REVISION)
    
    windows = lib.Gui
    main_window = 'frmMain'
    textdomain = 'uml_fri'
    localespath = LOCALES_PATH
    
    guipath = GUI_PATH

    project = None
    
    def __init__(self):
        self.openedDrawingAreas = COpenedDrawingAreas(self)
        self.warnings = lib.Warnings.List.WarningList()
        self.recentFiles = CRecentFiles()
        self.clipboard = CClipboard()
        self.bus = CBus()
        self.fileTypes = CFileTypeManager()
        self.commands = CCommandProcessor(self.bus)
        self.__action = None
        
        CApplication.__init__(self)
        self.pluginAdapter = CPluginAdapter(self)
        self.addonManager = CAddonManager(self.GetPluginAdapter(), ('gtk+', self))
        self.templateManager = CTemplateManager(self.addonManager)
        
        self.__startupStarter = self.addonManager.StartAll()
        gobject.timeout_add(CHECK_ADDON_INTERVAL, self.__StartupStarterTimer)
        #self.GetWindow('frmSplash').Hide()
    
    def GetBus(self):
        return self.bus
    
    def GetPluginAdapter(self):
        return self.pluginAdapter
    
    def GetCommands(self):
        return self.commands

    def GetOpenedDrawingAreas(self):
        return self.openedDrawingAreas
    
    @argument("-o", "--open", True)
    def DoOpen(self, value):
        "Opens selected project file"
        self.__action = 'open', value
            
    
    @argument("-n", "--new", True)
    def DoNew(self, value):
        "Creates new project from template"
        self.__action = 'new', value
    
    @argument(None, "--install-addon", True)
    def DoInstallAddon(self, value):
        "Install addon for UML .FRI"
        if self.__action is None:
            self.__action = 'install', value
            addon = self.addonManager.LoadAddon(value)
            
            self.GetWindow('frmSplash').Hide()
            
            if addon is None:
                CErrorDialog(None, _("Addon could not be installed")).run()
                return
            
            if self.GetWindow("frmInstallAddon").ShowDialog(self.GetWindow("frmMain"), addon):
                self.addonManager.InstallAddon(addon)
                return
    
    @argument()
    def DoArguments(self, *files):
        "File to open"
        self.__action = 'open', files[0]
    
    def GetRecentFiles(self):
        return self.recentFiles
    
    def ProjectInit(self):
        self.clipboard.Clear()
        if self.project is None:
            registrar.Clear()
            self.project = CProject(self.addonManager)
            
    def ProjectDelete(self):
        self.project = None
        
    def GetProject(self):
        return self.project
    
    def GetAddonManager(self):
        return self.addonManager
    
    def GetTemplateManager(self):
        return self.templateManager
    
    def GetFileTypeManager(self):
        return self.fileTypes
    
    def GetClipboard(self):
        return self.clipboard
    
    def cw_FileChooserWidget(self, str1, str2, int1, int2):
        if str1:
            action = getattr(gtk, 'FILE_CHOOSER_ACTION_%s'%str1.upper())
        else:
            action = gtk.FILE_CHOOSER_ACTION_OPEN
        widget = gtk.FileChooserWidget(action)
        widget.show()
        return widget
    
    def DisplayException(self, exccls, excobj, tb):
        if issubclass(exccls, UserException) and not __debug__:
            text = _('An exception has occured:')+ '\n\n<b>'+exccls.__name__ +':</b> '+ str(excobj)
            CExceptionDialog(None, text).run()
        else:
            if __debug__:
                traceback.print_exc()
            win = self.GetWindow('frmException')
            win.SetParent(self.GetWindow('frmMain'))
            win.SetErrorLog(exccls, excobj, tb)
            win.Show()
    
    def Quit(self):
        self.addonManager.StopAll()
        CApplication.Quit(self)
        config.Save()
        self.addonManager.Save()
        self.recentFiles.SaveRecentFiles()
    
    def __StartupStarterTimer(self):
        self.__startupStarter.Step()
        if not self.__startupStarter.Remaining():
            gobject.timeout_add(SPLASH_TIMEOUT, self.__HideSplash)
            return False
        else:
            return True
    
    def __HideSplash(self):
        self.GetWindow('frmSplash').Hide()
        
        if self.__action is not None:
            if self.__action[0] == 'open':
                self.GetWindow('frmMain').LoadProject(self.__action[1], False)
            elif self.__action[0] == 'new':
                self.GetWindow('frmMain').LoadProject(self.__action[1], True)
        
        del self.__action
        
        return False

if __name__ == '__main__':
    gobject.threads_init()
    Application().Main()
