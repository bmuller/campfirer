from twisted.internet import defer
from twisted.python import log

from campfirer.campfirenow.client import CampfireClient
from campfirer.campfirenow.lists import ParticipantList, MessageList
from campfirer.campfirenow.message import Message

from campfirer.DOMLight import createModel, XMLMaker

class CampfireRoom(CampfireClient):
    def __init__(self, account, token, roomname, room_id, muc, campfire_name):
        CampfireClient.__init__(self, account)
        self.roomname = roomname
        self.room_id = room_id
        self.token = token
        self.participants = ParticipantList()
        self.topic = ""
        self.msgs = MessageList()
        self.muc = muc
        # name of campfire user
        self.campfire_name = campfire_name
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
        return self.postPage("room/%s/speak.xml" % self.room_id, data=str(xmlmsg))
        

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
