# Campfirer: A Jabber / Campfire Gateway
Campfirer gives [campfire](http://campfirenow.com) users a way to connect to rooms using any [Jabber (XMPP)](http://xmpp.org) client.  It does this by implementing (a portion) of [the multi-user chat extension](http://xmpp.org/extensions/xep-0045.html).  Note that you must first have an account at [campfirenow.com](http://campfirenow.com) and have created a room there before you can use campfirer to connect.

There are two ways you can use the campfirer gateway:

1. You can use the gateway running at **campfirer.com** to connect to any campfire room.  See the instructions at [findingscience.com/campfirer](http://findingscience.com/campfirer) for more information.
1. You can run a Jabber server at your own domain and run campfirer as an [XMPP component](http://xmpp.org/extensions/xep-0114.html).  This process is described below.

The first option is the easiest to try things out - but there is no guarantee of service quality or uptime.

## Prerequisites
1. First, edit your jabber server config file to allow for a new component connection.  If you are using [ejabberd](http://www.ejabberd.im/), this can be done by adding the following lines to the services section of your *ejabberd.cfg* file.  Make sure to change the password to something actually secret, and then restart your jabber server.
<pre>
{listen, [
    ...
    {5554, ejabberd_service, [
                            {ip, {127, 0, 0, 1}},
                            {access, all},
                            {shaper_rule, fast},
                            {host, "muc.yourdomain.com", [{password, "secretpassword"}]}
                            ]},
    ...
  ]},
</pre>
2. Install [Twisted](http://twistedmatrix.com).
3. Make sure your jabber server is running and that you can connect to it.  
4. Edit your DNS to add a record for *muc.yourdomain.com* and make sure it resolves before continuing.

## Installation
First, get the source:

    git clone git://github.com/bmuller/campfirer.git

Then, within the campfirer directory:

    sudo python setup.py install

Copy config.py.dist to config.py and edit it for your configuration.  Minimally, you should set **xmpp.muc.host** and **xmpp.muc.password**.


You can then copy your config.py and the campfirer.tac file anywhere you'd like and can start the server with:

    twistd -noy campfirer.tac

See [findingscience.com/campfirer](http://findingscience.com/campfirer) for more information.

