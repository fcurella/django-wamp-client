django-wamp-client
==================

Installation
~~~~~~~~~~~~

::

    $ pip install django-wamp-client

Add ``channels`` and ``wampclient`` to your ``INSTALLED_APPS``::

    INSTALLED_APPS = [
        'channels',
        'wampclient',
    ]


In your settings, configure your connection to the WAMP Router::

    WAMP_CONNECTION = {
        'URL': "ws://127.0.0.1:9100/ws",
        'AUTHID': 'authid',
        'AUTHSECRET': 'secret',
        'REALM': "realname",
    }

Configure your routing to include ``wampclient.routing``::

    channel_routing = [
        route("wamp.join", "testproject.consumers.wamp_join"),
        include('wampclient.routing'),
    ]

Start the channel workers::

    $ ./manage.py runworker

Start the client that will connect to the WAMP Router::

    $ ./manage.py wamp_client

Usage
~~~~~

::

    from wampclient import publish, subscribe


    def wamp_hello(greeting):
        publish('com.example.hello', "'sup?")


    def wamp_join(message):
        # This consumer will be connected to the ``wamp.join`` channel
        subscribe('com.example.hello', wamp_hello)
        publish('com.example.hello', "Hi!", options={'exclude_me': False})

LICENSE
~~~~~~~

This software is released under the MIT License. See the ``LICENSE`` file.

Status
~~~~~~

This project should be considered a proof of concept.
