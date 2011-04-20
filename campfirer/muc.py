import time
import datetime
from twisted.words.protocols.jabber import jid, xmlstream
from twisted.words.protocols.jabber.xmlstream import IQ
from twisted.application import internet, service
from twisted.internet import interfaces, defer, reactor
from twisted.python import log
from twisted.words.xish import domish, xpath

from twisted.words.protocols.jabber.ijabber import IService
from twisted.words.protocols.jabber import component

from zope.interface import Interface, implements

#from campfirer.models import Room, Message

class LogService(component.Service):
    def transportConnected(self, xmlstream):
        xmlstream.rawDataInFn = self.rawDataIn
        xmlstream.rawDataOutFn = self.rawDataOut
        
    def rawDataIn(self, buf):
        log.msg("%s - RECV: %s" % (str(time.time()), unicode(buf, 'utf-8').encode('ascii', 'replace')))
        
    def rawDataOut(self, buf):
        log.msg("%s - SEND: %s" % (str(time.time()), unicode(buf, 'utf-8').encode('ascii', 'replace')))
        

class MUCService(component.Service):
    implements(IService)

    def __init__(self, config):
        self.config = config
        self.rooms = {}
        self.jid = "listener@%s/%s" % (self.config['xmpp.gossipr.host'], self.config['xmpp.gossipr.resource'])


    def iq(self, type='get'):
        r = IQ(self.xmlstream, type)
        r['from'] = self.jid
        return r


    def presence(self, sendto):
        p = domish.Element((None, 'presence'))
        p['to'] = sendto
        p['from'] = self.jid
        return p
        

    def componentConnected(self, xmlstream):
        self.jabberId = xmlstream.authenticator.otherHost
        self.xmlstream = xmlstream
        self.xmlstream.addObserver("/message", self.onMessage, 1)

        iq = self.iq()
        iq.addElement('query', 'http://jabber.org/protocol/disco#items')
        iq.send(self.config['xmpp.muc.host']).addCallback(self.updateRoomList)


    def updateRoomList(self, roomlist):
        rooms = []
        for room in roomlist.firstChildElement().elements():
            rooms.append((room['jid'], room['name']))

        def setID(room):
            self.rooms[unicode(room.jid)] = (room.id, room.name)

        def addRooms(r):
            room = r.pop()
            d = Room.createIfNonexistant(room[0], room[1]).addCallback(setID)
            if len(r) > 0:
                return d.addCallback(lambda _: addRooms(r))
            return d

        addRooms(rooms).addCallback(lambda _: self.joinRooms())


    def joinRooms(self):
        for jid in self.rooms.keys():
            if len(self.config['rooms']) == 0 or self.config['rooms'].has_key(jid):
                p = self.presence("%s/%s" % (jid, 'gossipr'))
                p.addElement('x', 'http://jabber.org/protocol/muc')
                self.xmlstream.send(p)


    def onMessage(self, msg):
        jidparts = jid.parse(msg['from'])
        userhost = "%s@%s" % (jidparts[0], jidparts[1])
        
        if self.rooms.has_key(userhost):
            room_id = self.rooms[userhost][0]
            body = xpath.queryForString("/message/body", msg)
            return Message(speaker=jidparts[2], message=body, room_id=room_id, created_at=datetime.datetime.now()).save()
