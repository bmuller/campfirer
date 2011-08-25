---
layout: base
title: "Campfire: A Jabber / Campfire Gateway"
---
# Campfire: A Jabber / Campfire Gateway
Campfirer gives [campfire](http://campfirenow.com) users a way to connect to rooms using any [Jabber (XMPP)](http://xmpp.org) client.  It does this by implementing (a portion) of [the multi-user chat extension](http://xmpp.org/extensions/xep-0045.html).  Note that you must first have an account at [campfirenow.com](http://campfirenow.com) and have created a room there before you can use campfirer to connect.

There are two ways you can use the campfirer gateway:

1. You can use the gateway running at **campfirer.com** to connect to any campfire room.
1. You can run a Jabber server at your own domain and run campfirer as a [component](http://xmpp.org/extensions/xep-0114.html).

The first option is the easiest to try things out - but there is no guarantee of service quality or uptime.

## 1. Connecting to Campfirer.com
There are three pieces of information you'll need first:

1. Your account name.  This is the **name** portion of your login url of https://**name**.campfirenow.com
1. The name of the room you want to connect to
1. Your username / password that you use at https://name.campfirenow.com to log in

To connect, start your Jabber client and choose the option to join a new group chat.  

* Your nickname (or username) should be your username for campfirenow.com.  
* Your password is the password you use to log into campfirenow.com.
* The name of the room you should use is is your acount name followed by a "." followed by the name of the room.  For instance, if your account name is *mycompany* and your room name is *tech*, you should tell your Jabber client you want to connect to "mycompany.tech".
* The name of the server is *muc.campfirer.com*.

If your client merely asks for the room (without a separate server entry box), use "mycompany.tech@muc.campfirer.com".

## 2. Running Campfirer Yourself

{% highlight erlang %}
%%%   ===============
%%%   LISTENING PORTS

%%
%% listen: Which ports will ejabberd listen, which service handles it
%% and what options to start it with.
%%
{listen,
 [

%% ...

  {5554, ejabberd_service, [
                            {ip, {127, 0, 0, 1}},
                            {access, all},
                            {shaper_rule, fast},
                            {host, "muc.campfirer.com", [{password, "secretpassword"}]}
                            ]},
%% ...
{% endhighlight %}

{% highlight bash %}
git://github.com/bmuller/campfirer.git
{% endhighlight %}