from twisted.words.protocols.jabber import client, jid
from twisted.words.xish import domish
from twisted.words.protocols.jabber import xmlstream
from twisted.names.srvconnect import SRVConnector
from twisted.internet import reactor
from twisted.python import log

import sys
import time

from config import CONFIG

log.startLogging(sys.stdout)

class XMPPClientConnector(SRVConnector):
    def __init__(self, reactor, domain, factory):
        SRVConnector.__init__(self, reactor, 'xmpp-client', domain, factory)


    def pickServer(self):
        host, port = SRVConnector.pickServer(self)

        if not self.servers and not self.orderedServers:
            # no SRV record, fall back..
            port = 5222

        return host, port



class Client(object):
    def __init__(self, client_jid, secret):
        f = client.XMPPClientFactory(client_jid, secret)
        f.addBootstrap(xmlstream.STREAM_CONNECTED_EVENT, self.connected)
        f.addBootstrap(xmlstream.STREAM_END_EVENT, self.disconnected)
        f.addBootstrap(xmlstream.STREAM_AUTHD_EVENT, self.authenticated)
        f.addBootstrap(xmlstream.INIT_FAILED_EVENT, self.init_failed)
        connector = XMPPClientConnector(reactor, client_jid.host, f)
        connector.connect()


    def rawDataIn(self, buf):
        log.msg("RECV: %s" % unicode(buf, 'utf-8').encode('ascii', 'replace'))


    def rawDataOut(self, buf):
        log.msg("SEND: %s" % unicode(buf, 'utf-8').encode('ascii', 'replace'))


    def connected(self, xs):
        log.msg("connected")
        self.xmlstream = xs
        xs.rawDataInFn = self.rawDataIn
        xs.rawDataOutFn = self.rawDataOut


    def disconnected(self, xs):
        log.msg("disconnected")


    def authenticated(self, xs):
        log.msg('authed')
        presence = domish.Element((None, 'presence'))
        xs.send(presence)

        presence = domish.Element((None, 'presence'))
        presence['from'] = CONFIG['jid']
        presence['to'] = CONFIG['room']
        x = presence.addElement('x', 'http://jabber.org/protocol/muc')
        x.addElement('password', content=CONFIG['roompasswd'])
        xs.send(presence)
        reactor.callLater(10, self.say, "hello there %i" % time.time())


    def say(self, msgtxt):
        msg = domish.Element((None, 'message'))
        msg['from'] = CONFIG['jid']
        msg['to'] = jid.JID(CONFIG['room']).userhost()
        msg['type'] = "groupchat"
        msg.addElement('body', content=msgtxt)
        self.xmlstream.send(msg)
        

    def init_failed(self, failure):
        log.err("Initialization failed.")
        log.err(failure)
        self.xmlstream.sendFooter()


c = Client(jid.JID(CONFIG['jid']), CONFIG['password'])
reactor.run()
        
