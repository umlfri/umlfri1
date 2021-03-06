from lib.Depend.gtk2 import gtk
from lib.Depend.sysplatform import platform

from common import CWindow, event
from lib.datatypes import CColor

class CfrmCopyImage(CWindow):
    name = 'frmCopyImage'
    glade = 'export.glade'
    
    widgets = ('spinCopyZoom','chkCopyTransparent', 'spinCopyPadding')
    
    def Show(self):
        if platform.isA("windows"):
            self.chkCopyTransparent.set_active(False)
            self.chkCopyTransparent.set_sensitive(False)
        try:
            if self.form.run() == gtk.RESPONSE_OK:
                zoom = self.spinCopyZoom.get_value_as_int()
                padding = self.spinCopyPadding.get_value_as_int()
                if self.chkCopyTransparent.get_active():
                    bg = None
                else:
                    bg = CColor("#FFFFFF")
                return zoom, padding, bg
            else:
                return None, None, None
        finally:
            self.Hide()
