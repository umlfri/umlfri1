from lib.Depend.gtk2 import gtk

import common
import lib.consts
import os.path

class CfrmSave(common.CWindow):
    name = 'frmSave'
    
    
    def __init__(self, app, wTree):
        common.CWindow.__init__(self, app, wTree)
        
        filter = gtk.FileFilter()
        filter.set_name(_("UML .FRI Projects"))
        filter.add_pattern('*'+lib.consts.PROJECT_EXTENSION)
        self.form.add_filter(filter)
        
        filter = gtk.FileFilter()
        filter.set_name(_("UML .FRI Clear XML Projects"))
        filter.add_pattern('*'+lib.consts.PROJECT_CLEARXML_EXTENSION)
        self.form.add_filter(filter)
        
        filter = gtk.FileFilter()
        filter.set_name(_("UML .FRI Project templates"))
        filter.add_pattern('*'+lib.consts.PROJECT_TPL_EXTENSION)
        self.form.add_filter(filter)
        
        filter = gtk.FileFilter()
        filter.set_name(_("All files"))
        filter.add_pattern("*")
        self.form.add_filter(filter)
    
    def ShowDialog(self, parent):
        self.form.set_transient_for(parent.form)
        try:
            while True:
                if self.form.run() == gtk.RESPONSE_CANCEL:
                    self.form.hide()
                    return None
                filter = self.form.get_filter().get_name()
                filename = self.form.get_filename().decode('utf-8')
                if filename is None:
                    continue
                if '.' not in os.path.basename(filename):
                    if filter == _("UML .FRI Projects"):
                        filename += lib.consts.PROJECT_EXTENSION
                    elif filter == _("UML .FRI Clear XML Projects"):
                        filename += lib.consts.PROJECT_CLEARXML_EXTENSION
                    elif filter == _("UML .FRI Project templates"):
                        filename += lib.consts.PROJECT_TPL_EXTENSION
                if not os.path.isdir(filename):
                    self.application.GetRecentFiles().AddFile(filename)
                    return filename
        finally:
            self.form.hide()
