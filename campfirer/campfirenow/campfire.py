from twisted.internet import defer
from twisted.python import log

from campfirer.campfirenow.client import CampfireClient
from campfirer.campfirenow.room import CampfireRoom

from campfirer.DOMLight import createModel

class Campfire(CampfireClient):
    """
    A Campfire is a per-user per-account (x in x.campfirenow.com) connection
    """
    def __init__(self, account, muc):
        CampfireClient.__init__(self, account)
        self.rooms = {}
        self.username = None
        self.muc = muc
        # name of campfire user
        self.campfire_name = None


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
            room = CampfireRoom(self.account, self.token, name, room_id, self.muc, self.campfire_name)
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
            self.campfire_name = root.name[0].text[0]
            log.msg("Successfully authenticated %s with token %s" % (username, self.token))            
            return self

        self.username = username
        return self.getPage("users/me.xml", username, password).addCallbacks(_getToken, _getTokenFailure)



