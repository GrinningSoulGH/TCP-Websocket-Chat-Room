import json, asyncio, websockets
import chat_utils.json_tools as json_tools

class SLogic:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    async def read(self):
        data = (await self.reader.read(255)).decode()
        if not self.reader.at_eof():
            return data
        else:
            return False

    async def write(self, data):
        self.writer.write(data.encode())
        await self.writer.drain()

    async def add(self, user):
        await self.write(json.dumps(json_tools.make_message(f'{user.username} is connected!!!', 'Server', 'broadcast')))

    async def leave(self, user):
        await self.write(json.dumps(json_tools.make_message(f'{user.username} disconnected.', 'Server', 'broadcast')))

    def close(self):
        self.writer.close()

class WSLogic:
    def __init__(self, websocket):
        self.websocket = websocket
    
    async def read(self):
        try:
            data = await self.websocket.recv()
        except websockets.exceptions.ConnectionClosedOK:
            return False
        else:
            return data

    async def write(self, data):
        await self.websocket.send(data)

    async def add(self, user):
        await self.write(json.dumps(json_tools.make_message(f'{user.username}+', 'Server', 'userLog')))

    async def leave(self, user):
        await self.write(json.dumps(json_tools.make_message(f'{user.username}-', 'Server', 'userLog')))

    def close(self):
        pass
