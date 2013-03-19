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
		
		initgui.fill_entries(self.xml,self.settings)
		
		self.check_all()

		window.show_all() # show window and contents

		qt.windows.get('main').hide()
		
	def	blank_activate(self):
		self.settings = {'checkRF1': 0,               # EXPERIMENT
				 'checkRF2': 0,
				 'checkMW': 0,
				 'checkMag': 0,
				 'checkTemp': 0,
				 'checkLaser': 0,
				 'addr': [],
				 'magrate': 0,
				 'pol': [],
				 'pause1': 0,
				 'pause2': 0,
				 'current_lim': 0,
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
		else:
			self.xml.get_widget('addr1').set_sensitive(False)
			for idx in range(16):
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
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.MWpos,'tBurst')
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.MWpos+1,'MWfreq')
				self.xml.get_widget('outputdac%d' %(idx+1)).insert_text(instrumentsused.MWpos+2,'MWpower')
		else:
			self.xml.get_widget('addr3').set_sensitive(False)
			for idx in range(16):
				self.xml.get_widget('outputdac%d' %(idx+1)).remove_text(instrumentsused.MWpos+2)
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
		# Get entries and save them. Then DONT close the input-window.
		self.blank_activate()
		initgui.get_entries(self.xml,self.settings)
		self.pkl_out_file = open('cleanlastsettings.pkl', 'wb')
		pickle.dump(self.settings, self.pkl_out_file)
		self.pkl_out_file.close()

		if self.settings['number_of_measurements']==0:
			print 'no measurement selected'
				
##		self.checkMW = self.settings['checkMW']
##		self.checkRF1 = self.settings['checkRF1']		
##		self.checkRF2 = self.settings['checkRF2']
##		self.checkMag = self.settings['checkMag']
##		self.checkTemp = self.settings['checkTemp']
##		self.checkLaser = self.settings['checkLaser']		

		# Create instruments 'dac' used as a general term, can be time/field etc
##		print 'loading instruments...'
####		self.ivvi = qt.instruments.create('ivvi','IVVI',address='COM1')
##		print 'dacs OK'
####		self.NIDev1 = qt.instruments.create('NIDev1','NI_DAQ',id='Dev1',samples=self.settings['num_samples'],freq=self.settings['samplerate'])
##		print 'adcs OK'

		useinstruments.createinstruments(self.settings)
		
##		if self.checkRF1:
##			try:
##				print self.HPPulse1.get_all()
##			except:
##				print 'Pulser 1 not set up yet...'
##				self.HPPulse1 = qt.instruments.create('HPPulse1','HP_8131A',address=self.settings['addr1'],reset=False)
##			print 'Pulser 1 OK'
##
##		if self.checkRF2:
##			try:
##				print self.HPPulse2.get_all()
##			except:
##				print 'Pulser 2 not set up yet...'
##				self.HPPulse2 = qt.instruments.create('HPPulse2','HP_8131A',address=self.settings['addr2'],reset=False)
##			print 'Pulser 2 OK'
##
##		if self.checkMW:
##			try:
##				print self.MWgen.get_all()
##			except:
##				print 'MW generator not set up yet...'
##				self.MWgen = qt.instruments.create('MWgen','Agilent_E8257C',address=self.settings['addr3'],reset=False)
##			print 'MW generator OK'
##			
##		if self.checkMag:
##			try:
##				print self.OXMag.get_all()
##			except:
##				print 'Magnet not set up yet...'
##				self.OXMag = qt.instruments.create('OXMag','OxfordInstruments_IPS120',address=self.settings['addr4'])
##			print 'Magnet OK'
##
##		if self.checkTemp:
##			##try:
##				##print self.OXtemp.get_all()
##			##except:
##				##print 'Instrument not set up yet...'
##				##self.OXtemp = qt.instruments.create('?','?',address=self.settings['addr5'])
##			print 'Temperature controller cannot be used at the moment'
##
##		if self.checkLaser:
##			try:
##				print self.jdsu.get_all()
##			except:
##				print 'Laser not set up yet...'
##				self.jdsu = qt.instruments.create('jdsu','JDSU_SWS15101',address=self.settings['addr6'])
##			print 'Laser OK'

		print 'All instruments loaded.'

		#initialise things
##		if self.checkMag:
##			self.OXMag.init_magnet(min(self.settings['magrate'],1))	#specify sweeprate in T/min	hardlimit of 1T/min

		#!! DONT Ramp all dacs back to zero!!
		
