from twisted.application import service, internet, strports
from twisted.words.protocols.jabber import component
from twisted.enterprise import adbapi
from twisted.web2 import server, channel, log

from twistar.registry import Registry
from twistar.dbconfig.base import InteractionBase

from gossipr import listener, website

from config import CONFIG

# connect to DB
Registry.DBPOOL = adbapi.ConnectionPool(CONFIG['db.driver'], 
                                        user=CONFIG['db.user'],
                                        passwd=CONFIG['db.pass'],
                                        db=CONFIG['db.name'],
                                        host=CONFIG['db.host'])
InteractionBase.LOG = CONFIG['db.debug']

# Application set up
application = service.Application("campfirer")


# Component
host = "tcp:%s:%s" % (CONFIG['xmpp.host'], CONFIG['xmpp.port'])
sm = component.buildServiceManager(CONFIG['xmpp.gossipr.host'], CONFIG['xmpp.password'], (host))
listener.LogService().setServiceParent(sm)
s = listener.ListenerService(CONFIG)
s.setServiceParent(sm)
sm.setServiceParent(application)

