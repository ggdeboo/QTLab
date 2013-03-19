from numpy import pi,arange,floor,fmod
import signal
import useinstruments
import qt
import time

def createvectors(settings):
    global v_dac
    global v_vec
    v_dac = []
    v_vec = []
    global I_gain    
    I_gain = []
    for idx in range(3):
        if settings['input'][idx] != 0:
            I_gain.append(float(settings['inputgain'][idx]))
        else:
            I_gain.append('none')

    for idx in range(16):
        if settings['dynamic'][idx] != 0 and settings['outputdac'][idx] != 0:
            v_dac.append('dac%d' % settings['outputdac'][idx])
            incrval = abs(float(settings['incr'][idx]))
            if float(settings['start'][idx]) - float(settings['stop'][idx]) > 0:
                incrval = -1*incrval
            v_vec.append(arange(float(settings['start'][idx]),float(settings['stop'][idx])+0.01*incrval,incrval))
        elif settings['outputdac'][idx] != 0:
            v_dac.append('dac%d' % settings['outputdac'][idx])
            v_vec.append([float(settings['start'][idx])])
        else:
            v_dac.append('dac0')
            v_vec.append([0])

    global instrument_array
    global vector_array
    global label_array

    instrument_array= []
    vector_array= []
    label_array= []
        
    for idx in range(settings['number_of_sweeps']):
        for jdx in range(16):
            if settings['order'][jdx] == '%d' % (idx+1):
                instrument_array.append(v_dac[jdx])
                vector_array.append(v_vec[jdx])
                label_array.append(settings['outputlabel'][jdx])

def createdatafile(settings):
	# Next a new data object is made.
	# The file will be placed in the folder:
	# <datadir>/<datestamp>/<timestamp>_testmeasurement/
	# and will be called:
	# <timestamp>_testmeasurement.dat
	# to find out what 'datadir' is set to, type: qt.config.get('datadir')

    global data
    data = qt.Data(name=settings['filename'])

	# Now you provide the information of what data will be saved in the
	# datafile. A distinction is made between 'coordinates', and 'values'.
	# Coordinates are the parameters that you sweep, values are the
	# parameters that you readout (the result of an experiment). This
	# information is used later for plotting purposes.
	# Adding coordinate and value info is optional, but recommended.
	# If you don't supply it, the data class will guess your data format.

    for idx in range (settings['number_of_sweeps']):		
        data.add_coordinate(name=label_array[idx])
    for idx in range (3):
        if settings['input'][idx]!=0:
            data.add_value(name=settings['inputlabel'][idx])
        else:
            data.add_value(name='no measurement')

def createplots(settings):
    # The next command will actually create the dirs and files, based
    # on the information provided above. Additionally a settingsfile
    # is created containing the current settings of all the instruments.
    data.create_file()
    # Next two plot-objects are created. First argument is the data object
    # that needs to be plotted. To prevent new windows from popping up each
    # measurement a 'name' can be provided so that window can be reused.
    # If the 'name' doesn't already exists, a new window with that name
    # will be created. For 3d plots, a plotting style is set.
    if settings['plot2d'][0] and settings['input'][0]!=0:
        global plot2d1
        plot2d1=(qt.Plot2D(data, name='measure2D_%s' %(settings['inputlabel'][0]), coorddim=0, valdim=settings['number_of_sweeps'], maxtraces=2))
    if settings['plot3d'][0] and settings['number_of_sweeps'] > 1 and settings['input'][0]!=0:
        global plot3d1
        plot3d1=(qt.Plot3D(data, name='measure3D_%s' %(settings['inputlabel'][0]), coorddims=(0,1), valdim=settings['number_of_sweeps'], style='image'))
    if settings['plot2d'][1] and settings['input'][1]!=0:
        global plo2d2
        plot2d2 = qt.Plot2D(data, name='measure2D_%s' %(settings['inputlabel'][1]), coorddim=0, valdim=settings['number_of_sweeps']+1, maxtraces=2)
    if settings['plot3d'][1] and settings['number_of_sweeps'] > 1 and settings['input'][1]!=0:
        global plot3d2
        plot3d2 = qt.Plot3D(data, name='measure3D_%s' %(settings['inputlabel'][1]), coorddim=(0,1), valdim=settings['number_of_sweeps']+1, style='image')
    if settings['plot2d'][2] and settings['input'][2]!=0:
        global plot2d3
        plot2d3 = qt.Plot2D(data, name='measure2D_%s' %(settings['inputlabel'][2]), coorddim=0, valdim=settings['number_of_sweeps']+2, maxtraces=2)
    if settings['plot3d'][2] and settings['number_of_sweeps'] > 1 and settings['input'][2]!=0:
        global plot3d3
        plot3d3 = qt.Plot3D(data, name='measure3D_%s' %(settings['inputlabel'][2]), coorddim=(0,1), valdim=settings['number_of_sweeps']+2, style='image')

