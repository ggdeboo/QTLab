# QTLab gui client
import os
import sys
import time
import optparse
adddir = os.path.join(os.getcwd(), 'source')
sys.path.insert(0, adddir)

from lib import config
config = config.create_config('qtlabgui.cfg')

from lib.network import object_sharer as objsh

from lib.misc import get_traceback
TB = get_traceback()()
import logging
f = logging.FileHandler(os.path.join(config['execdir'], 'qtlab_windows.log'), mode='a+')
formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s: %(message)s (%(filename)s:%(lineno)d)',
      datefmt='%Y-%m-%d %H:%M')
f.setFormatter(formatter)
f.setLevel(logging.DEBUG)
logging.getLogger('').addHandler(f)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
logging.getLogger('').setLevel(logging.DEBUG) 
# change this line to reduce the verbosity of the debugging messages
# logging.info('logging for windows enabled')
# logging.error('test error')
# logging.debug('debug message')

def log(msg):
    ''' just another alternative logging function '''
    f = open(config["execdir"]+"/window.log",'a+')    
    f.write(msg)
    f.write("\n")
    f.close()

def setup_windows():
    from windows import main_window
    main_window.Window()

    winpath = os.path.join(config['execdir'], 'source/gui/windows')
    for fn in os.listdir(winpath):
        if not fn.endswith('_window.py') or fn == 'main_window.py':
            continue

        dir, fn = os.path.split(fn)
        classname = os.path.splitext(fn)[0]

        if config.get('exclude_%s' % classname, False):
            logging.info('Skipping class %s', classname)
            continue

        logging.info('Loading class %s...', classname)
        start = time.time()
        codestr = "from windows import %s\n%s.Window()" % (classname, classname)
        try:
            exec codestr
        except Exception, e:
            print 'Error loading window %s' % classname
            # not very useful since it's run in a seperate file.

            TB()

        delta = time.time() - start
        logging.info('   Time = %.03s', delta)

def _close_gui_cb(*args):
    import gtk
    logging.info('Closing GUI')
    qt.config.save(delay=0)
    try:
        gtk.main_quit()
    except:
        pass
    sys.exit()

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('-d', '--disable-io', default=False, action='store_true')
    parser.add_option('-p', '--port', type=int, default=objsh.PORT,
        help='Port to connect to')
    parser.add_option('--name', default='',
        help='QTlab instance name to connect to')

    args, pargs = parser.parse_args()
    if args.name:
        config['instance_name'] = args.name

    objsh.start_glibtcp_client('localhost', port=args.port, nretry=60)
    objsh.helper.register_event_callback('disconnected', _close_gui_cb)
    import qtclient as qt
    qt.flow.connect('close-gui', _close_gui_cb)
    setup_windows()

    if args.disable_io:
        os.close(sys.stdin.fileno())
        os.close(sys.stdout.fileno())
        os.close(sys.stderr.fileno())

    # Ignore CTRL-C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    import gtk
    gtk.main()

