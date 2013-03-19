import gtk
import gtk.glade
import gobject

def normal_group_changed(xml):
		inputsselected = 0
		for idx in range(3):
			if xml.get_widget('input%d' %(idx+1)).get_active() != 0:
				inputsselected = inputsselected+1
				if xml.get_widget('log%d' %(idx+1)).get_active() != 0:
					logcheck = 1
				else:
					logcheck = 0
		if inputsselected == 1 and logcheck == 1:
			xml.get_widget('auto').set_sensitive(True)
			xml.get_widget('precision').set_sensitive(True)			
		else:
			xml.get_widget('auto').set_sensitive(False)
			xml.get_widget('precision').set_sensitive(False)
			xml.get_widget('constant').set_active(True)
		auto_group_changed(xml)

def auto_group_changed(xml):
		if xml.get_widget('auto').get_active()!= 0:
			xml.get_widget('precision').set_sensitive(True)
			xml.get_widget('num_samples').set_sensitive(False)
		else:
			xml.get_widget('precision').set_sensitive(False)
			xml.get_widget('num_samples').set_sensitive(True)

def a_input_changed(xml):
		for idx in range(3):
			if xml.get_widget('input%d' %(idx+1)).get_active() !=0:
				xml.get_widget('inputgain%d' %(idx+1)).set_sensitive(True)
				xml.get_widget('inputlabel%d' %(idx+1)).set_sensitive(True)
				xml.get_widget('plot2d%d' %(idx+1)).set_sensitive(True)
				xml.get_widget('plot3d%d' %(idx+1)).set_sensitive(True)
				xml.get_widget('normal%d' %(idx+1)).set_sensitive(True)
				xml.get_widget('log%d' %(idx+1)).set_sensitive(True)
			else:
				xml.get_widget('inputgain%d' %(idx+1)).set_sensitive(False)
				xml.get_widget('inputlabel%d' %(idx+1)).set_sensitive(False)
				xml.get_widget('plot2d%d' %(idx+1)).set_sensitive(False)
				xml.get_widget('plot3d%d' %(idx+1)).set_sensitive(False)
				xml.get_widget('normal%d' %(idx+1)).set_sensitive(False)
				xml.get_widget('log%d' %(idx+1)).set_sensitive(False)
