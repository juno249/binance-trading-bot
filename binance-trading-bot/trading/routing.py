from channels.routing import route
from trading.consumers import ws_add, ws_message, ws_disconnect, ws_prices


channel_routing = [
    route("websocket.connect", ws_add),
    route("websocket.receive", ws_message),
    route("websocket.disconnect", ws_disconnect),
    route("prices", ws_prices)
]