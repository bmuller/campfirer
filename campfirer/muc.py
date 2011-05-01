import time
import datetime
from twisted.words.protocols.jabber import jid, xmlstream
import twisted.words.protocols.jabber.xmlstream
from twisted.application import internet, service
from twisted.internet import interfaces, defer, reactor
from twisted.python import log
from twisted.words.xish import domish, xpath

from twisted.words.protocols.jabber.ijabber import IService
from twisted.words.protocols.jabber import component

from zope.interface import Interface, implements

from campfirer.xmpp import *
from campfirer.campfire import *

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
        self.host = self.config['xmpp.muc.host']
        self.smokey = SmokeyTheBear(self)
        # every x seconds, tell smokey to check on the fires

    def iq(self, type='get', id=None):
        r = xmlstream.IQ(self.xmlstream, type)
        r['from'] = self.host
        if id is not None:
            r['id'] = id
        return r
        

    def componentConnected(self, xmlstream):
        self.jabberId = xmlstream.authenticator.otherHost
        self.xmlstream = xmlstream
        self.xmlstream.addObserver(DISCO_INFO, self.onDiscoInfo)
        self.xmlstream.addObserver(PRESENCE, self.onPresence)
        log.msg("muc component connected")
        

    def onDiscoInfo(self, iq):
        response = self.iq('result', iq['id'])
        query = getattr(iq, 'query', None)
        if query is not None:
            query = response.addElement('query', DISCO_NS_INFO)
            identity = domish.Element((None, 'identity'), attribs={'category': "conference", 'name': 'campfirenow.com interface MUC', 'type': "text"})
            query.addChild(identity)
            query.addChild(domish.Element((None, 'feature'), attribs={'var': NS_MUC}))
            response.send(iq['from'])


    # <presence from='bmuller@butterfat.net/hm-min' to='testthree@muc.campfirer.com/bmuller'>
    #   <x xmlns='http://jabber.org/protocol/muc'><password>password</password></x></presence>
    def onPresence(self, pres):      
        to = jid.JID(pres['to'])
        room_parts = to.user.split(".")
        room = ".".join(room_parts[1:])
        account = room_parts[0]    

        def handleAuth(campfire):
            if campfire is None:
                self.sendErrorPresence(pres, "not-allowed", "cancel", NS_MUC)
            self.initializeRoom(campfire)

        password = xpath.queryForString("/presence/x/password", pres)
        if getattr(pres, 'type', "") == "unavailable":
            self.smokey.putCampfireOut(account, to.resource)
        elif password == "":
            self.sendErrorPresence(pres, "not-authorized")
        else:
            log.msg("attempting to auth %s for room %s on account %s" % (to.resource, room, account))
            self.smokey.getCampfire(account, to.resource, password).addCallback(handleAuth)


    def initializeRoom(self, campfire):            
        p = domish.Element((None, 'presence'))
        p['from'] = "%s@%s/coolguy" % (room, self.host)
        p['to'] = pres['from']
        x = p.addElement('x', NS_MUC_USER)
        x.addChild(domish.Element((None, 'item'), attribs = {'affiliation': 'member', 'role': 'participant'}))
        self.xmlstream.send(p)


    def sendErrorPresence(self, pres, reason, type="auth", ns=NS_MUC_USER):
        to = jid.JID(pres['to'])        
        p = domish.Element((None, 'presence'))
        p['from'] = to.userhost()
        p['to'] = pres['from']
        p.addElement('x', ns)
        p.addChild(Error(reason, type))
        self.xmlstream.send(p)        


    ##################    ##################    ##################    ##################    ##################
    def presence(self, sendto):
        p = domish.Element((None, 'presence'))
        p['to'] = sendto
        p['from'] = self.jid
        return p

    
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
