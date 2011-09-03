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
