from twisted.internet import reactor, defer
from twisted.python import log

from campfirer.campfirenow.campfire import Campfire

class SmokeyTheBear:
    def __init__(self, muc):
        self.fires = {}
        self.muc = muc


    def checkFires(self):
        if len(self.fires) > 0:
            log.msg("Smokey is checking all fires")
        for fire in self.fires.values():
            fire.updateRooms()


    def key(self, account, user):
        return "%s@%s" % (user.full(), account)        


    def initCampfire(self, account, fromjid, tojid, password):
        key = self.key(account, fromjid)
        def save(result):
            if result is not None and result.token is not None:
                self.fires[key] = result
            return result
        return Campfire(account, self.muc).initialize(tojid.resource, password).addCallback(save)


    def getCampfire(self, account, fromjid):
        key = self.key(account, fromjid)
        log.msg("looking for key %s" % key)
        if self.fires.has_key(key):
            log.msg("found it")
            return defer.succeed(self.fires[key])
        log.msg("didn't find it")
        return defer.succeed(None)
        

    def putCampfireOut(self, account, jid):
        def deleteFire(_, key):
            del self.fires[key]
        
        campfire_name = jid.resource
        for key, fire in self.fires.items():
            fires_campfire_name = fire.campfire_name.replace(" ", "")
            if fires_campfire_name == campfire_name and account == fire.account:
                log.msg("Putting campfire %s @ %s out" % (jid.resource, account))
                fire.leaveRooms().addCallback(deleteFire, key)
                
            
    def startFireDuty(self, seconds):
        self.checkFires()
        reactor.callLater(seconds, self.startFireDuty, seconds)
