import argparse
import asyncio
import socketio
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
import os, sys

from tqdm import tqdm

# Socket.IO client
sio = socketio.AsyncClient()

pc = RTCPeerConnection()
code = ""
# For demonstration, we'll create a data channel for message exchange
data_channel = None

def read_file_chunks(filepath, chunk_size=1024):
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def get_file_info(file_path):
    # Get the file size in bytes
    file_size_bytes = os.path.getsize(file_path)
    
    # Convert file size to megabytes (MB)
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    # Get the filename with extension
    filename_with_ext = os.path.basename(file_path)
    
    return file_size_mb, filename_with_ext


@sio.event
async def connect():
    print('Connected to Signaling Server')
    await sio.emit('join', code)

@sio.event
async def data(data):
    # print(f"Message from signaling server: {data}")
    data= data["data"]
    if data["type"] == "offer":
        print("offer recieved")
        await pc.setRemoteDescription(RTCSessionDescription(data["sdp"], data["type"]))
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        await sio.emit('data', {"room":code,"data":{"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}})
    elif data["type"] == "answer":
        print("answer recieved")
        await pc.setRemoteDescription(RTCSessionDescription(data["sdp"], data["type"]))

async def run(role, signaling_server):
    await sio.connect(signaling_server)

    if role == "offer":
        global data_channel
        data_channel = pc.createDataChannel("file_transfer")

        @data_channel.on("open")
        def on_open():
            print("Data channel is open")
            file_path = input("Enter the path of the file to send: ")
            print(f"Sending file: {file_path}")
            file_size_mb, filename_with_ext = get_file_info(file_path)
            print(f"File size: {file_size_mb:.2f} MB")
            print(f"Filename with extension: {filename_with_ext}")

            data_channel.send(f"HEAD__{file_size_mb:.2f}__{filename_with_ext}")

            for chunk in read_file_chunks(file_path):
                    data_channel.send(chunk)
            
            data_channel.send(f"EOF__{file_size_mb:.2f}__{filename_with_ext}")

            print("File transfer complete")
            

        # Create an offer
        print("ofering...")
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        await sio.emit('data', {"room":code,"data":{"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}})

    @pc.on("datachannel")
    def on_datachannel(channel):
        received_chunks = []

        @channel.on("open")
        def on_open():
            print("Data channel is open")

        @channel.on("message")
        def on_message(message):

            # print("recieved msg ",f".{message}.", "EOF"==message[:3])

            if "EOF"==message[:3]:
                file_name = message.split("__")[-1]
                file_size = message.split("__")[-2]
                output_path = "./"+file_name
                print("eof recieved")
                with open(output_path, 'wb') as f:
                    for chunk in received_chunks:
                        f.write(chunk)
                print(f"File saved to {output_path}")
            elif "HEAD"==str(message[:4]):
                file_name = message.split("__")[-1]
                file_size = message.split("__")[-2]
                output_path = "./"+file_name
                print("file_name is : ", file_name)
            else:
                received_chunks.append(message)
                # print("Received chunk")

        @channel.on("close")
        def on_close():
            print("Data channel closed")
    
    if role=="answer":
        print("asnwering to ",code)
            

    await sio.wait()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P2P connection using aiortc with Socket.IO signaling")
    parser.add_argument("role", choices=["offer", "answer"], help="Role of this peer")
    parser.add_argument("code", help="Unique Code for file security")
    parser.add_argument("--signaling", help="Signaling server URL", default="https://sparteek65.online:9999")
    
    args = parser.parse_args()
    code = args.code
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(args.role, args.signaling))
