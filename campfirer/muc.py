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
        # every campfire.update.interval seconds, tell smokey to check on the fires
        self.smokey.startFireDuty(self.config['campfire.update.interval'])


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
        self.xmlstream.addObserver(MESSAGE, self.onMessage)
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


    def parseCampfireName(self, jid):
        room_parts = jid.user.split(".")
        roomname = ".".join(room_parts[1:])
        account = room_parts[0]    
        return (account, roomname)
        

    # <presence from='bmuller@butterfat.net/hm-min' to='testthree@muc.campfirer.com/bmuller'>
    #   <x xmlns='http://jabber.org/protocol/muc'><password>password</password></x></presence>
    def onPresence(self, pres):
        to = jid.JID(pres['to'])
        account, roomname = self.parseCampfireName(to)

        def handleAuth(campfire):
            if campfire is None:
                self.sendErrorPresence(pres, "not-allowed", "cancel", NS_MUC)
            else:
                self.initializeRoom(campfire, roomname, to, jid.JID(pres['from']))

        password = xpath.queryForString("/presence/x/password", pres)
        if pres.getAttribute('type') == "unavailable":
            self.smokey.putCampfireOut(account, to.resource)
        elif password == "":
            self.sendErrorPresence(pres, "not-authorized")
        else:
            log.msg("attempting to auth %s for room %s on account %s" % (to.resource, roomname, account))
            self.smokey.getCampfire(account, to, password).addCallback(handleAuth)

    
    def initializeRoom(self, campfire, roomname, participant_jid, source_jid):
        log.msg("initializing room %s" % roomname)
        def initParticipants(room):
            if room is None:
                return
            room.setJIDs(source_jid, participant_jid)
            return room.update()
        campfire.getRoom(roomname).addCallback(initParticipants)


    def handleRoomUpdate(self, room):
        for username in room.participants.getJustJoined().values():
            mfrom = room.participant_jid.userhostJID()  
            mfrom.resource = username.replace(" ", "")
            self.sendPresence(mfrom, room.source_jid)
                
        for msg in room.msgs:
            mfrom = room.participant_jid.userhostJID()
            mfrom.resource = msg.user.replace(" ", "") 
            self.sendMessage(mfrom, msg.body, room.source_jid, msg.tstamp)


    def sendPresence(self, pfrom, pto):
        log.msg("sending presence from %s to %s" % (pfrom, pto))
        p = domish.Element((None, 'presence'), attribs = {'from': pfrom.full(), 'to': pto.full()})
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


    def sendMessage(self, mfrom, msgBody, mto, tstamp):
        log.msg("sending message from %s to %s" % (mfrom, mto))
        m = domish.Element((None, 'message'), attribs = {'from': mfrom.full(), 'to': mto.full(), 'type': 'groupchat'})
        m.addElement('body', content=msgBody)
        delay = domish.Element((DELAY_NS, 'delay'), attribs = {'from': mfrom.userhost(), 'stamp': tstamp})
        m.addChild(delay)
        self.xmlstream.send(m)


    def onMessage(self, msg):
        to = jid.JID(msg['to'])
        account, roomname = self.parseCampfireName(to)
        def sendMsgRoom(room):
            if room is not None:
                room.say(xpath.queryForString("/message/body", msg))
        def sendMsg(campfire):
            if campfire is not None:
                campfire.getRoom(roomname).addCallback(sendMsgRoom)
        self.smokey.getCampfire(account, to).addCallback(sendMsg)
