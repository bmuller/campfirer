import base64

from twisted.internet import defer, reactor
from twisted.python import log
from twisted.web import client

from campfirer.DOMLight import createModel, XMLMaker


class Message:
    def __init__(self, id, user, body, msgtype, tstamp):
        self.id = id
        self.user = user
        self.body = body
        self.msgtype = msgtype
        self.tstamp = tstamp


class ParticipantList:
    def __init__(self):
        self.participants = {}
        self.recent = {}

    def add(self, id, name):
        self.participants[id] = name

    def update(self, newpeople):
        self.recent = {}
        for uid, name in newpeople.items():
            if not self.participants.has_key(uid):
                self.recent[uid] = name
                self.participants[uid] = name

    def getName(self, id):
        return self.participants.get(id, id)

    def getJustJoined(self):
        return self.recent

    def __len__(self):
        return len(self.participants)
        

class MessageList:
    def __init__(self, maxsize=100):
        self.maxsize = maxsize
        self.msgs = []
        self.last_msg_id = None
        self.ignore = set()


    def addIgnore(self, id):
        self.ignore.add(id)


    def append(self, msgs):
        self.msgs = (self.msgs + msgs)[-self.maxsize:]


    def reset(self, msgs):
        self.msgs = []
        for msg in msgs:
            if msg.id in self.ignore:
                self.ignore.discard(msg.id)
            else:
                self.msgs.append(msg)


    def __iter__(self):
        return self.msgs.__iter__()


    def __len__(self):
        return len(self.msgs)
        

class CampfireClient:
    def __init__(self, account):
        self.account = account
        self.token = None


    def url(self, path):
        return str("https://%s.campfirenow.com/%s" % (self.account, path))
    
    
    def getPage(self, url, username=None, password=None):
        log.msg("GET %s" % url)
        if username is None:
            username = self.token
        if password is None:
            password = "X"
        auth = "%s:%s" % (username, password)
        headers = {'Authorization': base64.b64encode(auth) }            
        return client.getPage(self.url(url), headers=headers)    


    def postPage(self, url, data=None):
        log.msg("POST %s" % url)
        auth = "%s:X" % self.token
        headers = {'Authorization': base64.b64encode(auth) }
        if data is not None:
            headers['Content-Type'] = 'application/xml'
        return client.getPage(self.url(url), method='POST', headers=headers, postdata=data)    
    

class CampfireRoom(CampfireClient):
    def __init__(self, account, token, roomname, room_id, muc):
        CampfireClient.__init__(self, account)
        self.roomname = roomname
        self.room_id = room_id
        self.token = token
        self.participants = ParticipantList()
        self.topic = ""
        self.msgs = MessageList()
        self.muc = muc
        # the jid of the user who has connected
        self.source_jid = None
        # the jid of the use in the room
        self.participant_jid = None


    def setJIDs(self, source_jid, participant_jid):
        self.source_jid = source_jid
        self.participant_jid = participant_jid


    def _updateRoom(self, response):
        root = createModel(response)

        # update list of participants
        participants = {}
        for xmluser in root.users[0].user:
            uid = xmluser.id[0].text[0]
            name = xmluser.name[0].text[0]
            participants[uid] = name
        self.participants.update(participants)
        
        self.topic = root.topic[0].text[0]
        if self.msgs.last_msg_id is not None:
            url = "room/%s/recent.xml?since_message_id=%s" % (self.room_id, self.msgs.last_msg_id)
        else:
            url = "room/%s/recent.xml" % self.room_id
        return self.getPage(url).addCallback(self._updateMsgs)


    def _updateMsgs(self, response):
        root = createModel(response)
        msgs = []
        for xmlmsg in root.message:
            msgtype = xmlmsg.type[0].text[0]
            if msgtype in ["TextMessage", "PasteMessage"]:
                user = self.participants.getName(xmlmsg.children['user-id'][0].text[0])
                body = xmlmsg.body[0].text[0]
                id = xmlmsg.id[0].text[0]
                tstamp = xmlmsg.children["created-at"][0].text[0]
                msgs.append(Message(id, user, body, msgtype, tstamp))
            self.msgs.last_msg_id = xmlmsg.children['id'][0].text[0]
        self.msgs.reset(msgs)
        return self


    def say(self, msg):
        xml = XMLMaker()
        xmlmsg = xml.message({}, xml.body({}, msg))
        # ignore this message next time we poll campfirenow.com
        def addIgnore(result):
            root = createModel(result)
            self.msgs.addIgnore(root.id[0].text[0])
        return self.postPage("room/%s/speak.xml" % self.room_id, data=str(xmlmsg)).addCallback(addIgnore)
        

    def join(self):
        return self.postPage("room/%s/join.xml" % self.room_id).addCallback(lambda _: self)


    def leave(self):
        return self.postPage("room/%s/leave.xml" % self.room_id).addCallback(lambda _: self)
        

    def update(self):
        # if we haven't finished setting up MUC side - don't do anything yet
        if self.participant_jid == None:
            return defer.succeed(self)
        def _updateFinished(self):
            args = (self.roomname, self.account, len(self.participants), len(self.msgs))
            log.msg("%s.%s updated with %i participants and %i messages" % args)
            self.muc.handleRoomUpdate(self)
            return defer.succeed(self)
        return self.getPage("room/%s.xml" % self.room_id).addCallback(self._updateRoom).addCallback(_updateFinished)


