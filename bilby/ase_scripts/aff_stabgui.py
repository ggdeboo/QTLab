import gtk
import gtk.glade
import gobject
import time
import signal
from threading import Thread
import pickle

class Stabgui:
	def __init__(self):
		self.pkl_in_file = open('lastsettings.pkl', 'rb')
		self.settings = pickle.load(self.pkl_in_file)
		self.pkl_in_file.close()
		self.xml = gtk.glade.XML('stabgui.glade', 'window')
		self.window = self.xml.get_widget('window')
		self.initialize_gui()
		self.fill_entries()
		self.xml.signal_autoconnect(self) # connect signals from glade to python
		self.window.show_all() # show window and contents

	def initialize_gui(self):
		# Create ListStores
		self.dacstore = gtk.ListStore(gobject.TYPE_STRING)
		self.dacstore.append(['none'])
		for idx in range(16):
			self.dacstore.append(['dac%d' % (idx+1)])
		self.polstore = gtk.ListStore(gobject.TYPE_STRING)
		self.polstore.append(['NEG'])
		self.polstore.append(['BIP'])
		self.polstore.append(['POS'])
		self.inputstore = gtk.ListStore(gobject.TYPE_STRING)
		self.inputstore.append(['none'])
		for idx in range(16):
			self.inputstore.append(['ai%d' % (idx)])
		for idx in range(16):
			self.xml.get_widget('outputdac%d' % (idx+1)).set_model(self.dacstore)
			self.xml.get_widget('outputdac%d' % (idx+1)).set_text_column(0)
			self.xml.get_widget('outputdac%d' % (idx+1)).set_active(0)
		for idx in range(3):
			self.xml.get_widget('input%d' % (idx+1)).set_model(self.inputstore)
			self.xml.get_widget('input%d' % (idx+1)).set_text_column(0)
			self.xml.get_widget('input%d' % (idx+1)).set_active(0)

	def fill_entries(self):
		# Reset all values
		for idx in range(16):
			self.xml.get_widget('outputdac%d' % (idx+1)).set_active(0)
			self.xml.get_widget('start%d' % (idx+1)).set_text('')
		for idx in range(2):
			self.xml.get_widget('stop%d' % (idx+1)).set_text('')
			self.xml.get_widget('incr%d' % (idx+1)).set_text('')
		for idx in range(3):
			self.xml.get_widget('input%d' % (idx+1)).set_active(0)
			self.xml.get_widget('inputgain%d' % (idx+1)).set_text('')
			self.xml.get_widget('inputlabel%d' % (idx+1)).set_text('')
		# Set output dac values
		for idx,s in enumerate(self.settings['outputdac']):
			self.xml.get_widget('outputdac%d' % (idx+1)).set_active(s)
		# Set ouput start values
		for idx,s in enumerate(self.settings['start']):
			if self.xml.get_widget('outputdac%d' % (idx+1)).get_active() != 0:
				self.xml.get_widget('start%d' % (idx+1)).set_text('%7.2f' %s)
		# Set output stop values
		for idx,s in enumerate(self.settings['stop']):
			if self.xml.get_widget('outputdac%d' % (idx+1)).get_active() != 0:
				self.xml.get_widget('stop%d' % (idx+1)).set_text('%7.2f' %s)
		# Set output increment values
		for idx,s in enumerate(self.settings['incr']):
			if self.xml.get_widget('outputdac%d' % (idx+1)).get_active() != 0:
				self.xml.get_widget('incr%d' % (idx+1)).set_text('%4.2f' %s)
		# Set output polarity values
		for idx in range(4):
			self.xml.get_widget('pol%d' % (idx+1)).set_model(self.polstore)
			self.xml.get_widget('pol%d' % (idx+1)).set_text_column(0)
		for idx,s in enumerate(self.settings['pol']):
			self.xml.get_widget('pol%d' % (idx+1)).set_active(s)
		# Set input channels
		for idx,s in enumerate(self.settings['input']):
			self.xml.get_widget('input%d' % (idx+1)).set_active(s)
		# Set input gain
		for idx,s in enumerate(self.settings['inputgain']):
			if self.xml.get_widget('input%d' % (idx+1)).get_active() != 0:
				self.xml.get_widget('inputgain%d' % (idx+1)).set_text('%7.0f' %s)
		# Set input label
		for idx,s in enumerate(self.settings['inputlabel']):
			if self.xml.get_widget('input%d' % (idx+1)).get_active() != 0:
				self.xml.get_widget('inputlabel%d' % (idx+1)).set_text(s)
		# Set samplerate and number of samples
		self.xml.get_widget('samplerate').set_text('%7.0f' % self.settings['samplerate'])
		self.xml.get_widget('samples').set_text('%7.0f' % self.settings['num_samples'])
		# Set filename
		self.xml.get_widget('filename').set_text(self.settings['filename'])
		# Set checkboxes
		self.xml.get_widget('plot1').set_active(self.settings['plot2d'])
		self.xml.get_widget('plot2').set_active(self.settings['plot3d'])

	def get_entries(self):
		self.settings = {'outputdac': [],
						 'start': [],
						 'stop': [],
						 'incr': [],
						 'pol': [],
						 'input': [],
						 'inputgain': [],
						 'inputlabel': [],
						 'samplerate': '',
						 'num_samples': '',
						 'filename': '',
						 'plot2d': 0,
						 'plot3d': 0}
		for idx in range(16):
			if self.xml.get_widget('outputdac%d' % (idx+1)).get_active() != 0:
				self.settings['outputdac'].append(self.xml.get_widget('outputdac%d' % (idx+1)).get_active())
				self.settings['start'].append(float(self.xml.get_widget('start%d' % (idx+1)).get_text()))
			else:
				self.settings['outputdac'].append(0)
				self.settings['start'].append('none')
		for idx in range(2):
			if self.xml.get_widget('outputdac%d' % (idx+1)).get_active() != 0:
				self.settings['stop'].append(float(self.xml.get_widget('stop%d' % (idx+1)).get_text()))
				self.settings['incr'].append(float(self.xml.get_widget('incr%d' % (idx+1)).get_text()))
			else:
				self.settings['stop'].append('none')
				self.settings['incr'].append('none')
		for idx in range(4):
			self.settings['pol'].append(self.xml.get_widget('pol%d' % (idx+1)).get_active())
		for idx in range(3):
			if self.xml.get_widget('input%d' % (idx+1)).get_active() != 0:
				self.settings['input'].append(self.xml.get_widget('input%d' % (idx+1)).get_active())	
				self.settings['inputgain'].append(float(self.xml.get_widget('inputgain%d' % (idx+1)).get_text()))
				self.settings['inputlabel'].append(self.xml.get_widget('inputlabel%d' % (idx+1)).get_text())
			else:
				self.settings['input'].append(0)
				self.settings['inputgain'].append('none')
				self.settings['inputlabel'].append('none')
		self.settings['samplerate'] = float(self.xml.get_widget('samplerate').get_text())
		self.settings['num_samples'] = float(self.xml.get_widget('samples').get_text())
		self.settings['filename'] = self.xml.get_widget('filename').get_text()
		self.settings['plot2d'] = self.xml.get_widget('plot1').get_active()
		self.settings['plot3d'] = self.xml.get_widget('plot2').get_active()

	def	on_new_activate(self,widget):
		self.settings = {'outputdac': [],
						 'start': [],
						 'stop': [],
						 'incr': [],
						 'pol': [],
						 'input': [],
						 'inputgain': [],
						 'inputlabel': [],
						 'samplerate': 0,
						 'num_samples': 0,
						 'filename': '',
						 'plot2d': 0,
						 'plot3d': 0}
		self.fill_entries()
			
	def on_saveas_activate(self,widget):
		self.get_entries()
		self.dialog = gtk.FileChooserDialog("Save as..",
											self.window,
											gtk.FILE_CHOOSER_ACTION_SAVE,
											(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
											gtk.STOCK_OK, gtk.RESPONSE_OK))
		filter = gtk.FileFilter()
		filter.set_name("Pickle files")
		filter.add_pattern("*.pkl")
		self.dialog.add_filter(filter)
		response = self.dialog.run()
		if response == gtk.RESPONSE_OK:
			self.pkl_out_file = open(self.dialog.get_filename(), 'wb')
			pickle.dump(self.settings, self.pkl_out_file)
			self.pkl_out_file.close() 
		elif response == gtk.RESPONSE_CANCEL:
			print 'Closed, no file saved'
		self.dialog.destroy()
				
	def on_save_activate(self,widget):
		self.get_entries()
		self.pkl_out_file = open('lastsettings.pkl', 'wb')
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
			self.fill_entries()
		elif response == gtk.RESPONSE_CANCEL:
			print 'Closed, no file opened'
		self.dialog.destroy()

	def on_exit_activate(self,widget):
		self.window.destroy()

