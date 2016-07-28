VERSION = "0.0.2"

from django.utils.module_loading import import_string

from channels import Channel, channel_layers, route


def wamp_dispatch(message):
    func = import_string(message.content['func_path'])
    return func(*message.content['args'], **message.content['kwargs'])


def call(uri, *args, **kwargs):
    channel_layer = channel_layers["default"]
    options = kwargs.pop('options', {})
    reply_channel_name = channel_layer.new_channel('wamp.events?')
    Channel('wamp.call').send({
        'uri': uri,
        'args': args,
        'kwargs': kwargs,
        'options': options,
        'reply_channel': reply_channel_name,
    })


def publish(topic, *args, **kwargs):
    channel_layer = channel_layers["default"]
    options = kwargs.pop('options', {})
    reply_channel_name = channel_layer.new_channel('wamp.events?')
    Channel('wamp.publish').send({
        'topic': topic,
        'args': args,
        'kwargs': kwargs,
        'options': options,
        'reply_channel': reply_channel_name,
    })


def subscribe(topic, func, options=None):
    channel_layer = channel_layers["default"]
    reply_channel_name = channel_layer.new_channel('wamp.events?')

    Channel('wamp.subscribe').send({
        'func_path': '{}.{}'.format(func.__module__, func.__name__),
        'topic': topic,
        'options': options,
        'reply_channel': reply_channel_name,
    })
    subscription = None
    while subscription is None:
        channel, subscription = channel_layer.receive_many([reply_channel_name, 'wamp.disconnect'])
        if channel == 'wamp_disconnect':
            raise RuntimeError("Disconnected from router")
    return subscription


def register(uri, func, options=None):
    channel_layer = channel_layers["default"]
    reply_channel_name = channel_layer.new_channel('wamp.events?')

    Channel('wamp.register').send({
        'func_path': '{}.{}'.format(func.__module__, func.__name__),
        'uri': uri,
        'options': options,
        'reply_channel': reply_channel_name,
    })
    registration = None
    while registration is None:
        channel, registration = channel_layer.receive_many([reply_channel_name, 'wamp.disconnect'])
        if channel == 'wamp_disconnect':
            raise RuntimeError("Disconnected from router")
    return registration


def unsubscribe(subscription_id):
    Channel('wamp.unsubscribe').send({
        'subscription_id': subscription_id,
    })


def unregister(registration_id):
    Channel('wamp.unregister').send({
        'registration_id': registration_id,
    })


routing = [
    route("wamp.events", "wampclient.wamp_dispatch"),
]
