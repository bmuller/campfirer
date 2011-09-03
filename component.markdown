---
layout: base
title: "Campfire: A Jabber / Campfire Gateway"
---
# Campfirer Component
First, set up your jabber server to accept a new component.  For instance, for [ejabberd](http://www.ejabberd.im/) edit your **/etc/ejabberd/ejabberd.cfg** file like so:

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
                            {host, "muc.yourdomain.com", [{password, "secretpassword"}]}
                            ]},
%% ...
{% endhighlight %}

Make sure to set a more secret password, change the domain to your jabber server's domain, and restart your server.  The muc domain name should be set up in your DNS records to be a **CNAME** for yourdomain.com and should resolve before continuing.

Next, install the [twisted framework](http://twistedmatrix.com).  Twisted allows campfirer to handle many connections at once in an asynchronous manner.

Then, checkout campfirer:

{% highlight bash %}
git clone git://github.com/bmuller/campfirer.git
cd campfirer
cp config.py.dist config.py
{% endhighlight %}

Then, edit the **config.py** file:
{% highlight python %}
CONFIG = {
    'xmpp.host': 'localhost',
    'xmpp.port': 5554,
    'xmpp.muc.password': 'secretpassword',
    'xmpp.muc.host': 'muc.yourdomain.com',
    'campfire.update.interval': 5,
    #'campfirer.logdir': './logs' # set this if you want to retain your logs
    }
{% endhighlight %}

You can now start the twisted server to make sure the component can connect:
{% highlight bash %}
twistd -noy campfirer.tac
{% endhighlight %}

This will run campfirer in the foreground.  If you're able to connect successfully, then you can use the following to run in the background:
{% highlight bash %}
twistd -oy campfirer.tac
{% endhighlight %}

That's it.  Report issues [on github](http://github.com/bmuller/campfirer/issues).