##		pauseT1 = float(self.settings['pause1'])
##		pauseT2 = float(self.settings['pause2'])
##
##		CurrentLim = float(self.settings['current_lim'])

		measurementvectors.createvectors(self.settings)
				
## 		v_dac = []
## 		v_vec = []
##		number_of_sweeps = self.settings['number_of_sweeps']
##		number_of_inputs = self.settings['number_of_measurements']
##
##		# Set gain		
##		self.I_gain = []
##		for idx in range(3):
##			if self.settings['input'][idx] != 0:
##				self.I_gain.append(float(self.settings['inputgain'][idx]))
##			else:
##				self.I_gain.append('none')
##
##		#Create measurement vectors for dacs		
##		for idx in range(16):
##			print self.settings['outputdac'][idx]
##			if self.settings['dynamic'][idx] != 0:
##				v_dac.append('dac%d' % self.settings['outputdac'][idx])
##				incrval = abs(float(self.settings['incr'][idx]))
##				if float(self.settings['start'][idx]) - float(self.settings['stop'][idx]) > 0:
##					incrval = -1*incrval
##				v_vec.append(arange(float(self.settings['start'][idx]),float(self.settings['stop'][idx])+0.01*incrval,incrval))
##			elif self.settings['outputdac'][idx] != 0:
##				v_dac.append('dac%d' % self.settings['outputdac'][idx])
##				v_vec.append(float(self.settings['start'][idx]))
##			else:
##				v_dac.append('dac0')
##				v_vec.append([0])
##
##		instrument_array= []
##		vector_array= []
##		label_array= []
##			
##		for idx in range(number_of_sweeps):
##			for jdx in range(16):
##				if self.settings['order'][jdx] == '%d' % (idx+1):
##					instrument_array.append(v_dac[jdx])
##					vector_array.append(v_vec[jdx])
##					label_array.append(self.settings['outputlabel'][jdx])

		# Next a new data object is made.
		# The file will be placed in the folder:
		# <datadir>/<datestamp>/<timestamp>_testmeasurement/
		# and will be called:
		# <timestamp>_testmeasurement.dat
		# to find out what 'datadir' is set to, type: qt.config.get('datadir')

		measurementvectors.createdatafile(self.settings)
		
##		data = qt.Data(name=self.settings['filename'])
##
##		# Now you provide the information of what data will be saved in the
##		# datafile. A distinction is made between 'coordinates', and 'values'.
##		# Coordinates are the parameters that you sweep, values are the
##		# parameters that you readout (the result of an experiment). This
##		# information is used later for plotting purposes.
##		# Adding coordinate and value info is optional, but recommended.
##		# If you don't supply it, the data class will guess your data format.
##
##		for idx in range (self.settings['number_of_sweeps']):		
##			data.add_coordinate(name=measurementvectors.label_array[idx])
##		for idx in range (3):
##			if self.settings['input'][idx]!=0:
##				data.add_value(name=self.settings['inputlabel'][idx])
##			else:
##				data.add_value(name='no measurement')

		useinstruments.initinstruments(self.settings,measurementvectors.v_dac,measurementvectors.v_vec,measurementvectors.instrument_array)

##		for idx,dac in enumerate(v_dac):
##			if idx > (number_of_dynamic_dacs-1):
##				self.execute_set(dac,v_vec[idx])				print v_vec[idx]
##			else:
##				self.execute_set(dac,v_vec[idx][0])				print v_vec[idx][0]
		
		

##		if self.checkRF1:
##			self.HPPulse1.on(1)
##			self.HPPulse1.on(2)
##		if self.checkRF2:
##			self.HPPulse2.on(1)
##		if self.checkMW:
##			self.MWgen.on()
##		if self.checkMag:
##			heateroff = True
##			for idx in range(number_of_sweeps):
##				if instrument_array[idx] == ('dac%d' % instrumentsused.Magpos):
##					heateroff = False
##			# Switch heater off if magnet is not swept
##			if heateroff:
##				if self.OXMag.get_switch_heater() == 1:
##						self.OXMag.set_switch_heater(0)
##		if self.checkTemp:
			
##		if self.checkLaser:
			
		measurementvectors.createplots(self.settings)

