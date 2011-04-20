from twistar.dbobject import DBObject
from twistar.registry import Registry
from twistar.utils import joinWheres

class Room(DBObject):
    HASMANY = ['messages']

    @classmethod
    def createIfNonexistant(klass, jid, name):
        def _createIfNonexistant(result):
            if result is None:
                return Room(jid=jid, name=name).save()
            return result
        return Room.find(where=['jid = ?', jid], limit=1).addCallback(_createIfNonexistant)
        

class Message(DBObject):
    BELONGSTO = ['room']

    @classmethod
    def doSearch(klass, query, startdate, enddate, room_id):
        query = query.strip()
        where = ['room_id = ?', room_id]

        if query != "":
            where = joinWheres(where, ['message like ?', "%" + query + "%"])
        if startdate != "":
            where = joinWheres(where, ['created_at >= ?', startdate])
        if enddate != "":
            where = joinWheres(where, ['created_at <= ?', enddate])
            
        return klass.find(where=where, orderby="created_at ASC")

