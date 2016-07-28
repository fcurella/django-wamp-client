import logging
import time

from wampclient import call, publish, subscribe, register


logger = logging.getLogger(__name__)


def wamp_join(message):
    subscribe('com.example.bonjour', wamp_bonjour)
    register('com.example.hello', wamp_hello)


def wamp_unsubscribe(message):
    print(message.content)


def wamp_bonjour(message):
    print('bonjour')
    print(message)


def wamp_hello(message):
    print('hello')
    print(message)
    return "'sup?"


def wamp_add(message):
    print(message.content)
    total = sum(message.content['args'])
    time.sleep(5)
    print(total)
    message.reply_channel.send({'total': total})
