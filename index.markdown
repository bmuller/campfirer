---
layout: base
title: "Campfirer: A Jabber / Campfire Gateway"
---
# Campfirer: A Jabber / Campfire Gateway
Campfirer gives [campfire](http://campfirenow.com) users a way to connect to rooms using any [Jabber (XMPP)](http://xmpp.org) client.  It does this by implementing (a portion) of [the multi-user chat extension](http://xmpp.org/extensions/xep-0045.html).  Note that you must first have an account at [campfirenow.com](http://campfirenow.com) and have created a room there before you can use campfirer to connect.

There are two ways you can use the campfirer gateway:

1. You can use the gateway running at **campfirer.com** to connect to any campfire room.  See the instructions below.
1. You can run a Jabber server at your own domain and run campfirer as an [XMPP component](http://xmpp.org/extensions/xep-0114.html).  See the [component](component.html) page for directions.

The first option is the easiest to try things out - but there is no guarantee of service quality or uptime.

## Connecting to Campfirer.com
There are three pieces of information you'll need first:

1. Your account name.  This is the **name** portion of your login url of https://**name**.campfirenow.com
1. The name of the room you want to connect to
1. Your username / password that you use at https://name.campfirenow.com to log in

To connect, start your Jabber client and choose the option to join a new group chat.  

* Your nickname (or username) should be your username for campfirenow.com.  
* Your password is the password you use to log into campfirenow.com.
* The name of the room you should use is is your acount name followed by a "." followed by the name of the room.  For instance, if your account name is *mycompany* and your room name is *tech*, you should tell your Jabber client you want to connect to "mycompany.tech".
* The name of the server is *muc.campfirer.com*.

If your client merely asks for the room (without a separate box for the server name), use "mycompany.tech@muc.campfirer.com".  That's it.

