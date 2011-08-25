from twisted.application import service, internet, strports
from twisted.words.protocols.jabber import component
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile

import os

from campfirer import muc

from config import CONFIG

# Application set up
application = service.Application("campfirer")

# Set up logging
if CONFIG.has_key('campfirer.logdir'):
    if not os.path.exists(CONFIG['campfirer.logdir']):
        os.mkdir(CONFIG['campfirer.logdir'])
    logfile = DailyLogFile("campfirer.log", CONFIG['campfirer.logdir'])
    application.setComponent(ILogObserver, FileLogObserver(logfile).emit)

# Component
host = "tcp:%s:%s" % (CONFIG['xmpp.host'], CONFIG['xmpp.port'])
sm = component.buildServiceManager(CONFIG['xmpp.muc.host'], CONFIG['xmpp.muc.password'], (host))
muc.LogService().setServiceParent(sm)
s = muc.MUCService(CONFIG)
s.setServiceParent(sm)
sm.setServiceParent(application)

