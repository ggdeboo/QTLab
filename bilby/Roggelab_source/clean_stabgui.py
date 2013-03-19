#glade

#settings

#measurement

#datafile


# This interface should run automatically when you start QT-lab.

# Updated by: Sam Hile <samhile@gmail.com>, Nov 2011
# Updated by: Arjan Verduijn, Jan 2012
# Updated by: Jieyi Liu <jieyi.liu1@student.unsw.edu.au>, Feb 2012
# Updated by: Joost van der Heijden <j.vanderheijden@student.unsw.edu.au>, Mar 2012

# apologies - there is poor use of self.blah scoping, best not to create multiple instances of the class unless fixed

import gtk					#import glade for the user interface 
import gtk.glade		
import gobject			

import logging				#import other python files needed in this script
import time
import signal
from threading import Thread

import pickle				#import pickle to easy save and load files

import qt					#import qt to use the qt-lab functions

import initgui				#startup script for the user interface				
import outputwindow			#script to handle the window 'output'
import inputwindow			#script to handle the window 'input'
import instrumentsused		#script to bookkeep all the instruments used
import useinstruments		#measurement script to communicate with the instruments
import measurementvectors	#measurement script to set up the wanted measurement

class Stabgui:

## ===================================== Initialization ===================================== ##	
	def __init__(self):
		qt.windows.get('main').hide()

		self.xml = gtk.glade.XML('clean_stabgui.glade', 'window')
		window = self.xml.get_widget('window')

		self.xml.signal_autoconnect(self) # connect signals from glade to python
		
		initgui.initialize_gui(self.xml)
		
		pkl_in_file = open('cleanlastsettings.pkl', 'rb')
		self.blank_activate()
		self.settings = pickle.load(pkl_in_file)
		pkl_in_file.close()
		
		initgui.fill_entries1(self.xml,self.settings)
		self.check_all()
		initgui.fill_entries2(self.xml,self.settings)
		self.check_all()

		window.show_all() # show window and contents
		self.listlength = 0
		self.listsettings = []
		self.exptime = []
		
		qt.windows.get('main').hide()
		
	def	blank_activate(self):
		self.settings = {'checkRF1': 0,               # EXPERIMENT
				 'RF1pos': 0,
				 'checkRF2': 0,
				 'RF2pos': 0,
				 'checkMW': 0,
				 'MWpos': 0,
				 'checkMag': 0,
				 'Magpos': 0,
				 'checkTemp': 0,
				 'Temppos': 0,
				 'checkLaser': 0,
				 'Laserpos': 0,
				 'addr': [],
				 'magrate': 0,
				 'pol': [],
				 'pause1': 0,
				 'pause2': 0,
				 'filename': '',
				 'outputdac': [],               # OUTPUT
				 'outputlabel': [],
				 'start': [],
				 'dynamic': [],
				 'order': [],
				 'stop': [],
				 'incr': [],
				 'number_of_outputs': 0,
				 'number_of_sweeps': 0,
				 'input': [],                   # INPUT
				 'inputgain': [],
				 'inputlabel': [],
				 'plot2d': [],
				 'plot3d': [],
				 'normal': [],
				 'log': [],
				 'samplerate': 0,
				 'constant': 0,
				 'auto': 0,
				 'num_samples': 0,
				 'precision': 0,
				 'number_of_measurements': 0}

	def check_all(self):
		self.on_checkRF1_toggled(1)
		self.on_checkRF2_toggled(1)
		self.on_checkMW_toggled(1)
		self.on_checkMag_toggled(1)
		self.on_checkTemp_toggled(1)
		self.on_checkLaser_toggled(1)
		outputwindow.a_dyna_toggled(self.xml,1)
		outputwindow.a_outputdac_changed(self.xml)
		inputwindow.a_input_changed(self.xml)
		inputwindow.normal_group_changed(self.xml)
		inputwindow.auto_group_changed(self.xml)		
## =============================================================================================== ##

