from aiohttp import web
import socketio
import json, ssl

ROOM = 'general'

sio = socketio.AsyncServer(
    cors_allowed_origins='*',  # Allow all origins
    ping_timeout=35
)
app = web.Application()
async def handler(request):
    return web.Response(text="Hello, HTTPS!")

app = web.Application()
app.router.add_get('/', handler)

# Paths to your SSL/TLS certificate and private key files
ssl_certfile = './fullchain.pem'
ssl_keyfile = './privkey.pem'

# Create SSL context
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(ssl_certfile, keyfile=ssl_keyfile)


sio.attach(app)

rooms = dict()

@sio.event
async def connect(sid, environ):
    print('Connected', sid)
    await sio.emit('ready', room=ROOM, to=sid)

@sio.event
async def disconnect(sid):
    await sio.leave_room(sid, ROOM)
    print('Disconnected', sid)

@sio.event
async def join(sid, data):
    try:
        if rooms.get(data):
            rooms[data].add(sid)
        else:
            rooms[data]=set()
            rooms[data].add(sid)

        await sio.enter_room(sid, data)
        await sio.emit('data', f'{sid} joined room', room=data, skip_sid=sid)

    except:
        pass
    print(sid, rooms)

@sio.event
async def data(sid, data):
    print(sid,rooms)
    try:
        data = json.loads(data)
    except:
        pass
    if sid in rooms.get(data.get("room")):
        print('Message from {}: {} room {}'.format(sid, data, data.get("room")))
        await sio.emit('data', data, room=data.get("room"), skip_sid=sid)


if __name__ == '__main__':
    web.run_app(app, port=9999, ssl_context=ssl_context)