##
##		# The next command will actually create the dirs and files, based
##		# on the information provided above. Additionally a settingsfile
##		# is created containing the current settings of all the instruments.
##
##		data.create_file()
##
##		# Next two plot-objects are created. First argument is the data object
##		# that needs to be plotted. To prevent new windows from popping up each
##		# measurement a 'name' can be provided so that window can be reused.
##		# If the 'name' doesn't already exists, a new window with that name
##		# will be created. For 3d plots, a plotting style is set.
##		
##		if self.settings['plot2d'][0] and self.settings['input'][0]!=0:
##			self.plot2d1=(qt.Plot2D(data, name='measure2D_1', coorddim=0, valdim=number_of_sweeps, maxtraces=2))
##		if self.settings['plot3d'][0] and number_of_sweeps > 1 and self.settings['input'][0]!=0:
##			self.plot3d1=(qt.Plot3D(data, name='measure3D_1', coorddims=(0,1), valdim=number_of_sweeps, style='image'))
##		if self.settings['plot2d'][1] and self.settings['input'][1]!=0:
##			self.plot2d2 = qt.Plot2D(data, name='measure2D_2', coorddim=0, valdim=number_of_sweeps+1, maxtraces=2)
##		if self.settings['plot3d'][1] and number_of_sweeps > 1 and self.settings['input'][1]!=0:
##			self.plot3d2 = qt.Plot3D(data, name='measure3D_2', coorddim=(0,1), valdim=number_of_sweeps+1, style='image')
##		if self.settings['plot2d'][2] and self.settings['input'][2]!=0:
##			self.plot2d3 = qt.Plot2D(data, name='measure2D_3', coorddim=0, valdim=number_of_sweeps+2, maxtraces=2)
##		if self.settings['plot3d'][2] and number_of_sweeps > 1 and self.settings['input'][2]!=0:
##			self.plot3d3 = qt.Plot3D(data, name='measure3D_3', coorddim=(0,1), valdim=number_of_sweeps+2, style='image')
##		
		qt.mstart()
		print 'measurement started...'				

		# preparation is done, now start the measurement.

		print 'BUGFIX: press ctrl-c once if graph not seen on first run'

		measurementvectors.measurementloop(self.settings)
		
##		number_of_traces = 1		
##		for idx in range(self.settings['number_of_sweeps']-1):
##			number_of_traces = number_of_traces*len(measurementvectors.vector_array[idx+1])
##
##		print('total number of traces: %d' %(number_of_traces))
##		total_traces=number_of_traces
##		starttime = time.time()		
##						
##		for v1 in vector_array[number_of_sweeps-1]:
####			execute_set(instrument_array[number_of_sweeps-1],v1)
##			if number_of_sweeps > 1:
##				for v2 in vector_array[number_of_sweeps-2]:
####					execute_set(instrument_array[number_of_sweeps-2],v2)
##					if number_of_sweeps > 2:
##						for v3 in vector_array[number_of_sweeps-3]:
####							execute_set(instrument_array[number_of_sweeps-3],v3)
##							if number_of_sweeps > 3:
##								for v4 in vector_array[number_of_sweeps-4]:
####									execute_set(instrument_array[number_of_sweeps-2],v4)
##									if number_of_sweeps > 4:
##										for v5 in vector_array[number_of_sweeps-5]:
####											execute_set(instrument_array[number_of_sweeps-5],v5)
##											self.measure_inputs()
##											data.add_data_point(v5,v4,v3,v2,v1,self.result[0],self.result[1],self.result[2])
##											self.update_2d_plots()
##											sleep(pauseT2)
##										data.new_block()
##										self.update_3d_plots()
##										sleep(pauseT1)
##										totaltime= number_of_traces*(time.time()-starttime)/(total_traces-number_of_traces+1)
##										print ('Time of measurement left: %d hours, %d minutes and %d seconds' %(floor(totaltime/3600),floor(fmod(totaltime,3600)/60),fmod(totaltime,60)))
##										number_of_traces= number_of_traces-1
##									else:
##										self.measure_inputs()
##										data.add_data_point(v4,v3,v2,v1,self.result[0],self.result[1],self.result[2])
##										self.update_2d_plots()
##										sleep(pauseT2)
##								if number_of_sweeps==4:
##									data.new_block()
##									self.update_3d_plots()
##									sleep(pauseT1)
##									totaltime= number_of_traces*(time.time()-starttime)/(total_traces-number_of_traces+1)
##									print ('Time of measurement left: %d hours, %d minutes and %d seconds' %(floor(totaltime/3600),floor(fmod(totaltime,3600)/60),fmod(totaltime,60)))
##									number_of_traces= number_of_traces-1
##							else:
##								self.measure_inputs()
##								data.add_data_point(v3,v2,v1,self.result[0],self.result[1],self.result[2])
##								self.update_2d_plots()
##								sleep(pauseT2)
##						if number_of_sweeps==3:
##							data.new_block()
##							self.update_3d_plots()
##							sleep(pauseT1)
##							totaltime= number_of_traces*(time.time()-starttime)/(total_traces-number_of_traces+1)
##							print ('Time of measurement left: %d hours, %d minutes and %d seconds' %(floor(totaltime/3600),floor(fmod(totaltime,3600)/60),fmod(totaltime,60)))
##							number_of_traces= number_of_traces-1
##					else:
##						self.measure_inputs()
##						data.add_data_point(v2,v1,self.result[0],self.result[1],self.result[2])
##						self.update_2d_plots()
##						sleep(pauseT2)
##				if number_of_sweeps==2:
##					data.new_block()
##					self.update_3d_plots()
##					sleep(pauseT1)
##					totaltime= number_of_traces*(time.time()-starttime)/(total_traces-number_of_traces+1)
##					print ('Time of measurement left: %d hours, %d minutes and %d seconds' %(floor(totaltime/3600),floor(fmod(totaltime,3600)/60),fmod(totaltime,60)))
##					number_of_traces= number_of_traces-1
##			else:
##				self.measure_inputs()
##				data.add_data_point(v1,self.result[0],self.result[1],self.result[2])
##				self.update_2d_plots()
##				sleep(pauseT2)
##
##		if self.settings['plot2d'][0] and self.settings['input'][0]!=0:		
##			plot2d1_end = qt.Plot2D(data, name='measure2D1_end', coorddim=0, valdim=number_of_sweeps, maxpoints=1e6 ,maxtraces=1e3)
##			plot2d1_end.update()
##		if self.settings['plot2d'][1] and self.settings['input'][1]!=0:		
##			plot2d2_end = qt.Plot2D(data, name='measure2D2_end', coorddim=0, valdim=number_of_sweeps+1, maxpoints=1e6 ,maxtraces=1e3)
##			plot2d2_end.update()
##		if self.settings['plot2d'][2] and self.settings['input'][2]!=0:		
##			plot2d3_end = qt.Plot2D(data, name='measure2D3_end', coorddim=0, valdim=number_of_sweeps+2, maxpoints=1e6 ,maxtraces=1e3)
##			plot2d3_end.update()