def measurementloop(settings):
    number_of_traces = 1		
    for idx in range(settings['number_of_sweeps']-1):
        number_of_traces = number_of_traces*len(vector_array[idx+1])

	print('total number of traces: %d' %(number_of_traces))
	total_traces=number_of_traces
	starttime = time.time()

    for v1 in vector_array[settings['number_of_sweeps']-1]:
        useinstruments.execute_set(settings,instrument_array[settings['number_of_sweeps']-1],v1)
        if settings['number_of_sweeps'] > 1:
            for v2 in vector_array[settings['number_of_sweeps']-2]:
                useinstruments.execute_set(settings,instrument_array[settings['number_of_sweeps']-2],v2)
                if settings['number_of_sweeps'] > 2:
                    for v3 in vector_array[settings['number_of_sweeps']-3]:
                        useinstruments.execute_set(settings,instrument_array[settings['number_of_sweeps']-3],v3)
                        if settings['number_of_sweeps'] > 3:
                            for v4 in vector_array[settings['number_of_sweeps']-4]:
                                useinstruments.execute_set(settings,instrument_array[settings['number_of_sweeps']-2],v4)
                                if settings['number_of_sweeps'] > 4:
                                    for v5 in vector_array[settings['number_of_sweeps']-5]:
                                        useinstruments.execute_set(settings,instrument_array[settings['number_of_sweeps']-5],v5)
                                        useinstruments.measure_inputs(settings,I_gain)
                                        data.add_data_point(v5,v4,v3,v2,v1,useinstruments.result[0],useinstruments.result[1],useinstruments.result[2])
                                        qt.msleep(float(settings['pause2']))
                                        update_2d_plots(settings)
                                    data.new_block()
                                    qt.msleep(float(settings['pause1']))
                                    update_3d_plots(settings)
                                    totaltime= number_of_traces*(time.time()-starttime)/(total_traces-number_of_traces+1)
                                    print ('Time of measurement left: %d hours, %d minutes and %d seconds' %(floor(totaltime/3600),floor(fmod(totaltime,3600)/60),fmod(totaltime,60)))
                                    number_of_traces= number_of_traces-1
                                else:
                                    useinstruments.measure_inputs(settings,I_gain)
                                    data.add_data_point(v4,v3,v2,v1,useinstruments.result[0],useinstruments.result[1],useinstruments.result[2])
                                    qt.msleep(float(settings['pause2']))
                                    update_2d_plots(settings)
                            if settings['number_of_sweeps'] == 4:
                                data.new_block()
                                qt.msleep(float(settings['pause1']))
                                update_3d_plots(settings)
                                totaltime= number_of_traces*(time.time()-starttime)/(total_traces-number_of_traces+1)
                                print ('Time of measurement left: %d hours, %d minutes and %d seconds' %(floor(totaltime/3600),floor(fmod(totaltime,3600)/60),fmod(totaltime,60)))
                                number_of_traces= number_of_traces-1
                        else:
                            useinstruments.measure_inputs(settings,I_gain)
                            data.add_data_point(v3,v2,v1,useinstruments.result[0],useinstruments.result[1],useinstruments.result[2])
                            qt.msleep(float(settings['pause2']))
                            update_2d_plots(settings)
                    if settings['number_of_sweeps']==3:
                        data.new_block()
                        qt.msleep(float(settings['pause1']))
                        update_3d_plots(settings)                        
                        totaltime= number_of_traces*(time.time()-starttime)/(total_traces-number_of_traces+1)
                        print ('Time of measurement left: %d hours, %d minutes and %d seconds' %(floor(totaltime/3600),floor(fmod(totaltime,3600)/60),fmod(totaltime,60)))
                        number_of_traces= number_of_traces-1
                else:
                    useinstruments.measure_inputs(settings,I_gain)
                    data.add_data_point(v2,v1,useinstruments.result[0],useinstruments.result[1],useinstruments.result[2])
                    qt.msleep(float(settings['pause2']))
                    update_2d_plots(settings)                    
            if settings['number_of_sweeps']==2:
                data.new_block()
                qt.msleep(float(settings['pause1']))
                update_3d_plots(settings)                
                totaltime= number_of_traces*(time.time()-starttime)/(total_traces-number_of_traces+1)
                print ('Time of measurement left: %d hours, %d minutes and %d seconds' %(floor(totaltime/3600),floor(fmod(totaltime,3600)/60),fmod(totaltime,60)))
                number_of_traces= number_of_traces-1
        else:
            useinstruments.measure_inputs(settings,I_gain)
            data.add_data_point(v1,useinstruments.result[0],useinstruments.result[1],useinstruments.result[2])
            qt.msleep(float(settings['pause2']))
            update_2d_plots(settings)            

    if settings['plot2d'][0] and settings['input'][0]!=0:
        plot2d1_end = qt.Plot2D(data, name='measure2D_%s_end' %(settings['inputlabel'][0]), coorddim=0, valdim=settings['number_of_sweeps'], maxpoints=1e6 ,maxtraces=1e3)
        plot2d1_end.update()
    if settings['plot2d'][1] and settings['input'][1]!=0:
        plot2d2_end = qt.Plot2D(data, name='measure2D_%s_end' %(settings['inputlabel'][1]), coorddim=0, valdim=settings['number_of_sweeps']+1, maxpoints=1e6 ,maxtraces=1e3)
        plot2d2_end.update()
    if settings['plot2d'][2] and settings['input'][2]!=0:
        plot2d3_end = qt.Plot2D(data, name='measure2D_%s_end' %(settings['inputlabel'][2]), coorddim=0, valdim=settings['number_of_sweeps']+2, maxpoints=1e6 ,maxtraces=1e3)
        plot2d3_end.update()

	# after the measurement ends, you need to close the data file.

   	data.close_file()

	if settings['plot2d'][0] and settings['input'][0]!=0:
		plot2d1_end.save_png()
	if settings['plot2d'][1] and settings['input'][1]!=0:
		plot2d2_end.save_png()
	if settings['plot2d'][2] and settings['input'][2]!=0:
		plot2d3_end.save_png()
	if settings['plot3d'][0] and settings['input'][0]!=0:
		plot3d1.save_png()
	if settings['plot3d'][1] and settings['input'][1]!=0:
		plot3d2.save_png()
	if settings['plot3d'][2] and settings['input'][2]!=0:
		plot3d3.save_png()

def update_2d_plots(settings):
	if settings['plot2d'][0] and settings['input'][0]!=0:
		plot2d1.update()
	if settings['plot2d'][1] and settings['input'][1]!=0:
		plot2d2.update()
	if settings['plot2d'][2] and settings['input'][2]!=0:
		plot2d3.update()

def update_3d_plots(settings):
	if settings['plot3d'][0] and settings['input'][0]!=0:
		plot3d1.update()
	if settings['plot3d'][1] and settings['input'][1]!=0:
		plot3d2.update()
	if settings['plot3d'][2] and settings['input'][2]!=0:
		plot3d3.update()