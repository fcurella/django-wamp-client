from channels.routing import route, include


ws_routing = [
    route("wamp.join", "testproject.consumers.wamp_join"),
]

channel_routing = [
    # You can use a string import path as the first argument as well.
    include(ws_routing),
    include('wampclient.routing'),
]
