import base64

from twisted.internet.ssl import ClientContextFactory
from twisted.python import log
from twisted.web import client

from campfirer.DOMLight import createModel

class WebClientContextFactory(ClientContextFactory):
    def getContext(self):
        return ClientContextFactory.getContext(self)


class Message:
    def __init__(self, user, body, msgtype):
        self.user = user
        self.body = body
        self.msgtype = msgtype
        

class MessageList:
    def __init__(self, maxsize=100):
        self.maxsize = maxsize
        self.msgs = []

    def append(self, msgs):
        self.msgs = (self.msgs + msgs)[-self.maxsize:]

    def __iter__(self):
        return self.msgs.__iter__()
                
        

class CampfireClient:
    def __init__(self, account):
        self.account = account
        self.contextFactory = WebClientContextFactory()
        self.token = None

    
    def getPage(self, url, username=None, password=None):
        log.msg("fetching %s" % url)
        if username is None:
            username = self.token
        if password is None:
            password = "X"
        auth = "%s:%s" % (username, password)
        headers = {'Authorization': base64.b64encode(auth) }            
        url = str("https://%s.campfirenow.com/%s" % (self.account, url))
        return client.getPage(url, self.contextFactory, headers=headers)    


class CampfireRoom(CampfireClient):
    def __init__(self, account, token, roomname, room_id):
        CampfireClient.__init__(self, account)
        self.roomname = roomname
        self.room_id = room_id
        self.token = token
        self.participants = {}
        self.topic = ""
        self.msgs = MessageList()


    def _updateRoom(self, response):
        root = createModel(response)
        self.participants = {}
        for xmluser in root.users[0].user:
            uid = xmluser.id[0].text[0]
            self.participants[uid] = xmluser.name[0].text[0]
        self.topic = root.topic[0].text[0]
        return self.getPage("room/%s/recent.xml" % self.room_id).addCallback(self._updateMsgs)


    def _updateMsgs(self, response):
        root = createModel(response)
        msgs = []
        print response
        for xmlmsg in root.message:
            msgtype = xmlmsg.type[0].text[0]
            if msgtype in ["TextMessage", "PasteMessage"]:
                user = self.participants.get(xmlmsg.children['user-id'][0].text[0], xmlmsg.children['user-id'][0].text[0])
                body = xmlmsg.body[0].text[0]                
                msgs.append(Message(user, body, msgtype))
        self.msgs.append(msgs)
        

    def update(self):
        def _updateFinished():
            args = (self.roomname, self.account, len(self.participants), len(self.msgs))
            log.msg("%s.%s updated with %i participants and %i messages" % args)
            return self
        return self.getPage("room/%s.xml" % self.room_id).addCallback(self._updateRoom).addCallback(_updateFinished)


class Campfire(CampfireClient):
    """
    A Campfire is a per-user per-account (x in x.campfirenow.com) connection
    """
    def __init__(self, account):
        CampfireClient.__init__(self, account)
        self.rooms = {}

    
    def getRoom(self, name):
        if self.rooms.has_key(name):
            return defer.succeed(self.rooms[name])
        
        def _saveHandle(room):
            self.rooms[name] = room
            return room
        
        def _getRoomID(response):
            root = createModel(response)
            room_id = None
            for xmlroom in root.room:
                if str(xmlroom.name[0].text[0]) == name:
                    room_id = str(xmlroom.id[0].text[0])
            if room_id is None:
                return None
            return CampfireRoom(self.account, self.token, name, room_id).update().addCallback(_saveHandle)
        return self.getPage("rooms.xml").addCallback(_getRoomID)


    def initialize(self, username, password):
        def _getTokenFailure(result):
            self.token = None
            return None
            
        def _getToken(response):
            root = createModel(response)
            self.token = root.children["api-auth-token"][0].text[0]
            return self
        
        return self.getPage("users/me.xml", username, password).addCallback(_getToken, _getTokenFailure)


class SmokeyTheBear:
    def __init__(self, muc):
        self.fires = {}
        self.muc = muc

    def key(self, account, user):
        return "%s@%s" % (user, account)        

    def getCampfire(self, account, user, password):
        key = self.key(account, user)
        if self.fires.has_key(key):
            return self.succeed(self.fires[key])
        def save(result):
            if result is not None:
                self.fires[key] = result
            return result
        return Campfire(account).initialize(user, password).addCallback(save)

    def putCampfireOut(account, user):
        key = self.key(account, user)
        if self.fires.has_key(key):
            del self.fires[key]
            