#-------------------------------------------------------------------------------------------------
	def on_measure_clicked(self,widget):
		from numpy import pi, random, arange, size
		# Get entries and save them. Then close the input-window.
		self.get_entries()
		self.pkl_out_file = open('lastsettings.pkl', 'wb')
		pickle.dump(self.settings, self.pkl_out_file)
		self.pkl_out_file.close()
		self.window.destroy()
		# Create instruments
		ivvi = qt.instruments.create('ivvi','IVVI',address='COM1')
		NIDev1 = qt.instruments.create('NIDev1','NI_DAQ',id='Dev1',samples=self.settings['num_samples'],freq=self.settings['samplerate'])
		# Ramp all dacs back to zero
		for idx in range(16):
			ivvi.set('dac%d' % (idx+1),0)
		# Set I gain mV/nA
		I_gain = self.settings['inputgain'][0]
		# create dacs, first two will be swepped 
		v_dac = []
		v_vec = []
		number_of_dynamic_dacs = 0
		for idx in range(2):
			if self.settings['outputdac'][idx] != 0:
				v_dac.append('dac%d' % self.settings['outputdac'][idx])
				v_vec.append(arange(self.settings['start'][idx],self.settings['stop'][idx],self.settings['incr'][idx]))
				number_of_dynamic_dacs = number_of_dynamic_dacs + 1
		# From here on it will be static dacs
		for idx in range(14):
			if self.settings['outputdac'][idx+2] != 0:
				v_dac.append('dac%d' % self.settings['outputdac'][idx+2])
				v_vec.append(self.settings['start'][idx+2])

		# Next a new data object is made.
		# The file will be placed in the folder:
		# <datadir>/<datestamp>/<timestamp>_testmeasurement/
		# and will be called:
		# <timestamp>_testmeasurement.dat
		# to find out what 'datadir' is set to, type: qt.config.get('datadir')
		data = qt.Data(name=self.settings['filename'])

		# Now you provide the information of what data will be saved in the
		# datafile. A distinction is made between 'coordinates', and 'values'.
		# Coordinates are the parameters that you sweep, values are the
		# parameters that you readout (the result of an experiment). This
		# information is used later for plotting purposes.
		# Adding coordinate and value info is optional, but recommended.
		# If you don't supply it, the data class will guess your data format.
		data.add_coordinate('V2 [mV]')
		data.add_coordinate('V1 [mV]')
		data.add_value('I [nA]')

		# Ramp static dacs
		for idx,dac in enumerate(v_dac):
			if idx > (number_of_dynamic_dacs-1):
				ivvi.set(dac,v_vec[idx])

		# The next command will actually create the dirs and files, based
		# on the information provided above. Additionally a settingsfile
		# is created containing the current settings of all the instruments.
		data.create_file()

		# Next two plot-objects are created. First argument is the data object
		# that needs to be plotted. To prevent new windows from popping up each
		# measurement a 'name' can be provided so that window can be reused.
		# If the 'name' doesn't already exists, a new window with that name
		# will be created. For 3d plots, a plotting style is set.
		if self.settings['plot2d']:
			plot2d = qt.Plot2D(data, name='measure2D', coorddim=0, valdim=2, maxtraces=1)
		if self.settings['plot3d']:
			plot3d = qt.Plot3D(data, name='measure3D', coorddims=(0,1), valdim=2, style='image')

		print 'measurement started'				
		# preparation is done, now start the measurement.
		# It is actually a simple loop.
		if number_of_dynamic_dacs == 2:
			for v1 in v_vec[0]:
				ivvi.set(v_dac[0],v1)
				sleep(0.020)
				for iv2,v2 in enumerate(v_vec[1]):
					ivvi.set(v_dac[1],v2)
					# Pause to let the current meter settle
					sleep(0.005)
					# readout
					result = NIDev1.get('ai0')*(1000/I_gain)
					# save the data point to the file, this will automatically trigger
					# the plot windows to update
					data.add_data_point(v2, v1, result)
					# the next function is necessary to keep the gui responsive. It
					# checks for instance if the 'stop' button is pushed. It also checks
					# if the plots need updating.
					if self.settings['plot2d'] and divmod(iv2,10)[1] == 0:
						plot2d.update()
				# the next line defines the end of a single 'block', which is when sweeping
				# the most inner loop finishes. An empty line is put in the datafile, and
				# the 3d plot is updated.
				data.new_block()
				if self.settings['plot3d']:
					plot3d.update()
			if self.settings['plot2d']:
				steps1 = (self.settings['stop'][0]-self.settings['start'][0])/self.settings['incr'][0]
				steps2 = (self.settings['stop'][1]-self.settings['start'][1])/self.settings['incr'][1]
				plot2d_end = qt.Plot2D(data, name='measure2D_end', coorddim=0, valdim=2, maxpoints=1e6 ,maxtraces=steps2)
				plot2d_end.update()
		# after the measurement ends, you need to close the data file.
		data.close_file()

		if self.settings['plot2d']:
			plot2d_end.save_png()
		if self.settings['plot3d']:
			plot3d.save_png()
				
		#ramp dacs back to zero
		for idx,dac in enumerate(v_dac):
			ivvi.set(dac,0)

		print 'measurement finished'
#-------------------------------------------------------------------------------------------------

	def on_stopmeasure_clicked(self,widget):
		print 'you want to stop'
				
if __name__ == '__main__':
	signal.signal(signal.SIGINT, signal.SIG_DFL) # ^C exits the application

	try: 	# Import Psyco if available
		import psyco
		psyco.full()
	except ImportError:
		pass
	
	Stabgui()
	gtk.main()