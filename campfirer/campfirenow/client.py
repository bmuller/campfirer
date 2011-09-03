from twisted.web import client
from twisted.python import log

import base64

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