class Campfire(CampfireClient):
    """
    A Campfire is a per-user per-account (x in x.campfirenow.com) connection
    """
    def __init__(self, account, muc):
        CampfireClient.__init__(self, account)
        self.rooms = {}
        self.username = None
        self.muc = muc


    def updateRooms(self):
        log.msg("All rooms in %s being updated" % self.account)
        for room in self.rooms.values():
            room.update()

    
    def getRoom(self, name):
        if self.rooms.has_key(name):
            return defer.succeed(self.rooms[name])
        
        def _saveHandle(room):
            log.msg("saving room %s" % name)
            self.rooms[name] = room
            return room
        
        def _getRoomID(response):
            root = createModel(response)
            room_id = None
            for xmlroom in root.room:
                if str(xmlroom.name[0].text[0]).lower() == name.lower():
                    room_id = str(xmlroom.id[0].text[0])
                    log.msg("found room %s for account %s with id %s" % (xmlroom.name[0].text[0], self.account, room_id))                    
                    break
            if room_id is None:
                return None
            room = CampfireRoom(self.account, self.token, name, room_id, self.muc)
            return room.join().addCallback(lambda s: s.update()).addCallback(_saveHandle)
        return self.getPage("rooms.xml").addCallback(_getRoomID)


    def leaveRooms(self):
        ds = [room.leave() for room in self.rooms.values()]
        log.msg("%s@%s leaving all %i rooms" % (self.username, self.account, len(self.rooms)))
        return defer.DeferredList(ds)


    def initialize(self, username, password):
        def _getTokenFailure(result):
            log.err("Authentication for %s failed" % username)
            self.token = None
            return None
            
        def _getToken(response):
            root = createModel(response)
            self.token = root.children["api-auth-token"][0].text[0]
            log.msg("Successfully authenticated %s with token %s" % (username, self.token))            
            return self

        self.username = username
        return self.getPage("users/me.xml", username, password).addCallbacks(_getToken, _getTokenFailure)


class SmokeyTheBear:
    def __init__(self, muc):
        self.fires = {}
        self.muc = muc


    def checkFires(self):
        log.msg("Smokey is checking all fires")
        for fire in self.fires.values():
            fire.updateRooms()


    def key(self, account, user):
        return "%s@%s" % (user, account)        


    def getCampfire(self, account, jid, password=None):
        key = self.key(account, jid.userhost())
        if self.fires.has_key(key):
            return defer.succeed(self.fires[key])
        def save(result):
            if result is not None:
                self.fires[key] = result
            return result
        return Campfire(account, self.muc).initialize(jid.resource, password).addCallback(save)


    def putCampfireOut(self, account, user):
        log.msg("Putting campfire %s @ %s out" % (user, account))
        key = self.key(account, user)
        def deleteFire(result):
            del self.fires[key]            
        if self.fires.has_key(key):
            self.fires[key].leaveRooms().addCallback(deleteFire)
            
            
    def startFireDuty(self, seconds):
        self.checkFires()
        reactor.callLater(seconds, self.startFireDuty, seconds)