##
##		# after the measurement ends, you need to close the data file.
##
##		data.close_file()
##
##		if self.settings['plot2d'][0] and self.settings['input'][0]!=0:
##			plot2d1_end.save_png()
##		if self.settings['plot2d'][1] and self.settings['input'][1]!=0:
##			plot2d2_end.save_png()
##		if self.settings['plot2d'][2] and self.settings['input'][2]!=0:
##			plot2d3_end.save_png()
##		if self.settings['plot3d'][0] and self.settings['input'][0]!=0:
##			self.plot3d1.save_png()
##		if self.settings['plot3d'][1] and self.settings['input'][1]!=0:
##			self.plot3d2.save_png()
##		if self.settings['plot3d'][2] and self.settings['input'][2]!=0:
##			self.plot3d3.save_png()
			
		#!DONT ramp dacs back to zero!

		useinstruments.rampback(self.settings)				
##		if self.checkMW:
##			self.MWgen.off()
##			sleep(0.1)
##
##		if self.checkRF1:
##			pass
##			#self.HPPulse1.off()
##
##		if self.checkRF2:
##			#self.HPPulse2.off(1)
##			pass
##
##		if self.checkMag:
##			if self.OXMag.get_switch_heater() == 1:
##				self.OXMag.set_switch_heater(0)	

		print 'measurement finished!'
		
		print 'ALL other Voltages and Fields hanging at last value'

		qt.mend()

#-------------------------------------------------------------------------------------------------

##	def measure_inputs(self):
##		self.result=[]
##		for idx in range (3):
##			if self.settings['input'][idx] != 0:
##				if self.settings['log'][idx] !=0:
##					if self.settings['auto'] !=0:
##						print 'auto'
##						##NIDev1.set_samples(10)
##						##result_test=(NIDev1.get(self.settings['input'][idx]*(1000/I_gain[idx]))
##						##log_no_of_samples = self.settings['precision']*4780*exp(-0.0002341*abs(result_test))+6490*exp(-0.009734*abs(result_test))
##						##NIDev1.set_samples(log_no_of_samples)																														
##					self.result.append(1/8.488*sinh((idx)/self.I_gain[idx]))
##				else:
##					self.result.append((idx)/self.I_gain[idx])
##			else:
##				self.result.append(0)