## ===================================== File window buttons ===================================== ##
	def on_new_activate(self,widget):
		self.blank_activate()
		initgui.fill_entries(self.xml,self.settings)
		self.check_all()
		
	def on_saveas_activate(self,widget):
		self.blank_activate()
		initgui.get_entries(self.xml,self.settings)
		self.dialog = gtk.FileChooserDialog("Save as..",
											self.window,
											gtk.FILE_CHOOSER_ACTION_SAVE,
											(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
											gtk.STOCK_OK, gtk.RESPONSE_OK))
		filter = gtk.FileFilter()
		filter.set_name("Pickle files")
		filter.add_pattern("*.pkl")
		self.dialog.add_filter(filter)
		response = self.dialogrun()
		if response == gtk.RESPONSE_OK:
			self.pkl_out_file = open(self.dialog.get_filename(), 'wb')
			pickle.dump(self.settings, self.pkl_out_file)
			self.pkl_out_file.close() 
		elif response == gtk.RESPONSE_CANCEL:
			print 'Closed, no file saved'
		self.dialog.destroy()

	def on_save_activate(self,widget):
		self.blank_activate()
		initgui.get_entries(self.xml,self.settings)
		self.pkl_out_file = open('cleanlastsettings.pkl', 'wb')
		pickle.dump(self.settings, self.pkl_out_file)
		self.pkl_out_file.close()

	def on_open_activate(self,widget):
		self.dialog = gtk.FileChooserDialog("Open..",
											self.window,
											gtk.FILE_CHOOSER_ACTION_OPEN,
											(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
											gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		filter = gtk.FileFilter()
		filter.set_name("Pickle files")
		filter.add_pattern("*.pkl")
		self.dialog.add_filter(filter)
		response = self.dialog.run()
		if response == gtk.RESPONSE_OK:
			self.pkl_in_file = open(self.dialog.get_filename(), 'rb')
			self.settings = pickle.load(self.pkl_in_file)
			self.pkl_in_file.close()
			initgui.fill_entries(self.xml,self.settings)
		elif response == gtk.RESPONSE_CANCEL:
			print 'Closed, no file opened'
		self.dialog.destroy()
		self.check_all()

	def on_exit_activate(self,widget):
		self.window.destroy()
## =============================================================================================== ##

## ================================== Experiment window buttons ================================== ##
	def on_checkRF1_toggled(self,widget):
		instrumentsused.dac_positions(self.xml)
		if self.xml.get_widget('checkRF1').get_active() != 0:
			self.xml.get_widget('addr1').set_sensitive(True)
			for idx in range(16):
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.RF1pos,'tRepeat')
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.RF1pos+1,'tDelay')
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.RF1pos+2,'tPulse1')
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.RF1pos+3,'tBlock')
		else:
			self.xml.get_widget('addr1').set_sensitive(False)
			for idx in range(16):
				self.xml.get_widget('outputdac%d' %(idx+1)).remove_text(instrumentsused.RF1pos+3)				
				self.xml.get_widget('outputdac%d' %(idx+1)).remove_text(instrumentsused.RF1pos+2)
				self.xml.get_widget('outputdac%d' %(idx+1)).remove_text(instrumentsused.RF1pos+1)
				self.xml.get_widget('outputdac%d' %(idx+1)).remove_text(instrumentsused.RF1pos)

	def on_checkRF2_toggled(self,widget):
		instrumentsused.dac_positions(self.xml)
		if self.xml.get_widget('checkRF2').get_active() != 0:
			self.xml.get_widget('addr2').set_sensitive(True)
			for idx in range(16):
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.RF2pos,'tPulse2')
		else:
			self.xml.get_widget('addr2').set_sensitive(False)
			for idx in range(16):
					self.xml.get_widget('outputdac%d' %(idx+1)).remove_text(instrumentsused.RF2pos)
			
	def on_checkMW_toggled(self,widget):
		instrumentsused.dac_positions(self.xml)
		if self.xml.get_widget('checkMW').get_active() != 0:
			self.xml.get_widget('addr3').set_sensitive(True)
			for idx in range(16):
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.MWpos,'MWfreq')
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.MWpos+1,'MWpower')
		else:
			self.xml.get_widget('addr3').set_sensitive(False)
			for idx in range(16):
				self.xml.get_widget('outputdac%d' %(idx+1)).remove_text(instrumentsused.MWpos+1)
				self.xml.get_widget('outputdac%d' %(idx+1)).remove_text(instrumentsused.MWpos)
			
	def on_checkMag_toggled(self,widget):
		instrumentsused.dac_positions(self.xml)
		if self.xml.get_widget('checkMag').get_active() != 0:
			self.xml.get_widget('buttonMagZero').set_sensitive(True)
			self.xml.get_widget('addr4').set_sensitive(True)
			self.xml.get_widget('magrate').set_sensitive(True)
			for idx in range(16):
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.Magpos,'Bfield')			
		else:
			self.xml.get_widget('buttonMagZero').set_sensitive(False)
			self.xml.get_widget('addr4').set_sensitive(False)
			self.xml.get_widget('magrate').set_sensitive(False)
			for idx in range(16):
				self.xml.get_widget('outputdac%d' %(idx+1)).remove_text(instrumentsused.Magpos)

	def on_checkTemp_toggled(self,widget):
		instrumentsused.dac_positions(self.xml)
		if self.xml.get_widget('checkTemp').get_active() != 0:
			self.xml.get_widget('addr5').set_sensitive(True)
			for idx in range(16):
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.Temppos,'Temperature')			
		else:
			self.xml.get_widget('addr5').set_sensitive(False)
			for idx in range(16):
				self.xml.get_widget('outputdac%d' %(idx+1)).remove_text(instrumentsused.Temppos)			
			
	def on_checkLaser_toggled(self,widget):
		instrumentsused.dac_positions(self.xml)
		if self.xml.get_widget('checkLaser').get_active() != 0:
			self.xml.get_widget('addr6').set_sensitive(True)
			for idx in range(16):
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.Laserpos,'Laser_wavelength')
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.Laserpos+1,'Laser_power')
		else:
			self.xml.get_widget('addr6').set_sensitive(False)
			for idx in range(16):
				self.xml.get_widget('outputdac%d' %(idx+1)).remove_text(instrumentsused.Laserpos+1)
				self.xml.get_widget('outputdac%d' %(idx+1)).remove_text(instrumentsused.Laserpos)
