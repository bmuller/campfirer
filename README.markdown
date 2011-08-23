# Campfirer
Campfirer is a Jabber (XMPP) MUC component that provides a gateway to [Campfire](http://campfirenow.com).

# Usage

## Prerequisites
1. First, edit your jabber server config file to allow for a new component connection.  If you are using [ejabberd](http://www.ejabberd.im/), this can be done by adding the following lines to the services section of your *ejabberd.cfg* file.  Make sure to change the password to something actually secret, and then restart your jabber server.

    {5524, ejabberd_service, [ 
        {ip, {127, 0, 0, 1}}, 
        {access, all}, 
        {shaper_rule, fast}, 
        {host, "campfirer.localhost", [{password, "secret"}]} 
    ]},

2. Install [Twisted](http://twistedmatrix.com).


## Installation
First, get the source:

    git clone git://github.com/bmuller/campfirer.git

Then, within the campfirer directory:

    sudo python setup.py install

Copy config.py.dist to config.py and edit it for your configuration.  You can then copy your config.py and the campfirer.tac file anywhere you'd like and can start the server with:

    twistd -noy campfirer.tac

See the twistd man page for more information.