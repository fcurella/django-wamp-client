from django.core.management.base import BaseCommand

from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.logger import Logger

from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp import auth, types
from wampclient import conf
from channels import Channel, channel_layers


SLEEP_TIME = 1

# TODO:
# * session


class AppSession(ApplicationSession):

    log = Logger()

    channels = set([
        'wamp.call',
        'wamp.publish',
        'wamp.subscribe',
        'wamp.unsubscribe',
        'wamp.register',
        'wamp.unregister',
    ])
    reply_channels = {}
    subscriptions = {}
    registrations = {}

    def onConnect(self):
        """
        Implements :func:`autobahn.wamp.interfaces.ISession.onConnect`
        """
        if conf.WAMP_CONNECTION.get('AUTHID'):
            self.join(self.config.realm, authmethods=['wampcra'], authid=conf.WAMP_CONNECTION['AUTHID'])
        else:
            super(AppSession, self).onConnect()

    def onChallenge(self, challenge):
        if challenge.method == "wampcra":
            if 'salt' in challenge.extra:
                # salted secret
                key = auth.derive_key(
                    conf.WAMP_CONNECTION['AUTHSECRET'],
                    challenge.extra['salt'],
                    challenge.extra['iterations'],
                    challenge.extra['keylen'],
                )
            else:
                # plain, unsalted secret
                key = conf.WAMP_CONNECTION['AUTHSECRET']

            signature = auth.compute_wcs(key, challenge.extra['challenge'])
            self.log.info(key)

            return signature
        else:
            raise Exception("don't know how to handle authmethod {}".format(challenge.method))

    def forward_subscriber(self, func_path, topic, options=None):
        def wrapped(*args, **kwargs):
            payload = {
                'func_path': func_path,
                'topic': topic,
                'args': args,
                'kwargs': kwargs,
            }
            channel_name = 'wamp.events'
            Channel(channel_name).send(payload)
        self.log.info("registered subscriber for '{}'".format(topic))
        if options is None:
            options = types.SubscribeOptions()
        return self.subscribe(wrapped, topic, options=options)

    def forward_procedure(self, func_path, uri, options=None):
        @inlineCallbacks
        def wrapped(*args, **kwargs):
            reply_channel_name = self.channel_layer.new_channel('{}?'.format(uri))
            payload = {
                'func_path': func_path,
                'uri': uri,
                'args': args,
                'kwargs': kwargs,
                'reply_channel': reply_channel_name,
            }
            channel = Channel('wamp.events')
            channel.send(payload)

            d = Deferred()

            def cleanup(result):
                self.channels.remove(reply_channel_name)
                del self.reply_channels[reply_channel_name]
                self.log.info('result: {}'.format(result['total']))
            d.addCallback(cleanup)
            self.channels.add(reply_channel_name)
            self.reply_channels[reply_channel_name] = d

            yield d
        self.log.info("registered procedure for '{}'".format(uri))
        if options is None:
            options = types.RegisterOptions()
        return self.register(wrapped, uri, options=options)

    def forward_registration(self, reply_channel, registration):
        msg = {
            'id': registration.id,
            'procedure': registration.procedure,
            'active': registration.active,
            'session': registration.session._session_id,
        }
        Channel(reply_channel).send(msg)
        self.registrations[registration.id] = registration

    def forward_subscription(self, reply_channel, subscription):
        msg = {
            'id': subscription.id,
            'topic': subscription.topic,
            'active': subscription.active,
            'session': subscription.session._session_id,
        }
        Channel(reply_channel).send(msg)
        self.subscriptions[subscription.id] = subscription

    def warn(self, failure):
        self.log.warn(failure.value.error_message())

    @inlineCallbacks
    def onJoin(self, details):
        self.channel_layer = channel_layers["default"]

        Channel('wamp.join').send({'session': details.session})

        while self.is_connected():
            yield self.publish('com.example.bonjour', 2, options=types.PublishOptions(exclude_me=False))
            self.call('com.example.hello', 'hey!')

            channel_name, result = self.channel_layer.receive_many(self.channels)
            if channel_name is None:
                yield sleep(SLEEP_TIME)
                continue

            elif channel_name == 'wamp.call':
                uri = result['uri']
                args = result.get('args', [])
                kwargs = result.get('kwargs', {})
                options = result.get('options', {})
                if options:
                    kwargs['options'] = types.CallOptions(**options)
                registration = self.call(uri, *args, **kwargs)

            elif channel_name == 'wamp.publish':
                topic = result['topic']
                args = result.get('args', [])
                kwargs = result.get('kwargs', {})
                options = result.get('options', {})
                if options:
                    kwargs['options'] = types.PublishOptions(**options)
                self.publish(topic, *args, **kwargs)

            elif channel_name == 'wamp.subscribe':
                func_path = result['func_path']
                topic = result['topic']
                options = result.get('options', {}) or {}
                subscribe_options = types.SubscribeOptions(**options)
                subscription = yield self.forward_subscriber(func_path, topic, subscribe_options)
                self.forward_subscription(result['reply_channel'], subscription)

            elif channel_name == 'wamp.unsubscribe':
                subscription_id = result['subscription_id']
                subscription = self.subscriptions.pop(subscription_id)
                yield subscription.unsubscribe()

            elif channel_name == 'wamp.register':
                func_path = result['func_path']
                uri = result['uri']
                options = result.get('options', {}) or {}
                register_options = types.RegisterOptions(**options)
                registration = yield self.forward_procedure(func_path, uri, register_options)
                self.forward_registration(result['reply_channel'], registration)

            elif channel_name == 'wamp.unregister':
                registration_id = result['registration_id']
                registration = self.subscriptions.pop(registration_id)
                yield registration.unregister()

            elif channel_name in self.reply_channels:
                self.reply_channels[channel_name].callback(*result['args'], **result['kwargs'])

            yield sleep(SLEEP_TIME)

        self.log.info('disconnected!')
        Channel('wamp.disconnect').send({
            'reason': 'not connected',
        })
        self.disconnect()
        reactor.stop()


class Command(BaseCommand):

    def handle(self, *args, **options):
        runner = ApplicationRunner(
            conf.WAMP_CONNECTION['URL'],
            conf.WAMP_CONNECTION['REALM'],
        )
        runner.run(AppSession)