## =============================================================================================== ##

## ==================================== Output window buttons ==================================== ##
	def on_dyna1_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,1)
	def on_dyna2_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,2)
	def on_dyna3_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,3)
	def on_dyna4_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,4)
	def on_dyna5_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,5)
	def on_dyna6_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,6)
	def on_dyna7_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,7)
	def on_dyna8_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,8)
	def on_dyna9_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,9)
	def on_dyna10_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,10)
	def on_dyna11_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,11)
	def on_dyna12_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,12)
	def on_dyna13_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,13)
	def on_dyna14_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,14)
	def on_dyna15_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,15)
	def on_dyna16_toggled(self,widget):
		outputwindow.a_dyna_toggled(self.xml,16)
	def on_outputdac1_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac2_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac3_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac4_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac5_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac6_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac7_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac8_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac9_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac10_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac11_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac12_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac13_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac14_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac15_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
	def on_outputdac16_changed(self,widget):
		outputwindow.a_outputdac_changed(self.xml)
## =============================================================================================== ##

## ===================================== Input window buttons ==================================== ##
	def on_normal1_toggled(self,widget):
		inputwindow.normal_group_changed(self.xml)
	def on_normal2_toggled(self,widget):
		inputwindow.normal_group_changed(self.xml)		
	def on_normal3_toggled(self,widget):
		inputwindow.normal_group_changed(self.xml)		
	def on_log1_toggled(self,widget):
		inputwindow.normal_group_changed(self.xml)
	def on_log2_toggled(self,widget):
		inputwindow.normal_group_changed(self.xml)
	def on_log3_toggled(self,widget):
		inputwindow.normal_group_changed(self.xml)		
	def on_auto_toggled(self,widget):
		inputwindow.auto_group_changed(self.xml)
	def on_constant_toggled(self,widget):
		inputwindow.auto_group_changed(self.xml)
	def on_input1_changed(self,widget):
		inputwindow.a_input_changed(self.xml)
		inputwindow.normal_group_changed(self.xml)
	def on_input2_changed(self,widget):
		inputwindow.a_input_changed(self.xml)
		inputwindow.normal_group_changed(self.xml)
	def on_input3_changed(self,widget):
		inputwindow.a_input_changed(self.xml)
		inputwindow.normal_group_changed(self.xml)
## =============================================================================================== ##

## ======================================== Measure button ======================================= ##
	def on_measure_clicked(self,widget):

		from numpy import pi, random, arange, size		
		# Get entries and save them.
		self.blank_activate()
		initgui.get_entries(self.xml,self.settings)
		self.settings['RF1pos'] = instrumentsused.RF1pos
		self.settings['RF2pos'] = instrumentsused.RF2pos
		self.settings['MWpos'] = instrumentsused.MWpos
		self.settings['Magpos'] = instrumentsused.Magpos
		self.settings['Temppos'] = instrumentsused.Temppos
		self.settings['Laserpos'] = instrumentsused.Laserpos		
		self.pkl_out_file = open('cleanlastsettings.pkl', 'wb')
		pickle.dump(self.settings, self.pkl_out_file)
		self.pkl_out_file.close()

		if self.settings['number_of_measurements']==0:
			print 'no measurement selected'
		else:
			self.add_to_waitinglist()

	def startmeasurement(self):		
		useinstruments.createinstruments(self.listsettings[0])

		print 'All instruments loaded.'

		measurementvectors.createvectors(self.listsettings[0])
		measurementvectors.createdatafile(self.listsettings[0])
		useinstruments.initinstruments(self.listsettings[0],measurementvectors.v_dac,measurementvectors.v_vec,measurementvectors.instrument_array)
		measurementvectors.createplots(self.listsettings[0])

		qt.mstart()
		
		print 'measurement started...'				
		measurementvectors.measurementloop(self.listsettings[0])
		useinstruments.rampback(self.listsettings[0])				
		print 'measurement finished!'
		print 'ALL other Voltages and Fields hanging at last value'

		qt.mend()
		self.delete_from_waitinglist()
