import gtk
import gtk.glade
import gobject

def dynamicmax(xml):
    global dynamic_checks
    dynamic_checks = 0
    for idx in range (16):
        if xml.get_widget('dyna%d' %(idx+1)).get_active() != 0:
            dynamic_checks= dynamic_checks + 1     

def a_dyna_toggled(xml,dynanumber):
    for idx in range(16):
        if xml.get_widget('dyna%d' %(idx+1)).get_active() != 0:
            dynamicmax(xml)
            if dynamic_checks <= 5:
                xml.get_widget('order%d' %(idx+1)).set_sensitive(True)
                xml.get_widget('stop%d' %(idx+1)).set_sensitive(True)
                xml.get_widget('incr%d' %(idx+1)).set_sensitive(True)
            else:
                xml.get_widget('dyna%d' %dynanumber).set_active(0)
        else:
            xml.get_widget('order%d' %(idx+1)).set_sensitive(False)
            xml.get_widget('stop%d' %(idx+1)).set_sensitive(False)
            xml.get_widget('incr%d' %(idx+1)).set_sensitive(False)
        if xml.get_widget('outputdac%d' %(idx+1)).get_active() ==0:
            xml.get_widget('order%d' %(idx+1)).set_sensitive(False)
            xml.get_widget('stop%d' %(idx+1)).set_sensitive(False)
            xml.get_widget('incr%d' %(idx+1)).set_sensitive(False)

def a_outputdac_changed(xml):
    a_dyna_toggled(xml,1)
    for idx in range(16):
        if xml.get_widget('outputdac%d' %(idx+1)).get_active() !=0:
            xml.get_widget('outputlabel%d' %(idx+1)).set_sensitive(True)
            xml.get_widget('start%d' %(idx+1)).set_sensitive(True)
            xml.get_widget('dyna%d' %(idx+1)).set_sensitive(True)				
        else:
            xml.get_widget('outputlabel%d' %(idx+1)).set_sensitive(False)
            xml.get_widget('start%d' %(idx+1)).set_sensitive(False)
            xml.get_widget('dyna%d' %(idx+1)).set_sensitive(False)            