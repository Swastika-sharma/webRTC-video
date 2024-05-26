import argparse
import asyncio
import json
import socketio
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack

# Socket.IO client
sio = socketio.AsyncClient()

pc = RTCPeerConnection()

# For demonstration, we'll create a data channel for message exchange
data_channel = None

@sio.event
async def connect():
    print('Connected to signaling server')
    await sio.emit('join', "class")

@sio.event
async def data(data):
    print(f"Message from signaling server: {data}")
    data= data["data"]
    if data["type"] == "offer":
        print("offer recieved")
        await pc.setRemoteDescription(RTCSessionDescription(data["sdp"], data["type"]))
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        await sio.emit('data', {"room":"class","data":{"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}})
    elif data["type"] == "answer":
        print("answer recieved")
        await pc.setRemoteDescription(RTCSessionDescription(data["sdp"], data["type"]))

async def run(role, signaling_server):
    await sio.connect(signaling_server)

    if role == "offer":
        global data_channel
        data_channel = pc.createDataChannel("chat")

        @data_channel.on("open")
        def on_open():
            print("Data channel is open")
            msg = input("enter msg : ")
            data_channel.send(msg)

        @data_channel.on("message")
        def on_message(message):
            print(f"Received message: {message}")
            msg = input("enter msg : ")
            data_channel.send(msg)

        # Create an offer
        print("ofering...")
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        await sio.emit('data', {"room":"class","data":{"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}})

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("open")
        def on_open():
            print("Data channel is open")

        @channel.on("message")
        def on_message(message):
            print(f"Received message: {message}")
            msg = input("enter msg : ")
            channel.send(msg)

    await sio.wait()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P2P connection using aiortc with Socket.IO signaling")
    parser.add_argument("role", choices=["offer", "answer"], help="Role of this peer")
    parser.add_argument("--signaling", help="Signaling server URL", default="https://sparteek65.online:9999")
    parser.add_argument("--filepath", help="Path to the file to send (only for offer)")
    parser.add_argument("--output", help="Path to save the received file (only for answer)")
    
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(args.role, args.signaling))
