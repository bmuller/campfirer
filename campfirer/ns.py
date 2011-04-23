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
