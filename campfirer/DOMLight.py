"""
DOMLight is a little library for making DOM's more accessable in python.
Copyright (C) 2011 Brian Muller <bamuller@gmail.com>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

## DOMLight is a little library for making DOM's more accessable in python. 
##
## For instance, say you've got the following XML:
## <cheese with="spam">
##  <block type="jack">
##    A huge bunch of jack.
##  </block>
##  <block type="cheddar">
##    I like cheddar.
##    <color>yellow</color>
##    It is tastey.
##  </block>
##  <additional stuff="eggs" />
## </cheese>
##
## Python code to access the objects:
##
## import DOMLight
## root = DOMLight.createModel(xml_string)
## print root["with"]           # this accesses the attribute "with" in the root node
## print root["doesnt_exist"]   # this attempts to access a non-existant attribute, returns ""
## block = root.block[0]        # block now holds root's first child named block
## print block["type"]          # -> "jack"
## print block.text[0]          # Text children are named "text" - this prints the first text child
## block = root.block[1]        # block now holds root's second child named block
## print block.color[0].text[0] # -> "yellow"
## print block.text[0]          # -> "I like cheddar."
## print block.text[1]          # -> "It is tastey."
## a = root.additional          # "a" is now an list with one element
## print a[0]["stuff"]          # -> "eggs"
##
## node.children is a hash.  The keys are children names, and the values
## are lists of children with that name.
##
## for nodename, nodelist in root.children.items():
##    print "There are %d children named %s" % (len(nodelist), nodename)
##    for node in nodelist:
##       # if it's a text node, just print the text
##       if type(node).__name__ == 'unicode':
##           print "text value is: \"%s\"" % str(node)
##       else:
##           # node.attrs is a hash.  The keys are attribute names,
##           # and the values are the attribute values.
##           for attr_name,attr_value in node.attrs.items():
##               print "%s = %s" % (attr_name, attr_value)

from xml.dom.minidom import *
import cgi
import re

def createModel(xml_string):
    def makeObject(elem):
        doml = DOMLightObject(elem.nodeName)
        if elem.attributes:
            for k,v in elem.attributes.items():
                doml[k] = v
        for child in elem.childNodes:
            if child.nodeType == 3 and child.nodeValue.rstrip() != "":
                doml.setAttr('text', child.nodeValue)
            elif child.nodeType == 8:
                doml.setAttr('comment', child.nodeValue)
            elif child.nodeType != 3:
                doml.setAttr(child.nodeName, makeObject(child))
        return doml
    doc = parseString(xml_string)
    for kid in doc.childNodes:
        if kid.nodeType == 1:
            return makeObject(kid)
    return None

class DOMLightObject:
    def __init__(self, name):
        self.children = {}
        self.attrs = {}
        self._name = name

    def __getitem__(self, name):
        if self.attrs.has_key(name):
            return self.attrs[name]
        return ""

    def __setitem__(self, name, value):
        self.attrs[name] = value

    def setAttr(self, name, kid):
        if not self.children.has_key(name):
            self.children[name] = []
        self.children[name].append(kid)
        
    def __getattr__(self, name):
        if self.children.has_key(name):
            return self.children[name]
        return []

    def __str__(self):
        return "<DOMLightObject %s>" % self._name


## This class is used to generate xml.  It is used like:
# xml = XMLMaker()
# print xml.a({'href': 'http://google.com'}, xml.img({'src': 'http://www.google.com/intl/en/images/logo.gif'}), "Click the image")
# <a href="http://google.com"><img src="http://www.google.com/intl/en/images/logo.gif"/>Click the image</a>
class XMLMaker:
    ## Inner class representing an XML element.
    class Elem:
        def __init__(self,name):
            self.name = name
        def set(self,attr={},*args):
            self.attr = attr
            self.kids = args
            return self
        def cleanAttrs(self):
            if len(self.attr)==0: return ""
            return ' '+" ".join(["%s=\"%s\"" % (k,v) for (k,v) in self.attr.items()])
        def __str__(self):
            if len(self.kids)==0: return "<%s%s/>" % (self.name,self.cleanAttrs())
            result = ""
            kids = ""
            try:
                kids = "".join([str(kid) for kid in self.kids])
                strmap = lambda *a: map(lambda x: str(x), a)
                (self.name,cleanedAttrs,kids,self.name) = strmap(self.name,self.cleanAttrs(),kids,self.name)
                result = "<%s%s>%s</%s>" % (self.name,cleanedAttrs,kids,self.name)
            except Exception, e:
                print "Error: %s\nkids: %s" % (str(e),kids)
            return result
    ## Constructor.
    # @param namespace The xmlns to use
    def __init__(self, namespace=None):
        self.namespace = namespace
    ## Manually create a function
    def makeFunc(self,name):
        return self.__getattr__(name)
    ## Make a new elemented
    # @param name Name of the elem to make
    def __getattr__(self,name):
        if self.namespace!=None: elem = XMLMaker.Elem(self.namespace+':'+name)
        else: elem = XMLMaker.Elem(name)
        return elem.set


## This function first html escapes a string, and then converts
# entities to html entities to xml entities as much as possible.
# \return An XML entity escaped string
def XMLEscape(string):
    s = cgi.escape(string, True)
    return htmlToXmlEntities(s)

## XML only allows 5 entities (&lt; &gt; &quot; &amp; &apos;) and
# html tidy does not do any conversion when creating xml from html,
# so this must be done manually.  This function will convert Unicode
# entities to html entities to xml entities as much as possible.
# (for example, "&#169;" becomes "&amp;copy;"
# @param s The string containing HTML entities
# \return A string only containing XML entities
def htmlToXmlEntities(s):                           
    def convertentity(m):
        if m.group(1)=='#':
            try:
                return "&amp;%s;" % htmlentitydefs.codepoint2name[int(m.group(2))]
            except KeyError:
                return "" # Must keep runing - even if we loose a uni char
        elif m.group(2) in ['lt', 'gt', 'quot', 'amp', 'apos']:
            return '&%s;' % m.group(2)
        else:
            return '&amp;%s;' % m.group(2)
    return re.sub(r'&(#?)(.+?);', convertentity, s)


