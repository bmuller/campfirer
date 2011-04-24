from twisted.words.xish.domish import Element

DISCO_NS        = 'http://jabber.org/protocol/disco'
DISCO_NS_INFO   = DISCO_NS + '#info'
DISCO_NS_ITEMS  = DISCO_NS + '#items'

IQ        = '/iq'
IQ_GET    = IQ+'[@type="get"]'

DISCO_INFO = IQ_GET + '/query[@xmlns="' + DISCO_NS_INFO + '"]'
DISCO_ITEMS = IQ_GET + '/query[@xmlns="' + DISCO_NS_ITEMS + '"]'

NS_MUC          = 'http://jabber.org/protocol/muc'
NS_MUC_USER     = NS_MUC + '#user'

MESSAGE   = '/message'
PRESENCE  = '/presence'


class Error(Element):
    TYPES = { 'not-authorized': "urn:ietf:params:xml:ns:xmpp-stanzas" }
    
    def __init__(self, error, type="auth"):
        Element.__init__(self, (None, 'error'), attribs = {'type': type})
        self.addElement(error, Error.TYPES[error])
