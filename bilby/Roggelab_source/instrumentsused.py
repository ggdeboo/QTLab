import gtk
import gtk.glade
import gobject

def dac_positions(xml):
    global RF1pos
    RF1pos = 17
    global RF2pos
    RF2pos = 21
    global MWpos
    MWpos = 22
    global Magpos
    Magpos = 24
    global Temppos
    Temppos = 25
    global Laserpos
    Laserpos = 26
    if xml.get_widget('checkRF1').get_active() == 0:
        RF2pos   = RF2pos - 4
        MWpos    = MWpos - 4
        Magpos   = Magpos - 4
        Temppos  = Temppos - 4
        Laserpos = Laserpos - 4
    if xml.get_widget('checkRF2').get_active() == 0:
        MWpos    = MWpos - 1
        Magpos   = Magpos - 1
        Temppos  = Temppos - 1
        Laserpos = Laserpos - 1
    if xml.get_widget('checkMW').get_active() == 0:
        Magpos   = Magpos - 2
        Temppos  = Temppos - 2
        Laserpos = Laserpos - 2
    if xml.get_widget('checkMag').get_active() == 0:
        Temppos  = Temppos - 1
        Laserpos = Laserpos - 1
    if xml.get_widget('checkTemp').get_active() == 0:
        Laserpos = Laserpos - 1