##	def update_2d_plots(self):
##		if self.settings['plot2d'][0] and self.settings['input'][0]!=0:
##			self.plot2d1.update()
##		if self.settings['plot2d'][1] and self.settings['input'][1]!=0:
##			self.plot2d2.update()
##		if self.settings['plot2d'][2] and self.settings['input'][2]!=0:
##			self.plot2d3.update()
##
##	def update_3d_plots(self):
##		if self.settings['plot3d'][0] and self.settings['input'][0]!=0:
##			self.plot3d1.update()
##		if self.settings['plot3d'][1] and self.settings['input'][1]!=0:
##			self.plot3d2.update()
##		if self.settings['plot3d'][2] and self.settings['input'][2]!=0:
##			self.plot3d3.update()
## =============================================================================================== ##
			
## ========================================= Other buttons ======================================= ##
	def on_stopmeasure_clicked(self,widget):
		qt.flow.set_abort()
		print 'you want to stop - could be messy!'
		print 'attempting to switch off RF and MW'
		if self.checkMW:
			self.MWgen.off()
			sleep(0.1)
		if self.checkRF1 or self.checkRF2:
			self.HPPulse.off()
		if self.checkRF3:
			self.HPPulse.off(1)

	def on_buttonMagZero_clicked(self,widget):
		self.OXMag = qt.instruments.create('OXMag','OxfordInstruments_IPS120',address=self.settings['addr4'])
		self.OXMag.ramp_field_to_zero()
		self.OXMag.set_switch_heater(0)
		print 'Magnet ramped to zero and safe'

	def on_buttonDacZero_clicked(self,widget):
		self.ivvi = qt.instruments.create('ivvi','IVVI',address='COM1')
		print 'Ramping dacs to zero...'
		self.ivvi.set_dacs_zero()
		print 'Dacs at zero!'
## =============================================================================================== ##

##	def execute_set(self,dacnum,value):
##		if int(dacnum[3:]) == 0:								# Do nothing if nothing is specified
##			pass
##		elif int(dacnum[3:]) < 4:    							#it is a voltage DAC 1 to 4
##			self.ivvi.set(dacnum,value)
##		elif int(dacnum[3:]) < 7:    							#it is a voltage DAC 5 to 7
##			self.ivvi.set(dacnum,value)
##		elif int(dacnum[3:]) == 8:    							#it is voltage DAC 8
##			self.ivvi.set(dacnum,value*100 - 31.4)
##		elif int(dacnum[3:]) < 12:    							#it is a voltage DAC 9 to 12
##			self.ivvi.set(dacnum,value)
##		elif int(dacnum[3:]) < 15:    							#it is a voltage DAC 13 to 15
##			self.ivvi.set(dacnum,value)
##		elif int(dacnum[3:]) == 16:    							#it is voltage DAC 16
##			self.ivvi.set(dacnum,value*100 - 31.4)
##		elif int(dacnum[3:]) == instrumentsused.Magpos and self.checkMag:	#Bfield
##			self.OXMag.ramp_field_to(value)
##		elif int(dacnum[3:]) == instrumentsused.RF1pos and self.checkRF1:	#tBlock
##			self.HPPulse1.set_ch2_width(value)
##		elif int(dacnum[3:]) == 19 and self.checkRF1:			#tRepeat
##			self.HPPulse1.set_period(value)
##		elif int(dacnum[3:]) == 20 and self.checkRF2:			#tDelay
##			self.HPPulse1.set_ch1_delay(value)
##		elif int(dacnum[3:]) == 21 and self.checkRF2:			#tPulse1
##			self.HPPulse1.set_ch1_width(value)
##		elif int(dacnum[3:]) == 22 and self.checkRF2:			#tPulse2
##			self.HPPulse2.set_ch1_width(value)
##		# Scaled by the right factor, assuming a high impedance device:
##		elif int(dacnum[3:]) == 23:	
##			self.ivvi.set(('dac%d' % int(self.Vlow1Dac)), value/(0.116*1.9))
##		elif int(dacnum[3:]) == 24:
##			self.ivvi.set(('dac%d' % int(self.Vhigh1Dac)), value/(0.116*1.9))
##		elif int(dacnum[3:]) == 25:
##			self.ivvi.set(('dac%d' % int(self.Vlow2Dac)), value/(0.116*1.9))
##		elif int(dacnum[3:]) == 26:
##			self.ivvi.set(('dac%d' % int(self.Vhigh2Dac)), value/(0.116*1.9))
##		elif int(dacnum[3:]) == 27 and self.checkMW:			#MWfreq
##			self.MWgen.set_frequency(value)
##		elif int(dacnum[3:]) == 28 and self.checkMW:			#MWpow
##			self.MWgen.set_power(value)

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