from textual.app import App, ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.widgets import Header, Footer, Input, Button, Static
from textual.reactive import reactive
from textual.screen import Screen
from textual import work, log
from textual.worker import Worker, get_current_worker

from textual.containers import Grid
from textual.widgets import Button, Footer, Header, Label
import argparse
import asyncio
import json
import socketio
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
import asyncio

sio = socketio.AsyncClient()

class QuitScreen(Screen):
    """Screen with a dialog to quit."""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to quit?", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()


class ChatScreen(Screen):
    """Screen with a dialog to quit."""

    def __init__(self, name: str  = None, id: str  = None, classes: str  = None) -> None:
        super().__init__(name, id, classes)
        self.text = ""
        self.textContainer = ScrollableContainer(
            )

    def compose(self) -> ComposeResult:
        self.msg_inp = Input(placeholder="type message ...", id="message_text")
        self.container = Container(
            Label(f"You are in to room : {self.app.roomname}", id="chat-header"),
            self.textContainer,
            self.msg_inp,
            id="chat_message")
        
        yield self.container
        
    async def on_input_submitted(self, event):
        if event.input.id == "message_text":
            message = event.value
            self.textContainer.mount(Label(f"{self.app.username} {message}"))
            await sio.emit("data", {"room":"class","data":{"msg":message,"username":self.app.username}})
            self.msg_inp.clear()

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "message_text":
            self.text = event.value
   
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send_button":
            self.textContainer.mount(Label(self.text))
        if event.button.id == "connect_button":
            self.textContainer.mount(Label("initialting socket"))
            await self.on_load_()
    
    def on_message(self, message) -> None:
        self.textContainer.mount(Label(str(message)))
    
    def on_open(self, message) -> None:
        self.textContainer.mount(Label(str(message)))
    
    async def on_mount(self, event):
        await sio.connect("https://sparteek65.online:9999")
        await sio.emit("join", self.app.roomname)
        sio.on("data", self.handle_data)
        self.textContainer.mount(Label(f"connected to {self.app.friendName} !!!"))

    async def handle_data(self, data):
        # label = Label(str(data))
        msg = data.get("data",{"msg":"unknown datatype"}).get("msg")
        friendName = data.get("data",{"username":"unknown username"}).get("username")
        self.textContainer.mount(Label(f"{friendName} >> {msg}"))


class AddFriendScreen(Screen):
        def __init__(self):
            super().__init__()
            self.roomname = reactive("")

        def compose(self) -> ComposeResult:
            yield Grid(
                Input(placeholder="Enter Room NAme", id="friend_input"),
                Button("Submit", id="submit_button"),
                id="dialog"
            )

        async def on_input_changed(self, event: Input.Changed) -> None:
            if event.input.id == "friend_input":
                self.app.roomname = event.value

        async def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "submit_button":
                if self.app.roomname:
                    self.app.action_start_chat()

class ConnectLinkApp(App):
    CSS_PATH = "style.tcss"
    BINDINGS = [("q", "request_quit", "Quit"),
                ("a", "add_friend", "Add Friend"),
                ("t", "append_message", "Append Message Test")]

    class InputScreen(Static):
        def __init__(self):
            super().__init__()
            self.username = reactive("")

        def compose(self) -> ComposeResult:
            yield Container(
                Input(placeholder="Enter Username", id="username_input"),
                Button("Submit", id="submit_button"),
                id="center-middle"
            )

        async def on_input_changed(self, event: Input.Changed) -> None:
            if event.input.id == "username_input":
                self.app.username = event.value

        async def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "submit_button":
                if self.app.username:
                    self.app.action_add_friend()
    
    class MessageScreen(Static):
        def __init__(self, message: str):
            super().__init__()
            self.message = message

        def compose(self) -> ComposeResult:
            yield Static(self.message)
    
    def compose(self) -> ComposeResult:
        self.username = ""
        self.friendName = "hey"
        yield Header("ConnectLink TM")
        yield self.InputScreen()
        self.footer = Footer()
        yield self.footer

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())
    
    def action_add_friend(self) -> None:
        self.push_screen(AddFriendScreen())
    
    def action_start_chat(self) -> None:
        self.push_screen(ChatScreen())
    
    def show_message_screen(self, message: str) -> None:
        self.mount(self.MessageScreen(message))

    def action_append_message(self):
        self.app.show_message_screen(f"Room: {self.friendName}, Username: {self.username}")

if __name__ == "__main__":
    ConnectLinkApp().run()
