from twisted.application import service, internet, strports
from twisted.words.protocols.jabber import component

from campfirer import muc

from config import CONFIG

# Application set up
application = service.Application("campfirer")

# Component
host = "tcp:%s:%s" % (CONFIG['xmpp.host'], CONFIG['xmpp.port'])
sm = component.buildServiceManager(CONFIG['xmpp.muc.host'], CONFIG['xmpp.muc.password'], (host))
muc.LogService().setServiceParent(sm)
s = muc.MUCService(CONFIG)
s.setServiceParent(sm)
sm.setServiceParent(application)