## =============================================================================================== ##

## ========================================== Waitinglist ======================================== ##
	def add_to_waitinglist(self):
		self.listsettings.append(self.settings)
		self.listlength=self.listlength+1
		self.calculate_exptime()
		print 'measurement added'
		self.update_waitinglist()
		if self.listlength == 1:
			self.startmeasurement()

	def calculate_exptime(self):
		measurementpoints=1
		for idx in range(16):
			if self.settings['dynamic'][idx] != 0 and self.settings['outputdac'][idx] != 0:
				measurementpoints=measurementpoints*(abs(float(self.settings['start'][idx]) - float(self.settings['stop'][idx]))/abs(float(self.settings['incr'][idx])))
		no_of_seconds = floor(measurementpoints*(float(self.settings['num_samples'])/(float(self.settings['samplerate']))+float(self.settings['pause2'])))
		self.exptime.append(2.5*no_of_seconds) #2.5 is a calibrationfactor

	def delete_from_waitinglist(self):
		for idx in range(self.listlength-1):
			self.listsettings[idx] = self.listsettings[idx+1]
			self.exptime[idx] = self.exptime[idx+1]
		self.listsettings.pop(self.listlength-1)
		self.exptime.pop(self.listlength-1)
		self.listlength=self.listlength-1
		self.update_waitinglist()
		if self.listlength != 0:
			self.startmeasurement()

	def update_waitinglist(self):
		totaltime = 0
		for idx in range(10):
			if idx < self.listlength:
				self.xml.get_widget('expno%d' %(idx+1)).set_text('%d' % (idx+1))
				self.xml.get_widget('expname%d' %(idx+1)).set_text('%s' % self.listsettings[idx]['filename'])
				self.xml.get_widget('exptime%d' %(idx+1)).set_text('%d min %d sec' % (self.exptime[idx]/60, fmod(self.exptime[idx],60)))
				totaltime = totaltime + self.exptime[idx]
			else:
				self.xml.get_widget('expno%d' %(idx+1)).set_text('')
				self.xml.get_widget('expname%d' %(idx+1)).set_text('')
				self.xml.get_widget('exptime%d' %(idx+1)).set_text('')
		self.xml.get_widget('tottime').set_text('%d min %d sec' % (totaltime/60, fmod(totaltime,60)))
		

	def on_delexp_clicked(self,widget):
		delete_exp_no = int(self.xml.get_widget('delexpno').get_text())
		if delete_exp_no > self.listlength:
			print 'experiment not in list'
		elif delete_exp_no < 2:
			print 'experiment cannot be stopped'
		else:
			for idx in range (self.listlength-delete_exp_no):
				self.listsettings[idx+delete_exp_no-1] = self.listsettings[idx+delete_exp_no]
				self.exptime[idx+delete_exp_no-1] = self.exptime[idx+delete_exp_no]
			self.listsettings.pop(self.listlength-1)
			self.exptime.pop(self.listlength-1)
			self.listlength=self.listlength-1
			self.update_waitinglist()
				
## =============================================================================================== ##
			
## ========================================= Other buttons ======================================= ##
	def on_stopmeasure_clicked(self,widget):
		qt.flow.set_abort()
		print 'you want to stop - could be messy!'
		print 'attempting to switch off RF and MW'
		useinstruments.rampback(self.listssettings[0])

	def on_buttonMagZero_clicked(self,widget):
		useinstruments.OXMag.ramp_field_to_zero()
		useinstruments.OXMag.set_switch_heater(0)
		print 'Magnet ramped to zero and safe'

	def on_buttonDacZero_clicked(self,widget):
		try:
			print useinstruments.ivvi.get_all()
		except:
			useinstruments.ivvi = qt.instruments.create('ivvi','IVVI',address='COM1')
		print 'Ramping dacs to zero...'
		useinstruments.ivvi.set_dacs_zero()
		print 'Dacs at zero!'
## =============================================================================================== ##

## =============================================================================================== ##
if __name__ == '__main__':
	signal.signal(signal.SIGINT, signal.SIG_DFL) # ^C exits the application
	try: 	# Import Psyco if available
		import psyco
		psyco.full()
	except ImportError:
		pass	
	Stabgui()
	gtk.main()
## =============================================================================================== ##